from LA3.python.packet import Packet
from LA3.python.storepacketserver import storepacketserver
import threading
import time
from datetime import datetime
class makepacketserver:

    def __init__(self):
        self.seq_num = 0
        self.minlength = 22
        self.maxlength = 1024
        self.sentpackets = 0
        self.window = 10
        self.resendbuffer = {}
        self.storepacketacks = {}
        self.allacksreceived = False
        self.acklock = threading.Lock()
        self.naklock = threading.Lock()
        self.handleacknaklock = threading.Lock()
        self.timeout = 5
        self.responsereceived = False
        self.responselock = threading.Lock()
        self.resendlock = threading.Lock()
        self.storepacketserver = storepacketserver()
        self.initialindex = 0
        self.endindex = 0
        self.slidetimeout = 5
        self.servertimeoutcounter = 9
        self.expectedackno = 0
        self.acktimestamp = int(time.mktime(datetime.now().timetuple())) - 1

    def reset(self):
        self.seq_num = 0
        self.allacksreceived = False
        self.resendbuffer = {}
        self.storepacketacks = {}
        self.sentpackets = 0
        self.expectedackno = 0

    def storeack(self, packet4mserver):
        #print("Store Acknowledgements")
        self.acklock.acquire()
        seq = int(packet4mserver.seq_num)
        if packet4mserver.timestamp > self.acktimestamp: #only save the ack if it is the latest one else discard
            self.storepacketacks[seq] = True
            if seq == self.expectedackno:
                self.expectedackno = self.expectedackno + 1
                self.acktimestamp = packet4mserver.timestamp
            print("Ack received for packet : " + str(seq))
        self.acklock.release()

    def checkallacksreceived(self):
        flag = False
        for key in self.resendbuffer.keys():
            key = int(key)
            if self.storepacketacks[key] == False:
                flag = False
                break
            else:
                flag = True
        if flag and (self.sentpackets == len(self.resendbuffer.keys())):
            self.allacksreceived = True
        else:
            self.allacksreceived = False
        print(self.storepacketacks)
        print(self.allacksreceived)

    def resendunackedpackets(self, client, router):
        self.resendlock.acquire()
        print("Resending unacked packets")
        for key in self.storepacketacks.keys():
            if self.storepacketacks[key] == False:
                packet = self.resendbuffer[key]
                client.sendto(packet.to_bytes(), router)
                print("Resending packet : " + str(packet.seq_num))
        self.resendlock.release()




    def resendpacket(self,packet4mserver, client, router):
        print("Resending packet for Nak has been received")
        self.naklock.acquire()
        seq = int(packet4mserver.seq_num)
        packet = self.resendbuffer[seq]
        client.sendto(packet.to_bytes(), router)
        print("Resending packet : " + str(packet.seq_num))
        self.naklock.release()


    def sendpackets(self, request, client, router, peer_ip, port):
        print("Server sending packets")
        maxdatasent = self.maxlength - self.minlength
        datalength = len(request)
        while datalength > 0:
            while self.sentpackets < self.window and datalength > 0:
                self.sentpackets += 1
                if datalength > maxdatasent:
                    payloadlength = maxdatasent
                    lastpacket = False
                else:
                    payloadlength = datalength
                    lastpacket = True

                if self.seq_num == 0 and self.endindex == 0:
                    self.initialindex = 0
                else:
                    self.initialindex = self.endindex + 1

                self.endindex = self.initialindex + payloadlength

                sentdata = request[self.initialindex:self.endindex]
                #print(sentdata)

                packet = Packet(packet_type=storepacketserver.data_type,  # syn_type = 0
                                seq_num=self.seq_num,
                                peer_ip_addr=peer_ip,
                                peer_port=port,
                                is_last=lastpacket,
                                timestamp=int(time.mktime(datetime.now().timetuple())),
                                payload=sentdata.encode("utf-8"))

                print(packet)
                #print(packet.timestamp)
                seq = int(self.seq_num)
                self.resendbuffer[seq] = packet
                self.storepacketacks[seq] = False

                client.sendto(packet.to_bytes(), router)
                self.seq_num += 1
                datalength = datalength - payloadlength

                time.sleep(1)  # to have difference in timestamp of packet send

                if self.sentpackets == self.window or datalength == 0:
                    print("Packets sent from server are: ")
                    print(self.resendbuffer)
                    break
            self.checkallacksreceived()
            counter = 0
            while not self.allacksreceived:
                time.sleep(self.slidetimeout)
                self.checkallacksreceived()
                if self.allacksreceived:
                    print("All acks are received by the server")
                    break
                else:
                    self.resendunackedpackets(client, router) # after timeout: resend all the non-acked packets
                    counter = counter + 1
                    if counter == self.servertimeoutcounter:
                        self.allacksreceived = True #assume that client has now received the packets

            if self.sentpackets == self.window or datalength == 0:
                print("Entire window is sent: resetting the server window now.")
                #print(datalength)
                self.reset()





