import socket, json, time, argparse

p = argparse.ArgumentParser()
p.add_argument("--name", required=True)
p.add_argument("--zone")
p.add_argument("--upstream")
p.add_argument("--port", type=int, default=5300)
a = p.parse_args()

zone = json.load(open(a.zone)) if a.zone else {}
cache = {}  # name -> (ip, expiry)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", a.port))
print(f"[{a.name}] listening on {a.port}", flush=True)

def ask_upstream(name):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1.0)
    try:
        s.sendto(json.dumps({"type": "QUERY", "name": name}).encode(), (a.upstream, a.port))
        data, _ = s.recvfrom(2048)
        return json.loads(data)
    except socket.timeout:
        return None
    finally:
        s.close()

while True:
    data, addr = sock.recvfrom(2048)
    msg = json.loads(data)
    if msg["type"] == "PING":
        reply = {"type": "PONG", "server": a.name}
    else:
        name = msg["name"].lower()
        now = time.time()
        if name in zone:
            reply = {"type": "ANSWER", "name": name, "ip": zone[name]["ip"],
                     "ttl": zone[name]["ttl"], "source": "local"}
        elif name in cache and cache[name][1] > now:
            reply = {"type": "ANSWER", "name": name, "ip": cache[name][0],
                     "ttl": int(cache[name][1] - now), "source": "cache"}
        elif a.upstream:
            up = ask_upstream(name)
            if up is None:
                reply = {"type": "SERVFAIL", "name": name}
            elif up["type"] == "ANSWER":
                cache[name] = (up["ip"], now + up["ttl"])
                reply = {"type": "ANSWER", "name": name, "ip": up["ip"],
                         "ttl": up["ttl"], "source": "upstream"}
            else:
                reply = up
        else:
            reply = {"type": "NXDOMAIN", "name": name}
        reply["server"] = a.name
    print(f"[{a.name}] {addr[0]} -> {msg} => {reply.get('type')} {reply.get('source','')}", flush=True)
    sock.sendto(json.dumps(reply).encode(), addr)
