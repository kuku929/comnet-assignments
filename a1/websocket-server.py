import asyncio
import websockets
from collections import defaultdict
import struct

# Store client sessions and message buffers
sessions = {}  # {client_id: websocket}
buffers = defaultdict(list)  # {client_id: [messages]}

# Packet structure:
# MANAGEMENT packet: 3 bytes (type: 1 byte, message: 1 byte, id: client_id)
# CONTROL packet: 3 bytes (type: 1 byte, message: 1 byte, id: client_id)
# DATA packet: 5 bytes (type: 1 byte, message: 1 byte, id: 1 byte, id2: 1 byte, length: 1 byte) + variable-length payload


async def handle_connection(websocket):
    print("New client connected")
    client_id = None
    try:
        async for message in websocket:
            # Parse the packet type and message
            packet_type = message[0]  # First byte is the packet type
            packet_message = message[1]  # Second byte is the message type

            if packet_type == 0:  # MANAGEMENT packet
                if packet_message == 0:  # ASSOCIATE
                    print("Received raw message:", message)
                    client_id = message[2]  # Extract id (1 byte)
                    if client_id in sessions:
                        response = struct.pack('!BBB', 0, 3, client_id)  # UNKNOWNERROR
                        print("Raw response:", response)
                        await websocket.send(response)
                        #await websocket.close()  # Forcefully close the new connection
                    else:
                        sessions[client_id] = websocket
                        response = struct.pack('!BBB', 0, 1, client_id)  # ASSOCIATIONSUCCESS
                        print("Raw response:", response)
                        await websocket.send(response)
                else:
                    print("Received raw message:", message)
                    client_id = message[2]  # Extract id (1 byte)
                    response = struct.pack('!BBB', 0,3,client_id) # UNKNOWNERROR
                    print("Raw response:", response)
                    await websocket.send(response)
                    
            elif packet_type == 1:  # CONTROL packet
                if packet_message == 0:  # GET
                    print("Received raw message:", message)
                    client_id = message[2]  # Extract id (1 byte)
                    if client_id not in sessions:
                        response = struct.pack('!BBB', 0, 2, client_id)  # ASSOCIATIONFAILED
                        print("Raw response:", response)
                    elif not buffers[client_id]:
                        response = struct.pack('!BBB', 1, 1, client_id)  # BUFFEREMPTY
                        print("Raw response:", response)
                    else:
                        message_payload = buffers[client_id].pop(0)
                        sender_id = message_payload[0]
                        message_payload = message_payload[3:]
                        response = struct.pack('!BBBBB', 2, 0, client_id, sender_id, len(message_payload)) + message_payload  # GETRESPONSE
                        print("Raw response:", response)
                    await websocket.send(response)
                else:
                    print("Received raw message:", message)
                    client_id = message[2]  # Extract id (1 byte)
                    response = struct.pack('!BBB', 0,3,client_id) # UNKNOWNERROR
                    print("Raw response:", response)
                    await websocket.send(response)

            elif packet_type == 2:  # DATA packet
                if packet_message == 1:  # PUSH
                    client_id = message[2]  # Extract id (1 byte)
                    print("Received raw message:", message)
                    if client_id not in sessions:
                        response = struct.pack('!BBB', 0, 2, client_id)  # ASSOCIATIONFAILED
                    else:
                        receiver_id = message[3]  # Extract receiver_id (1 bytes)
                        length = message[4] 
                        payload = message[5:]  # Extract payload (variable length)
                        if length < 255:
                            if length == len(payload):
                                if len(buffers[receiver_id]) < 100:  # Buffer size limit
                                    buffers[receiver_id].append(message[2:])
                                    response = struct.pack('!BBB', 1, 2, client_id)  # POSITIVEACK
                                else:
                                    response = struct.pack('!BBB', 1, 3, client_id)  # BUFFERFULL
                            else:
                                response = struct.pack('!BBB', 0,3,client_id) # UNKNOWNERROR
                        else:
                            response = struct.pack('!BBB', 0,3,client_id) # UNKNOWNERROR
                        print("Raw response:", response)
                        await websocket.send(response)
                else:
                    print("Received raw message:", message)
                    client_id = message[2]  # Extract id (1 byte)
                    response = struct.pack('!BBB', 0,3,client_id) # UNKNOWNERROR
                    print("Raw response:", response)
                    await websocket.send(response)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if client_id in sessions:
            del sessions[client_id]
        print("Client disconnected")

async def start_server():
    async with websockets.serve(handle_connection, '', 12345):
        print("WebSocket server started on ws://localhost:12345")
        await asyncio.Future()  # Run forever

# Run the server
asyncio.run(start_server())

