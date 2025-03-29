import socket
import threading
import time
import heapq

# Server parameters
SERVER_IP = "127.0.0.1"
SERVER_PORT = 4000
CAPACITY = 10  # packets per second
PACKET_SIZE = 1024
BUFFER_SIZE = 10 # Max queue size
FLOW_WEIGHTS = {5001: 1, 5002: 1, 5003: 1}  # weights for each flow

class WFQServer:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((SERVER_IP, SERVER_PORT))
        self.virtual_time = 0  # System virtual time
        self.last_vft = {port: 0 for port in FLOW_WEIGHTS}  # Last VFT for each flow
        self.lock = threading.Lock()
        self.buffer = [] # [(vft, (data, flow_num))]

    def compute_vft(self, flow, arrival_time):
        weight = FLOW_WEIGHTS[flow]
        last_vft = self.last_vft[flow]
        vft = max(arrival_time, last_vft) + 1 / (CAPACITY * weight)
        self.last_vft[flow] = vft
        return vft

    def enqueue_packet(self, packet, flow, arrival_time):
        vft = self.compute_vft(flow, arrival_time)
        with self.lock:
            heapq.heappush(self.buffer, (vft, (packet, flow)))
            if len(self.buffer) >= BUFFER_SIZE:
                # Drop the packet with the highest VFT
                # since we are removing the last element
                # the tree does not change so you don't
                # need to heapify.
                self.buffer.pop()
                # heapify is O(n), we don't want that
                # heapq.heapify(self.buffer)

    def serve_packets(self):
        while True:
            time.sleep(1 / CAPACITY)  # Serve packets at the given capacity
            with self.lock:
                if self.buffer:
                    vft, (packet, flow) = self.buffer.pop(0)
                    self.virtual_time = vft
                    client_addr = ("127.0.0.1", flow)
                    self.sock.sendto(packet, client_addr)

    def start(self):
        # didn't daemon make it like very slow??
        # Yeah but it isn't happening here
        # If I make it false program doesn't terminate properly
        threading.Thread(target=self.serve_packets, daemon=True).start()
        while True:
            data, addr = self.sock.recvfrom(PACKET_SIZE)
            flow_port = addr[1]  # Extract client port number from address tuple
            arrival_time = self.virtual_time
            if flow_port in FLOW_WEIGHTS:
                self.enqueue_packet(data, flow_port, arrival_time)

if __name__ == "__main__":
    server = WFQServer()
    server.start()