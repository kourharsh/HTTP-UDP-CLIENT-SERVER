from LA3.python.packet import Packet
import threading
#from numpy import uint32
import time
from datetime import datetime

class storepacketclient:
    """
    Packet represents a simulated UDP packet.
    """
    syn_type = 0
    syn_ack_type = 1
    ack_type = 2
    data_type = 3
    nak_type = 4
    window = 10

    def __init__(self):
        self.seq_num = 0
        self.last_packet = False
        self.good_packets = {}
        self.all_packets_received = False
        self.expectedseq_num = 0
        self.resp = b''
        self.datatimestamp = int(time.mktime(datetime.now().timetuple())) - 1

    def combinemsg(self):
        print("combining all packets")
        #print("All packets received are:")
        #print(self.good_packets)
        count = len(self.good_packets.keys())
        for key in range(0,count):
            print(self.good_packets[key])
            self.resp = self.resp + self.good_packets[key]
        return self.resp

    def reset(self):
        self.seq_num = 0
        self.good_packets = {}
        self.expectedseq_num = 0

    def checkwindowreceived(self):
        s = 0
        flag = False
        for seq in range(s, storepacketclient.window):
            if seq in self.good_packets.keys():
                flag = True
            else:
                flag = False
                break
        return flag

    def sendack(self,packet, listener, sender):
        data = "ack"
        packet_ack = Packet(packet_type=storepacketclient.ack_type,
                        seq_num=packet.seq_num,
                        peer_ip_addr=packet.peer_ip_addr,
                        peer_port=packet.peer_port,
                        is_last=False,
                        timestamp=int(time.mktime(datetime.now().timetuple())),
                        payload=data.encode("utf-8"))
        listener.sendto(packet_ack.to_bytes(), sender)  # send acknowledgement even if this is a duplicate packet

    def storepacket(self, packet, listener, sender):
        try:
            #print("Storing packets in buffer")
            if (packet.packet_type ==  storepacketclient.data_type) and packet.seq_num >= self.expectedseq_num and packet.seq_num < (self.expectedseq_num + storepacketclient.window):
                #if packet.seq_num not in self.good_packets.keys():
                self.sendack(packet, listener, sender)
                if packet.timestamp > self.datatimestamp:
                    print("Sending ACK for :" + str(packet.seq_num))
                    if packet.seq_num == self.expectedseq_num:
                        self.expectedseq_num += 1
                        self.datatimestamp = packet.timestamp
                    seqno = int(packet.seq_num)
                    self.good_packets[seqno] = packet.payload
                    #self.seq_num = max(self.good_packets.keys())
                    windowreceived = self.checkwindowreceived()
                    if packet.is_last == 1:
                        print("Last packet received")
                        self.last_packet = True
                    if self.last_packet:
                        packetlist = []
                        #print(self.good_packets)
                        #print(self.good_packets.keys())
                        # list2 = list(self.good_packets.keys()).sort()
                        list2 = []
                        for i in self.good_packets.keys():
                            list2.append(i)
                        #print(list2)
                        self.seq_num = max(list2)
                        #print(self.seq_num)
                        while(packet.seq_num in self.good_packets.keys() and packet.seq_num >=0):
                            #print("Inside while loop")
                            #print(self.seq_num)
                            packetlist.append(self.seq_num)
                            packetlist.sort()
                            list2.sort()
                            #print(packetlist)
                            #print(list2)
                            # list2 = list(self.good_packets.keys()).sort()
                            if self.seq_num == 0 and packetlist == list2:
                                print("All packets are received")
                                #print(packetlist)
                                #print(list2)
                                self.all_packets_received = True
                                break
                            else:
                                self.seq_num = self.seq_num - 1
                        if self.all_packets_received:
                            #print("All packets are received")
                            resp = self.combinemsg()
                            self.reset()
                            self.resp = b''
                            self.last_packet = False
                            return resp
                        else:
                            print("All packets have not been received yet by client")
                            resp = ""
                            return resp
                    elif windowreceived:
                        print(" entire window received for client")
                        print(self.datatimestamp)
                        self.combinemsg()
                        self.reset()
                    else:
                        resp = ""
                        return resp
                else:
                    resp = ""
                    print("Duplicate packet received and discarded")
                    print(packet.timestamp)
                    return resp
            resp = ""
            return resp
        finally:
            print("")

