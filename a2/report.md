# Reliable data transfer and Congestion Control 

## Strategy
Owing to the working of the server we figured out a way to find the RTT and processing delay by sending a few packets first. Since the processing delay and RTT was fixed we could simply send packets at a fixed rate once we figured out these constants. 
Here's the explanation:
![img](/home/krutarth/comnet_assgn2/rtt.png)

In practice though we sent a set of packets to account for the drop due to chance.


| S. No. | Capacity(PPS) | RTT | PER(%) | Buffer Size(packets) | Throughput(Pps) |
|----------|----------|----------|----------|----------|----------|
| 1   |  1000  | 100   |  0  | 100   | 646.0189396128969  |
| 2   |  1000  | 100   | 0  | 10  |645.612909536777  |
| 3  |  10 | 1  |   0   |   1   |  1.05
| 4 | 10    |   1 | 10  |   10  | 8.00
