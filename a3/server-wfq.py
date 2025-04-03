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
        self.last_vft = {port: [0] for port in FLOW_WEIGHTS}  # Last VFT for each flow
        self.lock = threading.Lock()
        self.buffer = [] # Acts as a heap, contains: [(vft, (data, flow_num))]

    def compute_vft(self, flow, arrival_time):
        # Function to compute vft of packet that arrived
        weight = FLOW_WEIGHTS[flow]
        last_vft = self.last_vft[flow][-1]
        vft = max(arrival_time, last_vft) + 1 / (CAPACITY * weight)
        self.last_vft[flow].append(vft)
        return vft
    
    def enqueue_packet(self, packet, flow):
        # Function to add packet to queue and handle dropping
        with self.lock:
            vft = self.compute_vft(flow, self.virtual_time)
            # Insert in order of vft
            heapq.heappush(self.buffer, (vft, (packet, flow)))
            if len(self.buffer) > BUFFER_SIZE:
                # Treat the 'heap' as list
                # Find index of max vft packet
                # Drop that packet
                # Re-heapify the list
                index_max = max(range(len(self.buffer)), key=self.buffer.__getitem__)
                vft, (packet, flow) = self.buffer.pop(index_max)
                self.last_vft[flow].pop(-1)
                heapq.heapify(self.buffer)
            
    def serve_packets(self):
        # Function to serve packets
        while True:
            self.lock.acquire()
            if self.buffer:
                # Pop from top of heap
                vft, (packet, flow) = heapq.heappop(self.buffer)
                self.lock.release()
                time.sleep(1/CAPACITY)
                # print(self.buffer)
                self.virtual_time = vft
                client_addr = ("127.0.0.1", flow)
                self.sock.sendto(packet, client_addr)
            else:
                self.lock.release()
            

    def start(self):
        # Server enqueued packets on another thread
        threading.Thread(target=self.serve_packets, daemon=True).start()
        while True:
            data, addr = self.sock.recvfrom(PACKET_SIZE)
            flow_port = addr[1]  # Extract client port number from address tuple
            if flow_port in FLOW_WEIGHTS:
                self.enqueue_packet(data, flow_port)

if __name__ == "__main__":
    server = WFQServer()
    server.start()