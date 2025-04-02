import socket
import threading
import time
import heapq

# Server parameters
SERVER_IP = "127.0.0.1"
SERVER_PORT = 4000
CAPACITY = 10  # packets per second
PACKET_SIZE = 1024
BUFFER_SIZE = 1000 # Max queue size
FLOW_WEIGHTS = {5001: 8, 5002: 1, 5003: 1}  # weights for each flow
SIZE_CNT = [0,0,0]

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
    def find_flow_ind(self,flow):
        flow_ind = 0
        for key in FLOW_WEIGHTS.keys():
            if key == flow:
                break
            else:
                flow_ind+=1
        return flow_ind
    
    def enqueue_packet(self, packet, flow):
        with self.lock:
            flow_ind = self.find_flow_ind(flow)
            vft = self.compute_vft(flow, self.virtual_time)
            if SIZE_CNT[flow_ind] < BUFFER_SIZE:
                # Drop the packet with the highest VFT
                # since we are removing the last element
                # the tree does not change so you don't
                # need to heapify.
                heapq.heappush(self.buffer, (vft, (packet, flow)))
                SIZE_CNT[flow_ind]+=1
                print(f"received on {flow_ind} at {self.virtual_time}, vft = {vft}", flush=True)
                # heapify is O(n), we don't want that
                # heapq.heapify(self.buffer)
            

    def serve_packets(self):
        while True:
            self.lock.acquire()
            if self.buffer:
                vft, (packet, flow) = heapq.heappop(self.buffer)
                self.lock.release()
                time.sleep(1/CAPACITY)
                flow_ind = self.find_flow_ind(flow)
                SIZE_CNT[flow_ind]-=1
                # print(self.buffer)
                self.virtual_time = vft
                client_addr = ("127.0.0.1", flow)
                self.sock.sendto(packet, client_addr)
                print(flow_ind, " ", vft)
            else:
                self.lock.release()
            

    def start(self):
        # didn't daemon make it like very slow??
        # Yeah but it isn't happening here
        # If I make it false program doesn't terminate properly
        threading.Thread(target=self.serve_packets, daemon=True).start()
        while True:
            data, addr = self.sock.recvfrom(PACKET_SIZE)
            flow_port = addr[1]  # Extract client port number from address tuple
            if flow_port in FLOW_WEIGHTS:
                self.enqueue_packet(data, flow_port)

if __name__ == "__main__":
    server = WFQServer()
    server.start()