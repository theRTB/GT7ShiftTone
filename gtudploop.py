# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 20:46:18 2024

@author: RTB
"""

import socket
from threading import Timer
from concurrent.futures.thread import ThreadPoolExecutor
from gtdatapacket import GTDataPacket

#TODO:
# - use ipaddress library for target_ip
# - consider a second socket to send packets, to set two different timeouts
# - replace 1024 in recvfrom with correct packet size, if there are multiple
#   packets in queue, this may mess things up. So far so good.

#Class to manage the incoming/outgoing packet stream from/to the PS5
#loop_func is called for each consecutive received packet
#Default socket timeout is 15 seconds, this seems to delay exiting any program
#Sends a heartbeat every 10 seconds

class GTUDPLoop():
    RECV_PORT = 33740
    HEARTBEAT_PORT = 33739
    HEARTBEAT_TIMER = 10 # in seconds
    HEARTBEAT_CONTENT = b'A'
    
    def __init__(self, target_ip, loop_func=None):
        self.threadPool = ThreadPoolExecutor(max_workers=8,
                                             thread_name_prefix="exec")
        self.isRunning = False
        self.socket = None
        self.t = None

        self.target_ip = target_ip
        self.loop_func = loop_func

    def init_socket(self):
        if self.socket is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(1)
            sock.bind(('', self.RECV_PORT))
        return sock
    
    #Toggles the packet loop with a logical 'xor' on boolean toggle
    #If toggle is false: loop will be stopped if it is running
    #if toggle is true: loop will be started if it is not running
    def toggle(self, toggle=None):
        if toggle and not self.isRunning:
            def starting():
                print("Starting loop")
                self.isRunning = True
                #This was an attempt to close the socket after the loop ends
                #Not sure it is succesful.
                with self.init_socket() as self.socket:
                    self.maintain_heartbeat()
                    self.gtdp_loop(self.loop_func)
                self.socket = None #This runs after the loop stops!
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
            print(e)
        print("gtdp_loop ended")

    def send_heartbeat(self):
        address = (self.target_ip, self.HEARTBEAT_PORT)
        if self.socket is not None:
            self.socket.sendto(self.HEARTBEAT_CONTENT, address)
            print("Heartbeat sent")
        else:
            print("Socket was closed for heartbeat")

    def maintain_heartbeat(self):
        try:
            if self.isRunning:
                self.send_heartbeat()
                self.t = Timer(self.HEARTBEAT_TIMER, self.maintain_heartbeat)
                self.t.start()
        except BaseException as e:
            print(e)

    def set_target_ip(self, target_ip):
        self.target_ip = target_ip

    def is_running(self):
        return self.isRunning

    def close(self):
        self.isRunning = False
        if self.t is not None:
            self.t.cancel() #abort any running timer
        print("Ended timer function for heartbeat")
        self.threadPool.shutdown(wait=False)
        
    def nextGTdp(self):
        try:
            rawdata, _ = self.socket.recvfrom(1024)
            return GTDataPacket(rawdata)
        except BaseException as e:
            print(f"BaseException {e}")
            return None