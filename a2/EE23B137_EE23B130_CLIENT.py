import socket
import time
import struct
import threading

# Configuration
SERVER_IP = "127.0.0.1"
SERVER_PORT = 12345
BUFFER_SIZE = 1024

CLIENT_IP = "127.0.0.1"
CLIENT_PORT = 8000

lock = threading.Lock()

# Create UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(1.0)
client_socket.bind((CLIENT_IP, CLIENT_PORT))

# Send function
def send_pckt(id):
    payload = struct.pack("!I", id)
    client_socket.sendto(payload, (SERVER_IP, SERVER_PORT))
    return id+1

# Find out the parameters
# First I will send and receive ack for 0, becaus thats the only weird case for which ack is not sent
N = 0
curr_seq = 0
latest_recv = -1

start = time.time()
curr_seq = send_pckt(curr_seq)
while True:
    try:
        packet, _ = client_socket.recvfrom(BUFFER_SIZE)
    except Exception as e:
        # The -1 ack problem 
        curr_seq=latest_recv+1
        curr_seq = send_pckt(curr_seq)
        continue
    latest_recv+=1
    break

# Now find RTT and Service time
# Send 10 packets and hope atleast 2 will return
# RTT will be the time of first ack
# Service time will be time of second ack - RTT

RTT = 0.1 # Default values
service_time = 0.1 # Default values
t1 = time.time()
for i in range(6):
    curr_seq = send_pckt(curr_seq)
    time.sleep(0.0001)

# recv first ack
try:
    packet, _ = client_socket.recvfrom(BUFFER_SIZE)
except:
    pass
t2 = time.time()

# handle this packet
ack_num = struct.unpack("!I", packet)[0]
# print(ack_num)
if(ack_num == latest_recv+1):
    latest_recv+=1
elif(ack_num < latest_recv):
    print("this should not happen.")
elif(ack_num == latest_recv):
    curr_seq=ack_num+1
elif(ack_num > latest_recv+1):
    print("this should not happen.")

# recv second ack
try:
    packet, _ = client_socket.recvfrom(BUFFER_SIZE)
except:
    pass

t3 = time.time()

# handle this packet
ack_num = struct.unpack("!I", packet)[0]
# print(ack_num)
if(ack_num == latest_recv+1):
    latest_recv+=1
elif(ack_num < latest_recv):
    print("this should not happen.")
elif(ack_num == latest_recv):
    curr_seq=ack_num+1
elif(ack_num > latest_recv+1):
    print("this should not happen.")

# handle rest of the acks
for i in range(4):
    try:
        packet, _ = client_socket.recvfrom(BUFFER_SIZE)
    except Exception as e:
        break
    ack_num = struct.unpack("!I", packet)[0]
    curr_seq = ack_num + 1
    latest_recv = ack_num
    
# Calculate parameters
RTT = t2-t1
service_time = t3-t2

# Function to send packets every service_time time
def spam():
    global curr_seq
    global latest_recv
    while latest_recv < 10000:
        with lock:
            curr_seq = send_pckt(curr_seq)
        # print("sending ", curr_seq)
        time.sleep(service_time)

p = threading.Thread(target=spam, daemon=False)
p.start()

last_recv_arr = [0.0 for _ in range(10100)] # Time of last ack received for any packet sent
def update():
    # Process rest of the packets
    global curr_seq
    global latest_recv
    global last_recv_arr
    while latest_recv < 10000:
        try:
            packet, _ = client_socket.recvfrom(BUFFER_SIZE)
        except Exception as e:
            # Buffer full 
            with lock: 
                curr_seq=latest_recv+1
        ack_num = struct.unpack("!I", packet)[0]
        # print(ack_num, curr_seq - latest_recv - 1)
        if(ack_num == latest_recv+1):
            # Ideal case: Send the next in line
            latest_recv+=1
        elif(ack_num < latest_recv):
            print("this should not happen.")
        elif(ack_num == latest_recv):
            # this happens when at least the latest_recv+1 gets dropped
            # and some other pckt > latest_recv+1 was acked
            # NOTE: We want to resend a number only the first time we receive an ack for it,
            # Unless it has actually been dropped twice
            # i.e. it has been more than an RTT since the last ack
            curr_time = time.time()
            if curr_time > last_recv_arr[ack_num+1] + RTT:
                last_recv_arr[ack_num+1] = curr_time
                with lock:
                    curr_seq=ack_num+1
        elif(ack_num > latest_recv+1):
            print("this should not happen.")
t = threading.Thread(target=update, daemon=False)
t.start()

# Wait for threads to join
p.join()
t.join()
end = time.time()
print("Time taken to send 10000 packets = ", (end - start))
print("Throughput = ", 10000/(end-start))