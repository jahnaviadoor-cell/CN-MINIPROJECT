import socket, json, sys, time

VIP, PORT = "10.0.0.100", 5300
name = sys.argv[1]
for attempt in range(1, 4):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1.0)
    t0 = time.time()
    try:
        s.sendto(json.dumps({"type": "QUERY", "name": name}).encode(), (VIP, PORT))
        data, _ = s.recvfrom(2048)
        r = json.loads(data)
        print(f"{r}  ({(time.time()-t0)*1000:.1f} ms, attempt {attempt})")
        break
    except socket.timeout:
        print(f"attempt {attempt}: timeout, retrying...")
else:
    print("resolution failed after 3 attempts")
