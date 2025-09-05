# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 20:46:18 2024

@author: RTB
"""

import socket
from threading import Timer
from concurrent.futures.thread import ThreadPoolExecutor

from gtbase.gtdatapacket import GTDataPacket

#TODO:
# - use ipaddress library for target_ip
# - replace 1024 in recvfrom with correct packet size, if there are multiple
#   packets in queue, this may mess things up. So far so good.

#Class to manage the incoming/outgoing packet stream from/to the PS5
#loop_func is called for each consecutive received packet
#Default socket timeout is 1 seconds, this seems to delay exiting any program
#Sends a heartbeat every 10 seconds

#Implemented UDP broadcast instead of asking the user for the PS IP-address
#There appear to be two choices on Windows:
    #1. subnet broadcast with the socket bound to ''
    #2. global broadcast with the socket bound to the local IP address
#The problem is that both options require information on either the local
#IP-address or the subnet it is on. This is platform dependent on how easy it
#is to derive. On Linux, binding to '' and broadcasting to the global broadcast
#address (255.255.255.255) supposedly does work.

class GTUDPLoop():
    RECV_PORT = 33740
    HEARTBEAT_PORT = 33739
    HEARTBEAT_TIMER = 10 # in seconds
    HEARTBEAT_TIMER_FAST = 1 # in seconds
    HEARTBEAT_CONTENT = 'A' #default if config does not contain it
    BROADCAST_ADDRESS = '255.255.255.255'

    def __init__(self, config, loop_func=None):
        self.threadPool = ThreadPoolExecutor(max_workers=8,
                                             thread_name_prefix="exec")
        self.isRunning = False
        self.socket = None
        self.t = None

        # JSON does not support bytearray, so we need to convert it
        # Should be a single character: A, B, C and ~ currently known
        config_heartbeat_content = getattr(config, 'heartbeat_content',
                                         self.HEARTBEAT_CONTENT)
        self.heartbeat_content = config_heartbeat_content.encode()
        self.timer = self.HEARTBEAT_TIMER

        self.forward = None
        if config.forward_ipaddress != '':
            self.forward = (config.forward_ipaddress, config.forward_port)
            print(f"Forwarding to {self.forward}")

        self.target_ip = config.target_ip
        self.loop_func = loop_func

    def init_socket(self):
        local_ip = self.derive_local_address()
        local_ip_string = local_ip if local_ip else "UNKNOWN, using: ''"
        print(f'Derived local IP: {local_ip_string}')

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1)
        sock.bind((local_ip, self.RECV_PORT))
        return sock

    #Crude implementation of finding a local valid IP address
    #where it's simpler to assume it's in the most common range:
    #192.168.0.0/16 with a subnet of /24
    @classmethod
    def derive_local_address(cls, match_ip='192.168'):
        #Method 1:
        ip = socket.gethostbyname(socket.gethostname())
        if ip[:len(match_ip)] == match_ip:
            return ip

        #Method 2:
        ips = [i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None)]
        for ip in ips:
            if ip[:len(match_ip)] == match_ip:
                return ip

        #No match
        return ''

    def loop_get_ps_ip(self):
        print("Entering loop to derive PS IP-address")
        while self.isRunning:
            try:
                _, address = self.socket.recvfrom(1024)
                self.set_target_ip(address[0])
                return
            except BaseException as e:
                print(f"Waiting for PS response: {e}")

    #Toggles the packet loop with a logical 'xor' on boolean toggle
    #If toggle is false: loop will be stopped if it is running
    #if toggle is true: loop will be started if it is not running
    def toggle(self, toggle=None):
        if toggle and not self.isRunning:
            def starting():
                print("Starting loop")
                self.isRunning = True

                #Do global broadcast with fast timer
                if (broadcast_method :=
                        (self.target_ip in ['', self.BROADCAST_ADDRESS])):
                    print("No PS IP given: Using broadcast method")
                    self.set_target_ip(self.BROADCAST_ADDRESS)
                    self.timer = self.HEARTBEAT_TIMER_FAST

                with self.init_socket() as self.socket:
                    self.maintain_heartbeat()

                    #loop until we receive a packet on RECV_PORT
                    #then reset timer back to default
                    if broadcast_method:
                        self.loop_get_ps_ip()  #loops here
                        print(f"Derived PS IP: {self.target_ip}")
                        self.timer = self.HEARTBEAT_TIMER

                    self.gtdp_loop(self.loop_func)
            self.threadPool.submit(starting)
        else:
            def stopping():
                print("Stopping loop")
                self.isRunning = False
                if self.t is not None:
                    self.t.cancel() #abort running timer
                else:
                    print("Heartbeat timer was not running on stopping")
            self.threadPool.submit(stopping)

    def gtdp_loop(self, loop_func=None):
        try:
            while self.isRunning:
                gtdp = self.nextGTdp()
                if gtdp is None:
                    continue

                if loop_func is not None:
                    loop_func(gtdp)
        except BaseException as e:
            print(f'gtdp_loop: {e}')
        print("gtdp_loop ended")

    def send_heartbeat(self):
        address = (self.target_ip, self.HEARTBEAT_PORT)
        if self.socket is not None:
            self.socket.sendto(self.heartbeat_content, address)
            print(f"Heartbeat sent to {address}")
        else:
            print("Socket was closed for heartbeat")

    def maintain_heartbeat(self):
        try:
            if self.isRunning:
                self.send_heartbeat()
                self.t = Timer(self.timer, self.maintain_heartbeat)
                self.t.start()
        except BaseException as e:
            print(f'maintain_heartbeat: {e}')

    def nextGTdp(self):
        try:
            rawdata, _ = self.socket.recvfrom(1024)
            if self.forward is not None:
                self.socket.sendto(rawdata, self.forward)
            return GTDataPacket(rawdata)
        except BaseException as e:
            print(f"BaseException {e}")
            return None

    #Externally called functions
    def firststart(self):
        self.toggle(True)

    def get_target_ip(self):
        return self.target_ip

    #no check on target_ip is a valid IPv4 address
    def set_target_ip(self, target_ip):
        self.target_ip = target_ip

    def is_running(self):
        return self.isRunning

    def close(self):
        def stopping():
            print("Stopping loop")
            self.isRunning = False
        self.threadPool.submit(stopping)
        if self.t is not None:
            self.t.cancel() #abort any running timer
        print("Ended timer function for heartbeat")
        self.threadPool.shutdown(wait=True)
