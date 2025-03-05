import asyncio
import websockets
import struct
from collections import defaultdict
from PySide6.QtWidgets import QApplication, QWidget, QBoxLayout, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QTextEdit, QListWidget, QLabel
from PySide6.QtCore import Signal, QObject, Slot, QTimer
from PySide6 import QtAsyncio

class Backend(QObject):
    update_user_list = Signal()
    update_chat_window = Signal()
    connection_status = Signal(bool)

    def __init__(self):
        super().__init__()
        self.websocket = None
        self.client_id = None
        self.user_list = []
        self.chat_logs = defaultdict(list)

    async def connect_to_serverrr(self, uri, client_id):
        try:
            self.websocket = await websockets.connect(uri)
            self.client_id = client_id
            associate_packet = struct.pack('!BBB', 0, 0, client_id)
            await self.websocket.send(associate_packet)
            response = await self.websocket.recv()
            if response[0] == 0 and response[1] == 1:
                self.connection_status.emit(True)
                asyncio.create_task(self.get_responses())
            else:
                self.connection_status.emit(False)
        except Exception as e:
            print(f"Connection error: {e}")
            self.connection_status.emit(False)

    async def send_message(self, receiver_id, message):
        payload = message.encode('ascii')
        payload_length = len(payload)
        if payload_length > 255:
            return False
        push_packet = struct.pack('!BBBBB', 2, 1, int(self.client_id), int(receiver_id), payload_length) + payload
        await self.websocket.send(push_packet)
        response = await self.websocket.recv()
        self.chat_logs[int(self.client_id)].append(f"[{self.client_id}]: {payload}")
        return response[0] == 1 and response[1] == 2

    async def get_responses(self):
        while True:
            try:
                get_packet = struct.pack('!BBB', 1, 0, self.client_id)
                await self.websocket.send(get_packet)
                response = await self.websocket.recv()
                if response[0] == 2 and response[1] == 0:
                    sender_id = struct.unpack("B", response[3:4])[0]
                    payload = response[5:].decode('ascii')
                    self.chat_logs[int(sender_id)].append(f"[{sender_id}]: {payload}")
                    if int(sender_id) not in self.user_list:
                        self.user_list.append(str(sender_id))
                elif response[0] == 1 and response[1] == 1:  # CONTROL, BUFFEREMPTY
                    await asyncio.sleep(1)
                self.update_user_list.emit()
                self.update_chat_window.emit() 
            except websockets.exceptions.ConnectionClosedError:
                break
        

class UserList(QWidget):
    select_chat = Signal(str)

    def __init__(self, parent=None, backend=None):
        super().__init__(parent)
        self.backend = backend
        self.buttons = []
        self.layout = QBoxLayout(QBoxLayout.TopToBottom, self)
        self.layout.insertStretch( -1, 1 )
        self.rec_id_input = QLineEdit(self)
        self.add_button = QPushButton("Add user", self)
        self.layout.addWidget(self.rec_id_input)
        self.layout.addWidget(self.add_button)
        self.add_button.clicked.connect(self.add_user)

    @Slot()
    def add_user(self):
        user = self.rec_id_input.text()
        if user:  # Check if the input is not empty
            new_user = True
            for button in self.buttons:
                if user == button.text():
                    new_user = False
                    break
            if new_user:
                push_button = QPushButton(user, self)
                self.buttons.append(push_button)
                self.layout.insertWidget(len(self.buttons) - 1, push_button)
                push_button.clicked.connect(self.user_selected)
            self.rec_id_input.clear()  # Clear the input field after adding

    @Slot()
    def update(self):
        for user in self.backend.user_list:
            new_user = True
            for button in self.buttons:
                if user == button.text():
                    new_user = False
                    break
            if new_user:
                push_button = QPushButton(str(user), self)
                self.buttons.append(push_button)
                self.layout.insertWidget(len(self.buttons) - 1, push_button)
                push_button.clicked.connect(self.user_selected)

    @Slot()
    def user_selected(self):
        username = self.sender().text()
        self.select_chat.emit(username)

class ChatWindow(QWidget):
    def __init__(self, parent=None, backend=None):
        super().__init__(parent)
        self.backend = backend
        self.layout = QBoxLayout(QBoxLayout.BottomToTop, self)
        self.layout.insertStretch(-1,1)
        self.messages = []
        self.current_user = "0"
        pass

    @Slot()
    def change_current_user(self, username):
        self.current_user = username

    @Slot()
    def update(self):
        for message in self.messages:
            self.layout.removeWidget(message)
            message.deleteLater()
            self.messages.clear()
        for i in range(len(self.backend.chat_logs[int(self.current_user)])):
            label = QLabel(self.backend.chat_logs[int(self.current_user)][i], self)
            self.layout.addWidget(label)
            self.messages.append(label)



class Chat(QWidget):
    def __init__(self, parent=None, backend=None):
        super().__init__(parent)
        self.chat_window = ChatWindow(self, backend)
        self.type_window = QLineEdit(self, backend)
        self.backend = backend

        self.layout = QBoxLayout(QBoxLayout.TopToBottom, self)
        self.layout.addWidget(self.chat_window)
        self.layout.addWidget(self.type_window)
        self.layout.insertStretch(0,1)

        self.type_window.editingFinished.connect(self.handle_message)
        pass

    @Slot()
    def handle_message(self):
        payload = self.type_window.text()
        username = self.chat_window.current_user
        asyncio.create_task(self.backend.send_message(username, payload))
        self.type_window.clear()


class MainWindow(QWidget):
    connect_to_server_signal = Signal(str, str)
    def __init__(self, backend=None):
        super().__init__()
        self.backend = backend
        self.backend.connection_status.connect(self.on_connection_status)
        self.user_list = UserList(self, self.backend)
        self.chat_hist = Chat(self, self.backend)
        self.layout = QBoxLayout(QBoxLayout.LeftToRight, self)
        self.layout.addWidget(self.user_list, stretch=1)
        self.layout.addWidget(self.chat_hist, stretch=3)

        # backend has replied, update message
        self.backend.update_chat_window.connect(self.chat_hist.chat_window.update)
        # new users recieved, update list
        self.backend.update_user_list.connect(self.user_list.update)
        # when user is done editing, call backed
        self.user_list.select_chat.connect(self.chat_hist.chat_window.change_current_user)

        self.client_id_input = QLineEdit(self)
        self.connect_button = QPushButton("Connect", self)
        self.layout.addWidget(self.client_id_input)
        self.layout.addWidget(self.connect_button)
        self.connect_button.clicked.connect(self.request_connect_to_server)

    @Slot()
    def request_connect_to_server(self):
        client_id = int(self.client_id_input.text())
        asyncio.create_task(self.backend.connect_to_serverrr("ws://localhost:12345", client_id))

    @Slot(bool)
    def on_connection_status(self, status):
        if status:
            self.connect_button.setEnabled(False)
            self.client_id_input.setEnabled(False)
        else:
            self.connect_button.setEnabled(True)
            self.client_id_input.setEnabled(True)

def main():
    app = QApplication([])
    client = Backend()
    window = MainWindow(client)
    window.show()

    loop = asyncio.get_event_loop()
    
    def qt_event_loop():
        app.processEvents()
        loop.call_later(0.01, qt_event_loop)
    
    loop.call_soon(qt_event_loop)
    loop.run_forever()

if __name__ == "__main__":
    QtAsyncio.run(main())
