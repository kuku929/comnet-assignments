import socket
import time
import struct
import threading

DEBUG = 1
TOTAL_PACKETS = 10000
# Configuration
SERVER_IP = "127.0.0.1"
SERVER_PORT = 12345
BUFFER_SIZE = 1024

CLIENT_IP = "127.0.0.1"
CLIENT_PORT = 8000

lock = threading.Lock()

# Create UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# hope processing + RTT will not be greater than this 
client_socket.settimeout(10.0)
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

if DEBUG:  print("sending 0...")
sent_zero = time.time()
start = time.time()
curr_seq = send_pckt(curr_seq)
RTT = 0.1 # Default values
service_time = 0.1 # Default values
while True:
    try:
        packet, _ = client_socket.recvfrom(BUFFER_SIZE)
        got_zero = time.time()
        RTT = got_zero - sent_zero
    except Exception as e:
        # The -1 ack problem 
        sent_zero = time.time()
        curr_seq=latest_recv+1
        curr_seq = send_pckt(curr_seq)
        continue
    latest_recv+=1
    break

# Now find RTT and Service time
# Send 10 packets and hope atleast 2 will return
# RTT will be the time of first ack
# Service time will be time of second ack - RTT

t1 = time.time()
for i in range(6):
    if DEBUG: print("sending " ,curr_seq)
    curr_seq = send_pckt(curr_seq)

# recv first ack
try:
    packet, _ = client_socket.recvfrom(BUFFER_SIZE)
except Exception as _:
    if DEBUG: print("packet 1 not received!")
    pass
t2 = time.time()
first_delay = t2 - got_zero
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

if first_delay > RTT*1.01:
    service_time = first_delay
    
else:
    # recv second ack
    try:
        packet, _ = client_socket.recvfrom(BUFFER_SIZE)
    except Exception as _:
        if DEBUG: print("packet 2 not received!")
        pass
    t3 = time.time()
    service_time = t3 - t2
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
        if DEBUG: print("packet not recieved!")
        break
    ack_num = struct.unpack("!I", packet)[0]
    print(f"ack for packet {ack_num} received!")
    curr_seq = ack_num + 1
    latest_recv = ack_num
    

print(f"Calculated RTT: {RTT}, service_time: {service_time}")

# updating timeout value to a better estimate
client_socket.settimeout((RTT+service_time)*1.1)
# Function to send packets every service_time time
def spam():
    global curr_seq
    global latest_recv
    while latest_recv < TOTAL_PACKETS:
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
    while latest_recv < TOTAL_PACKETS:
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
print(f"Time taken to send {TOTAL_PACKETS} packets = ", (end - start))
print("Throughput = ", TOTAL_PACKETS/(end-start))
