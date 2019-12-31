import socket
from LA3.python.packet import Packet
from LA3.python.makepacketclient import makepacketclient
from LA3.python.storepacketclient import storepacketclient
import ipaddress
import time
from threading import Lock
from datetime import datetime
import threading

class http:
    count = 0
    ab = 0

    def __init__(self, url, body, headers, is_verbose, is_write, output_file, req_type):  # constructor to add values

        self.port = 8007
        self.host = ""
        self.url = url
        self.body = body
        self.header = headers
        self.is_verbose = is_verbose
        self.is_write = is_write
        self.output_file = output_file
        self.reply_header = {}
        self.req_type = req_type
        self.path = ""
        self.router_port = 3000
        self.router_host = "localhost"
        self.responsereceived = False
        #self.makepacketclient = makepacketclient()
        self.storepacket = storepacketclient()
        self.handshake = False
        self.lock = Lock()


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
        if (resp_code == "301" or resp_code == "302" or resp_code == "300" or (resp_num > 300 and resp_num < 400)) and self.count <= 5:
            if 'Location' in self.reply_header.keys():
                url_r = self.reply_header['Location']
                #if self.host in url_r:
                if ("http://" in url_r) or ("https://" in url_r) or ("www." in url_r):
                    self.url = url_r
                    self.url_break(self.url)
                else:
                    url_s = self.host + url_r
                    self.url = url_s
                print("Redirecting to new URL:" + str(self.url))
                if self.req_type == "get":
                    self.get_request()
                elif self.req_type == "post":
                    self.post_request()
            else:
                print("There is no Redirecting URL in the Server Response")

        if "Content-Disposition" in self.reply_header.keys():
            #print("Disposition is found")
            value = self.reply_header["Content-Disposition"]
            if value == "attachment":
                self.is_write = True
                self.output_file = "server_response.txt"
            elif "attachment/" in value:
                self.is_write = True
                arr = value.split("/")
                self.output_file = arr[1]
            else:
                self.is_write = False


        if self.is_write:
            file_o = open(self.output_file, "w")
            if self.is_verbose:
                file_o.write(first_line[0] + " "+ resp_code + " " + resp_msg)
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


    def initialconnect(self, request, test_flag):    # Make a UDP connection and initiate handshaking
        self.count = self.count + 1
        try:
            peer_ip = ipaddress.ip_address(socket.gethostbyname(self.host))
            router = (self.router_host, self.router_port)
            #client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            data = "Hello Harsh"
            packet = Packet(packet_type= storepacketclient.syn_type, # syn_type = 0
                       seq_num= 0,
                       peer_ip_addr= peer_ip,
                       peer_port= self.port,
                       is_last = False,
                       timestamp=int(time.mktime(datetime.now().timetuple())),
                       payload= data.encode("utf-8"))

            print(packet)
            if packet.packet_type == storepacketclient.syn_type:
                print("Initiating handshaking -- sending sync message!")

            while (not self.handshake):
                try:
                    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    print("client is waiting for sync ack....")
                    client.sendto(packet.to_bytes(), router)
                    client.settimeout(4)
                    response, sender = client.recvfrom(1024)
                    client.settimeout(None)
                    packet = Packet.from_bytes(response)
                    print(packet)
                    print(self.handshake)
                except socket.timeout:
                    if packet.packet_type != storepacketclient.syn_ack_type:
                        print("No Sync Acknowledgement received during handshking, Sending Sync message again.")
                        #client.settimeout(0)
                        self.handshake = False
                    else:
                        self.handshake = True


            print("Sync Acknowledgement received from server, sending acknowledgement back.")
            packet = Packet(packet_type=storepacketclient.ack_type,  # syn_type = 0
                            seq_num=0,
                            peer_ip_addr=peer_ip,
                            peer_port=self.port,
                            is_last=True,
                            timestamp=int(time.mktime(datetime.now().timetuple())),
                            payload=data.encode("utf-8"))
            print(packet)
            client.sendto(packet.to_bytes(), router)
            port_no = self.port
            print(port_no)
            m = makepacketclient(self.reply_header, self.is_verbose)
            m.sendpackets(request, client, router, peer_ip, port_no)
        except OSError as err:
            print(err)
        except Exception as e:
            print(e)
        except socket.timeout:
            print("timeout error")
        #finally:
            #client.close()


    def url_break(self, url):
        #print("In url_break :   " + url)
        if url.startswith('https://'):
            len_u = len(url)
            url = url[8:len_u]
        elif url.startswith('http://'):
            len_u = len(url)
            url = url[7:len_u]
        pos = url.find('/')
        pos1 = url.find('?')
        if pos >=0:
            self.host = url[0:pos]
            #print("Host is  " + self.host)
            self.path = url[pos:len(url)]
            #print("Path is  " + self.path)
        elif pos1 >=0:
            self.host = url[0:pos1]
            #print("Host is  " + self.host)
        else:
            self.host = url[0:len(url)]
            #print("Host is  " + self.host)

    def post_request(self,test_flag):
        self.url_break(self.url)
        if self.path == "":
            self.path = "/"
        request = "POST " + self.path + " HTTP/1.1\r\n" + "Host: " + self.host+"\r\n" + self.header+"\r\n" + self.body
        #print("request is as follows :-")
        #print(request)
        if test_flag:
            resp = self.initialconnect(request, test_flag)
            return resp
        else:
            self.initialconnect(request, test_flag)

    def get_request(self, test_flag):
        self.url_break(self.url)
        if self.path == "":
            self.path = "/"
        request = "GET " + self.path + " HTTP/1.1\r\n" + "Host: " + self.host+"\r\n" + self.header+"\r\n"
        #print("request is as follows :-")
        #print(request)
        if test_flag:
            self.lock.acquire()
            self.initialconnect(request, test_flag)
            self.lock.release()
            #return resp
        else:
            self.initialconnect(request, test_flag)













