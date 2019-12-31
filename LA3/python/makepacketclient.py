from LA3.python.packet import Packet
from LA3.python.storepacketclient import storepacketclient
import threading
import time
from datetime import datetime
#from LA3.python.http import http
class makepacketclient:

    def __init__(self, reply_header, is_verbose):
        self.seq_num = 0
        self.minlength = 22
        self.maxlength = 1024
        self.sentpackets = 0
        self.window = 10
        self.resendbuffer = {}
        self.storepacketacks = {}
        self.allacksreceived = False
        self.acklock = threading.Lock()
        #self.naklock = threading.Lock()
        #self.handleacknaklock = threading.Lock()
        #self.timeout = 5
        self.responsereceived = False
        #self.responselock = threading.Lock()
        self.resendlock = threading.Lock()
        self.storepacketclient = storepacketclient()
        self.initialindex = 0
        self.endindex = 0
        self.slidetimeout = 15
        self.expectedackno = 0
        self.acktimestamp = int(time.mktime(datetime.now().timetuple())) - 1
        self.reply_header = reply_header
        self.is_verbose = is_verbose




    def display_msg(self, msg):
        header_l = msg.split('\r\n\r\n')
        str_upper = header_l[0]
        str_lines = str_upper.split('\r\n')
        first_line = str_lines[0].split(' ')
        resp_code = first_line[1]
        resp_msg = ""
        for j in range(2, len(first_line)):
            resp_msg += first_line[j] + " "
        for line in range(1, len(str_lines)):
            string_h = str(str_lines[line])
            pos = string_h.find(":")
            pos = pos
            key_r = string_h[0:pos].strip()
            pos = pos+1
            length = len(string_h)
            value_r = string_h[pos:length]
            self.reply_header[str(key_r)] = str(value_r).strip()
        #print(self.reply_header)
        resp_num = int(resp_code)
        if "Content-Disposition" in self.reply_header.keys():
            #print("Disposition is found")
            value = self.reply_header["Content-Disposition"]
            if value == "attachment":
                is_write = True
                output_file = "server_response.txt"
            elif "attachment/" in value:
                is_write = True
                arr = value.split("/")
                output_file = arr[1]
            else:
                is_write = False


        if is_write:
            file_o = open(output_file, "w")
            if self.is_verbose:
                file_o.write(first_line[0] + " " + resp_code + " " + resp_msg + "\r\n")
                for line in range(1, len(str_lines)):
                    file_o.write(str_lines[line])
                    file_o.write("\r\n")
            file_o.write("\r\n")
            #file_o.write("Body:\n")
            for body_line in range(1, len(header_l)):
                file_o.write(header_l[body_line])
                file_o.write("\r\n")
            file_o.close()

        elif self.is_verbose:
            print("\nOutput: \n")
            #print("\nProtocol: ")
            print(first_line[0] + " "+ resp_code + " " + resp_msg)
            for line in range(1,len(str_lines)):
                print(str_lines[line])
            #print("\nBody: ")
            print("\r\n")
            for body_line in range(1, len(header_l)):
                print(header_l[body_line])
        else:
            print("\nOutput: \n")
            for body_line in range(1, len(header_l)):
                print(header_l[body_line])


    def reset(self):
        self.seq_num = 0
        self.allacksreceived = False
        self.resendbuffer = {}
        self.storepacketacks = {}
        self.sentpackets = 0
        self.expectedackno = 0

    def storeack(self, packet4mserver):
        #print("Store Acknowledgements")
        #self.acklock.acquire()
        seq = int(packet4mserver.seq_num)
        if packet4mserver.timestamp > self.acktimestamp:  # only save the ack if it is the latest one else discard
            self.storepacketacks[seq] = True
            if seq == self.expectedackno:
                self.expectedackno = self.expectedackno + 1
                self.acktimestamp = packet4mserver.timestamp
            print("Ack received for packet : " + str(seq))
        print(packet4mserver.timestamp)

        #self.acklock.release()

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
        #self.naklock.acquire()
        seq = int(packet4mserver.seq_num)
        packet = self.resendbuffer[seq]
        client.sendto(packet.to_bytes(), router)
        print("Resending packet : " + str(packet.seq_num))
        #self.naklock.release()

    def handleacknack(self, client, router):
        while not self.allacksreceived or not self.responsereceived:
            #print("Client waiting....")
            try:
                response, sender = client.recvfrom(1024)
                packet4mserver = Packet.from_bytes(response)
                print(packet4mserver)
                if packet4mserver.packet_type == storepacketclient.ack_type:
                    threading.Thread(target=self.storeack, args=(packet4mserver,)).start()
                elif packet4mserver.packet_type == storepacketclient.nak_type:
                    print("Nak received for packet : " + str(packet4mserver.seq_num))
                    threading.Thread(target=self.resendpacket, args=(packet4mserver, client, router)).start()
                elif packet4mserver.packet_type == storepacketclient.data_type:
                    #print("Data packet received by client:")
                    #print(packet4mserver)
                    #print(self.responsereceived)
                    resp = self.storepacketclient.storepacket(packet4mserver, client, sender)
                    #print("resp is:")
                    #print(resp)
                    if resp != '':
                        print("Entire response from server has been received by the client:\n")
                        resp = bytes(resp).decode("utf-8")
                        self.responsereceived = True
                        #http.display_msg(resp)
                        print("Server Response: \n")
                        #print(resp) #Printing final output from the server
                        #print("\n\n")
                        self.display_msg(resp)
                        print("\n\n")
                        exit()
                    else:
                        print("Not all packets for server response have been received, Client is waiting....")
                        #print(self.responsereceived)
            except Exception as e:
                print(e)



    def sendpackets(self, request, client, router, peer_ip, port):
        print("\nRequest is :\n")
        print(request)
        print("\n\n")
        #print("sending packets")
        maxdatasent = self.maxlength - self.minlength
        datalength = len(request)
        if datalength != 0:
            print("Start receiving acknowledgements")
            threading.Thread(target=self.handleacknack, args=(client, router)).start()

        print("Sending Data packets :")
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
                #print("content for packet" + str(self.seq_num) + ":\n")
                #print(sentdata)
                #print("\nends")
                packet = Packet(packet_type=storepacketclient.data_type,  # syn_type = 0
                                seq_num=self.seq_num,
                                peer_ip_addr=peer_ip,
                                peer_port=port,
                                is_last=lastpacket,
                                timestamp=int(time.mktime(datetime.now().timetuple())),
                                payload=sentdata.encode("utf-8"))

                print(packet)
                seq = int(self.seq_num)
                self.resendbuffer[seq] = packet
                self.storepacketacks[seq] = False

                client.sendto(packet.to_bytes(), router)
                self.seq_num += 1
                datalength = datalength - payloadlength

                time.sleep(1) #to have difference in timestamp of packet send

                if self.sentpackets == self.window or datalength == 0:
                    print("Packets sent from client are: ")
                    print(self.resendbuffer)
                    break
            self.checkallacksreceived()
            while not self.allacksreceived and not self.responsereceived:
                time.sleep(self.slidetimeout)
                self.checkallacksreceived()
                if self.allacksreceived or self.responsereceived:
                    if self.allacksreceived:
                        print("All acks are received by the client")
                        break
                    if self.responsereceived:
                        exit()
                else:
                    self.resendunackedpackets(client, router) # after timeout: resend all the non-acked packets
            if self.sentpackets == self.window or datalength == 0:
                print("Entire window is sent: resetting the client window now.")
                #print(datalength)
                self.reset()





