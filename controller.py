import socket, json, time, subprocess

VIP, VMAC, PORT = "10.0.0.100", "00:00:00:00:00:64", 5300
RESOLVERS = {  # name: (ip, mac, switch port)
    "r1": ("10.0.0.11", "00:00:00:00:00:11", 1),
    "r2": ("10.0.0.12", "00:00:00:00:00:12", 2),
}
CLIENTS = {"10.0.0.21": "r1", "10.0.0.22": "r2"}  # preferred resolver (load split)
alive = {r: True for r in RESOLVERS}
misses = {r: 0 for r in RESOLVERS}

def ofctl(*args):
    subprocess.run(["ovs-ofctl", *args], check=False)

def probe(ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0.5)
    try:
        s.sendto(b'{"type":"PING"}', (ip, PORT))
        return json.loads(s.recvfrom(1024)[0])["type"] == "PONG"
    except Exception:
        return False
    finally:
        s.close()

def install_flows():
    ofctl("add-flow", "s1", "priority=0,actions=normal")
    for r, (ip, mac, port) in RESOLVERS.items():  # return path: resolver -> client
        ofctl("add-flow", "s1",
              f"priority=100,udp,nw_src={ip},tp_src={PORT},"
              f"actions=mod_nw_src:{VIP},mod_dl_src:{VMAC},normal")
    for client, pref in CLIENTS.items():
        target = pref if alive[pref] else next((r for r in RESOLVERS if alive[r]), None)
        match = f"priority=100,udp,nw_src={client},nw_dst={VIP},tp_dst={PORT}"
        if target is None:
            ofctl("add-flow", "s1", match + ",actions=drop")
            print(f"[ctrl] {client}: no resolver alive, dropping", flush=True)
            continue
        ip, mac, port = RESOLVERS[target]
        ofctl("add-flow", "s1",
              f"{match},actions=mod_dl_dst:{mac},mod_nw_dst:{ip},output:{port}")
        print(f"[ctrl] {client} -> {target}", flush=True)

install_flows()
while True:
    changed = False
    for r, (ip, _, _) in RESOLVERS.items():
        if probe(ip):
            misses[r] = 0
            if not alive[r]:
                alive[r] = True; changed = True
                print(f"[ctrl] {r} RECOVERED", flush=True)
        else:
            misses[r] += 1
            if misses[r] >= 3 and alive[r]:
                alive[r] = False; changed = True
                print(f"[ctrl] {r} FAILED", flush=True)
    if changed:
        install_flows()
    time.sleep(1)
