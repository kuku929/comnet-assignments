import subprocess
import sys
import time

# Client configuration
CLIENT_SCRIPT = "client-wfq4a.py"
PORTS = [(5001, 10), (5002, 20), (5003, 40)]

def run_clients():
    processes = []
    for port in PORTS:
        cmd = [
            sys.executable,
            CLIENT_SCRIPT,
            str(port[0]),
            str(port[1])
        ]
        processes.append(subprocess.Popen(cmd))
    
    print(f"Started {len(PORTS)} clients on ports: {PORTS}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTerminating clients...")
        for p in processes:
            p.terminate()

if __name__ == "__main__":
    run_clients()
