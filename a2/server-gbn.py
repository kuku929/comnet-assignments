import socket
import time
import struct
import threading
import queue
import random

# Configuration
SERVER_IP = "127.0.0.1"
SERVER_PORT = 12345
BUFFER_SIZE = 1024
QUEUE_SIZE = 100  #B, Max buffer size
PACKET_SERVICE_INTERVAL = 0.001  #1/C, Inverse of the link capacity, packet processing rate (FIFO)
DROP_PROBABILITY = 0.0  #PER, Probability of packet drop before entering the queue
RTT = 0.1  #Round-trip time (RTT)

# Create UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((SERVER_IP, SERVER_PORT))

# Data structures
received_packets = set()  # Track received sequence numbers
delayed_packets = queue.PriorityQueue()  # Priority queue for delay handling
processing_queue = queue.Queue(maxsize=QUEUE_SIZE)  # FIFO buffer
base = -1  # Last in-order received packet

lock = threading.Lock()

# Function to delay packets independently
def delay_packet(seq_num, client_addr, recv_time):
    expected_departure_time = recv_time + RTT 
    delayed_packets.put((expected_departure_time, seq_num, client_addr))
    print(f"Packet {seq_num} added to delay queue, expected at {expected_departure_time:.3f}")

# Function to process delayed packets and add to queue
def process_delayed_packets():
    global base
    while True:
        delay_time, seq_num, client_addr = delayed_packets.get()

        # Ensure we don't process before its due time
        sleep_time = max(0, delay_time - time.time())
        time.sleep(sleep_time)

        # Simulate random drop before entering queue
        if random.random() < DROP_PROBABILITY:
            print(f"Packet {seq_num} dropped before entering queue!")
            continue

        # Add packet to processing queue (FIFO)
        if not processing_queue.full():
            processing_queue.put((seq_num, client_addr))
            print(f"Packet {seq_num} added to queue at {time.time():.3f}")
        else:
            print(f"Packet {seq_num} dropped due to full buffer!")

# Function to process queue and acknowledge packets
def serve_packets():
    global base
    while True:
        seq_num, client_addr = processing_queue.get()
        with lock:
            if seq_num == base+1:
                received_packets.add(seq_num)

            # Update cumulative ACK base
            while base + 1 in received_packets:
                base += 1

            # Send cumulative ACK
            try:
                ack_packet = struct.pack("!I", base)
                server_socket.sendto(ack_packet, client_addr)
                print(f"Processed Packet {seq_num}, Sent Cumulative ACK {base}")
            except struct.error:
                print(f"Error: Unable to pack ACK for base {base}")

        time.sleep(PACKET_SERVICE_INTERVAL)  # Processing rate

# Start packet processing threads
threading.Thread(target=process_delayed_packets, daemon=True).start()
threading.Thread(target=serve_packets, daemon=True).start()

print(f"Server listening on {SERVER_IP}:{SERVER_PORT}")

while True:
    packet, client_addr = server_socket.recvfrom(BUFFER_SIZE)
    recv_time = time.time()
    seq_num = struct.unpack("!I", packet)[0]

    print(f"Received Packet {seq_num}, adding to delay line")

    # Delay packet independently
    threading.Thread(target=delay_packet, args=(seq_num, client_addr, recv_time), daemon=True).start()


