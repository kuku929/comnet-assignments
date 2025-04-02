import socket
import time
import threading
from collections import deque
import sys

# Client parameters
SERVER_IP = "127.0.0.1"
SERVER_PORT = 4000
CLIENT_PORT = 5001  # Change this for different clients
PACKET_SIZE = 1024  # Size of each packet
SEND_INTERVAL = 0.1  # Interval between sending packets (in seconds)

class Client:
    def __init__(self, client_port, speed):
        self.send_interval = 1/speed
        self.client_port = client_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", self.client_port))
        self.total_packets_sent = 0
        self.total_packets_received = 0
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.received_timestamps = deque()  # To track timestamps of received packets

    def send_packets(self):
        while True:
            packet_data = f"Packet {self.total_packets_sent + 1}".encode()
            self.sock.sendto(packet_data, (SERVER_IP, SERVER_PORT))
            with self.lock:
                self.total_packets_sent += 1
            # print(f"Sent: {packet_data.decode()}")
            time.sleep(self.send_interval)

    def receive_packets(self):
        while True:
            data, _ = self.sock.recvfrom(PACKET_SIZE)
            with self.lock:
                self.total_packets_received += 1
                self.received_timestamps.append(time.time())  # Record the timestamp of the received packet
            # print(f"Received: {data.decode()}")

    def compute_throughput(self):
        while True:
            time.sleep(5)  # Compute throughput every 5 seconds
            current_time = time.time()
            elapsed_time = current_time - self.start_time

            with self.lock:
                # Long-term throughput: Total packets received divided by total elapsed time
                long_term_throughput = self.total_packets_received / elapsed_time

                # Short-term throughput: Packets received in the last 5 seconds divided by 5 seconds
                # Remove timestamps older than 5 seconds
                while self.received_timestamps and self.received_timestamps[0] < current_time - 5:
                    self.received_timestamps.popleft()
                short_term_throughput = len(self.received_timestamps) / 5

                print(f"Client Port: {self.client_port} ")
                print(f"Long-term throughput: {long_term_throughput:.2f} packets/sec")
                print(f"Short-term throughput: {short_term_throughput:.2f} packets/sec")
                print(f"Total packets sent: {self.total_packets_sent}, Total packets received: {self.total_packets_received}\n")

    def start(self):
        # Start threads for sending, receiving, and computing throughput
        threading.Thread(target=self.send_packets, daemon=True).start()
        threading.Thread(target=self.receive_packets, daemon=True).start()
        threading.Thread(target=self.compute_throughput, daemon=True).start()

        # Keep the main thread alive
        while True:
            time.sleep(1)

if __name__ == "__main__":
    client_port = int(sys.argv[1])
    speed = int(sys.argv[2])
    client = Client(client_port, speed)
    client.start()


