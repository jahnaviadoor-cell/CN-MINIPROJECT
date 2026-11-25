# CN-MINIPROJECT

Distributed DNS-like Name Resolution System

Problem statement:Implement a simplified DNS-like name-resolution service using UDP sockets. SDN should dynamically manage the forwarding of resolution requests.

Project expectations:
• Implement UDP name-resolution queries
• Maintain name-to-IP mappings
• Support multiple resolution servers
• Implement caching
• Handle timeouts
• Detect server failures
• Redirect requests when required
• Measure lookup latency

Solution. Clients send UDP queries to one virtual IP, 10.0.0.100 port 5300. No real host has that address. The OpenFlow switch rewrites the destination to a real resolver (r1 or r2) and rewrites the source back to the VIP on the reply, so the client never learns which resolver answered. An SDN controller decides which resolver each client is mapped to, watches resolver health, and rewrites the switch rules when a resolver fails or recovers

How a query flows
<img width="539" height="157" alt="image" src="https://github.com/user-attachments/assets/d9981b05-a436-43d1-9b43-c254e4c48042" />
DNS: translates a name such as www.example.com into an IP address. A resolver answers queries
NXDOMAIN means the name does not exist.
• TTL and caching: each answer carries a time-to-live. Within the TTL the resolver reuses the stored answer instead of looking it up again, which cuts latency and load on the upstream server. 
• SDN: the control plane (decisions) is separated from the data plane (forwarding). The switch only matches packets and applies rules. The controller is the brain. 
• OpenFlow: the protocol the controller uses to install rules on the switch. A rule has a match, actions (rewrite the destination IP, send out a port), a priority and optional timeouts.
• Virtual IP (VIP): a fake address clients use. The switch rewrites destination to the chosen resolver on the way in and source back to the VIP on the way out. It is the same idea as NAT in a load balancer.
• UDP vs TCP: UDP is connectionless and message-based. Each sendto is one datagram and recvfrom returns exactly one datagram, so there is no framing problem as there is in TCP. There is no handshake, no retransmission and no ordering. 
• Timeout and retry: without a timeout, recvfrom would block forever if the resolver died. The timeout turns silence into a detectable failure.
• Why retries help here: by the second attempt the controller may already have remapped the client to a healthy resolver, so the retry succeeds. 
• Concurrency: a resolver that handles one query at a time would block others, so use a thread per query or a fast single loop .
• Table-miss and PacketIn: a packet that matches no specific rule goes to the controller. This happens for the first packet of a client's flow, after that the switch handles packets alone and the controller is not in the data path. 
• Why rewrite the source on the reverse path: the client sent to 10.0.0.100. If the reply arrived from 10.0.0.12 it would not match what the client expects and its socket would not accept it. The rewrite keeps the VIP illusion. 
• Static ARP for the VIP: nobody answers an ARP request for 10.0.0.100, so the clients are given a fixed fake MAC for it [VERIFY in topo.py]. 
• OpenFlow version: mod_nw_dst is OpenFlow 1.0 style output.

demo script:
<img width="541" height="254" alt="image" src="https://github.com/user-attachments/assets/03cf9b19-46d2-47ff-98e9-1f4b098cf4a9" />

Before running this make sure you have client.py , controller.py , resolver.py , topo.py ready along with zones.json

Deliverables 1 and 2 regarding the MINI Project in the main file
