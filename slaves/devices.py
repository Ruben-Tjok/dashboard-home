import json
import time
import redis
from config import dashconfig
from dashboard import DashboardSlave

r = redis.Redis()
slave = DashboardSlave("devices")

while True:
    print("[+] local (dhcp) devices checker: updating")

    devices = {}

    dhclients = r.keys('dhcp-*')
    for client in dhclients:
        payload = r.get(client).decode('utf-8')
        keyname = client.decode('utf-8')[5:]

        devices[keyname] = json.loads(payload)

    clients = r.keys('traffic-*')
    for client in clients:
        payload = r.get(client).decode('utf-8')
        live = json.loads(payload)

        # ignore inactive client
        if live['active'] < time.time() - (4 * 3600):
            continue

        dhcpfound = False

        for device in devices:
            if devices[device]['ip-address'] == live['addr']:
                devices[device]['rx'] = live['rx']
                devices[device]['tx'] = live['tx']
                devices[device]['timestamp'] = live['active']
                dhcpfound = True
                break

        if not dhcpfound:
            devices[live['addr']] = {
                "timestamp": live['active'],
                "mac-address": live['macaddr'],
                "hostname": live['host'],
                "ip-address": live['addr'],
                "rx": live['rx'],
                "tx": live['tx'],
            }

    print("[+] local devices checker: %d devices found" % len(devices))
    slave.set(devices)
    slave.publish()
    slave.sleep(1)

