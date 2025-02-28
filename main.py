# This Python file uses the following encoding: utf-8
import sys
from PySide6 import QtCore, QtWidgets, QtGui


class Backend(QtCore.QObject):
    update_user_list = QtCore.Signal(list)
    update_chat_window = QtCore.Signal(str,list)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    @QtCore.Slot()
    def update(self):
        # bussiness logic
        user_list_dbg = ["1", "2", "3"]


        # ask user list to update people
        self.update_user_list.emit(user_list_dbg)
        pass

    @QtCore.Slot()
    def send_message(self, username, message):
        # login for PUSH
        # check if a user is selected
        print(username + message)
        pass

    @QtCore.Slot()
    def serve(self, username):
        # send a list of messages
        # with username in order
        hist_dbg = [f"[{username}]: hello", "[Me]: ayo"]

        self.update_chat_window.emit(username, hist_dbg)
        pass

class UserList(QtWidgets.QWidget):
    request_backend_for_chat = QtCore.Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = []
        self.layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.BottomToTop, self)
        # -1 is the last guy, make him huge
        # so that everything else gets squished
        self.layout.insertStretch( -1, 1 );
        # dbg
        # self.update_list(["hele", "dummy"])
        # self.update_list(["hele", "dummy", "baka"])


    @QtCore.Slot()
    def update(self,usernames):
        for user in usernames:
            new_user = 1
            for button in self.buttons:
                if user == button.text():
                    new_user = 0
                    break
            if new_user:
                push_button = QtWidgets.QPushButton(user, self)
                self.buttons.append(push_button)
                self.layout.addWidget(push_button)
                push_button.clicked.connect(self.user_selected)

    @QtCore.Slot()
    def user_selected(self):
        username = self.sender().text()
        self.request_backend_for_chat.emit(username)

class ChatWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.BottomToTop, self)
        self.layout.insertStretch(-1,1)
        self.messages = []
        self.current_user = str()
        pass

    @QtCore.Slot()
    def update(self, username, chat_history):
        # backend has replied
        # show the messages
        self.current_user = username
        curr_chat = 0
        # reuse the existing labels
        for message in self.messages:
            message.setText(chat_history[curr_chat])
            curr_chat+=1
            if(curr_chat == len(chat_history)):
                break

        # if not enough, add more
        for i in range(curr_chat, len(chat_history)):
            label = QtWidgets.QLabel(chat_history[i], self)
            self.layout.addWidget(label)
            self.messages.append(label)



class Chat(QtWidgets.QWidget):
    request_backend_to_send = QtCore.Signal(str, str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chat_window = ChatWindow(self)
        self.type_window = QtWidgets.QLineEdit(self)

        self.layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom, self)
        self.layout.addWidget(self.chat_window)
        self.layout.addWidget(self.type_window)
        self.layout.insertStretch(0,1)

        self.type_window.editingFinished.connect(self.handle_message)
        pass

    @QtCore.Slot()
    def handle_message(self):
        payload = self.type_window.text()
        username = self.chat_window.current_user

        self.request_backend_to_send.emit(username, payload)


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.user_list = UserList(self)
        self.chat_hist = Chat(self)
        self.backend = Backend(self)
        self.layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight, self)
        self.layout.addWidget(self.user_list, stretch=1)
        self.layout.addWidget(self.chat_hist, stretch=3)

        # ask backend for history
        self.user_list.request_backend_for_chat.connect(self.backend.serve)
        # backend has replied, update message
        self.backend.update_chat_window.connect(self.chat_hist.chat_window.update)
        # new users recieved, update list
        self.backend.update_user_list.connect(self.user_list.update)
        # when user is done editing, call backed
        self.chat_hist.request_backend_to_send.connect(self.backend.send_message)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    # ...
    sys.exit(app.exec())
