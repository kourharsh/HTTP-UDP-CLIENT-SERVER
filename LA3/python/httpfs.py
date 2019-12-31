import socket
import threading
from threading import Lock
import os
import json
import pathlib
from mimetypes import MimeTypes
from LA2.httplib import httplib
from LA3.python.packet import Packet
from LA3.python.makepacketserver import makepacketserver
from LA3.python.storepacketserver import storepacketserver
import binascii


class httpfs:
    def __init__(self, inputarray, directory):
        self.inputarray = inputarray
        self.port = 8007
        self.curr_directory = directory
        self.directory = directory
        self.debugging = False
        self.action = ""
        self.header_dict = {}
        self.req_body = ""
        self.query = ""
        self.path = ""
        self.error_code = 200
        self.host = 'localhost'
        self.client_body = ""
        self.isDirectory = False
        self.isFile = False
        self.lock = Lock()
        self.file_directory = ""
        self.patheditflag = False
        self.router_port = 3000
        self.router_host = "localhost"
        self.handshaking = False
        self.storepacket = storepacketserver()
        self.makepackserver = makepacketserver()
        self.response = ""


    def checkinput(self):
        for i in range(0, len(self.inputarray)):
            if (self.inputarray[i] == '-p'):
                self.port = int(self.inputarray[i+1])
            if (self.inputarray[i] == '-d'):
                self.curr_directory = self.curr_directory + self.inputarray[i+1]
                #print(self.curr_directory)
                if os.path.exists(self.curr_directory):
                    if self.debugging:
                        print("Server Directory is :   " + self.curr_directory)
                else:
                    print("Error!! The current directory " + self.curr_directory + " for the server does not exists.")
                    exit()
            if (self.inputarray[i] == '-v'):
                self.debugging = True
        self.run_server()


    def run_server(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            listener.bind((self.host, self.port))
            print('File server has been initialized and is listening at', self.port, ' :')
            while True:
                data, sender = listener.recvfrom(1024)
                threading.Thread(target=self.handle_client_packet, args=(listener,data, sender)).start()
        finally:
            print("")
            #listener.close()

    def handle_client_packet(self, listener, data, sender):

        packet = Packet.from_bytes(data)
        print("Server received a new packet:")
        print(packet)
        #print(packet.timestamp)
        #print(self.handshaking)
        if packet.packet_type == storepacketserver.syn_type:
            print("Sync message received from client!")
            packet.packet_type = storepacketserver.syn_ack_type
            self.handshaking = True
            packet.is_last = False
            listener.sendto(packet.to_bytes(), sender)
        elif packet.packet_type == storepacketserver.ack_type and not self.handshaking and packet.is_last == 1:
            print("Ack received from client, Handshaking is now done!")
            self.handshaking = True
        elif packet.packet_type == storepacketserver.ack_type and packet.is_last == 0: #all acks have is_last == 0
            print("ACK received for Server response with seq : " + str(packet.seq_num))
            self.makepackserver.storeack(packet)
        elif self.handshaking:
            self.lock.acquire()
            print("Data transfer now begins")
            #print("Server received a new packet:")
            #print(packet)

            resp = self.storepacket.storepacket(packet, listener, sender)
            print(resp)
            if resp != "":

                request = self.handle_client_request(resp, sender)
                router = (self.router_host, self.router_port)
                self.makepackserver.sendpackets(request, listener, router, packet.peer_ip_addr, packet.peer_port)
                self.reset()
            else:
                print("All packets are not received yet!")
            self.lock.release()
        else:
            print("Invalid packet: packet has been discarded") #when handshaking flag is false and server has been reset


    def handle_client_request(self, resp, addr):
        #print("Handling client request")
        #print(resp)
        try:
            #while True:
             #   data = server.recv(2048)
            #resp = binascii.a2b_uu(resp)
            #resp = self.new_break_req(resp)
            resp = bytes(resp).decode("utf-8")
            #print(resp)
            #print(bytes(resp).decode("utf-8"))
            if self.debugging:
                print("Processing a new request for the server:")
             #       print(data)
             #   if not data:
              #      break
            #self.lock.acquire()
            self.break_req(resp)# break the client request for server to understand
            self.checksecurity()
            if self.error_code != 400:
                self.directory = self.curr_directory + self.path
                try:
                    if self.action == "GET":
                        self.make_file_name()
                        if os.path.exists(self.directory):
                            flagorig = True
                            flagnew = False
                        else:
                            flagorig = False
                            if os.path.exists(self.file_directory):
                                flagnew = True
                                self.directory = self.file_directory
                            else:
                                flagnew = False
                        if flagorig or flagnew:
                            if self.debugging:
                                print("Valid Path!")
                            self.isDirectory = os.path.isdir(self.directory)
                            if self.isDirectory:
                                self.error_code = 200
                                files = os.listdir(self.directory)
                                self.req_body = json.dumps(files)
                                if self.debugging:
                                    print("Returning a list of the current files in the current data directory!",
                                            self.directory)
                                    print("Files returned from the server: ")
                                    print(self.req_body)
                            else:
                                self.isFile = os.path.isfile(self.directory)
                                if self.isFile:
                                    if self.debugging:
                                        print("Returning the content of the file in the data directory",
                                                self.directory)
                                    file_read = open(self.directory, "r")
                                    self.req_body = file_read.read()
                                    file_read.close()
                        else:
                            if self.debugging:
                                print("Path could not be found : ", self.directory)
                            self.error_code = 404

                    elif self.action == "POST":
                        pathlib.Path(os.path.dirname(self.directory)).mkdir(parents=True, exist_ok=True)
                        self.make_file_name()
                        if self.patheditflag:
                            self.directory = self.file_directory
                        file_o = open(self.directory, "w")
                        file_o.write(self.client_body)
                        file_o.close()
                        self.error_code = 200
                        self.req_body = self.client_body
                        self.isFile = True

                except OSError as err:
                    if self.debugging:
                        print(err)
                    self.error_code = 400
                    self.req_body = ""
                except SystemError as err:
                    if self.debugging:
                        print(err)
                    self.error_code = 400
                    self.req_body = ""
            if self.isDirectory:
                self.header_dict["Content-Type"] = "application/json"
            elif self.isFile:
                if self.patheditflag:
                    self.directory = self.file_directory
                    #print("File type")
                mimes_all = MimeTypes()
                mime_type = mimes_all.guess_type(self.directory)
                #print(mime_type[0])
                self.header_dict["Content-Type"] = mime_type[0]

            resp = httplib(self.error_code, self.req_body, self.header_dict)
            self.response = resp.response_head() + self.req_body
            if self.debugging:
                print('Response is :\n',self.response)
                #print('\nrequest body is: \n' + self.req_body)
            return self.response
                #server.sendall(response.encode("ascii"))
            #self.makepacket.makepackets(response, addr)
            #TODO: check what needs to be passed to send packets back to client

            #self.error_code = 200
            #self.header_dict = {}
            #self.lock.release()
        finally:
            print("")
            #server.close()

    def break_req(self, msg):
        #print("In break request: ")
        #print(msg)
        #print("\n\n msg ends here")
        header_l = msg.split('\r\n\r\n')
        str_upper = header_l[0]
        self.client_body = header_l[1]
        #print(self.client_body)
        #print("\n\n client body ends")
        str_lines = str_upper.split('\r\n')
        first_line = str_lines[0].split(' ')
        self.action = first_line[0]
        if self.debugging:
            print("action is: ", self.action)
        self.search = first_line[1]
        #if self.debugging:
         #   print("Search folder is: ", self.search)

        if "?" in self.search:          # find the query and path
            pos = self.search.find("?")
            pos = pos
            key_r = self.search[0:pos].strip()
            pos = pos + 1
            length = len(self.search)
            value_r = self.search[pos:length]
            self.path = key_r
            self.query = value_r
        else:
            self.path = self.search

        for line in range(1, len(str_lines)):  # store all the headers from request to dictionary
            string_h = str(str_lines[line])
            pos = string_h.find(":")
            pos = pos
            key_r = string_h[0:pos].strip()
            pos = pos+1
            length = len(string_h)
            value_r = string_h[pos:length]
            self.header_dict[str(key_r)] = str(value_r).strip()
        #print(self.header_dict)
        #print(self.client_body)

    def new_break_req(self, resp):
        data = b''
        for b in resp:
            b = b.to_bytes(1, byteorder='big')
            data = data + b
        return data

    def reset(self):
        self.port = 8080
        self.debugging = False
        self.action = ""
        self.header_dict = {}
        self.req_body = ""
        self.query = ""
        self.path = ""
        self.error_code = 200
        self.host = 'localhost'
        self.client_body = ""
        self.isDirectory = False
        self.isFile = False
        self.file_directory = ""
        self.patheditflag = False
        self.handshaking = False
        self.storepacket = storepacketserver()
        self.makepackserver = makepacketserver()
        self.client_body = ""
        self.response = ""

    def make_file_name(self):
        pathlist = (self.directory).split("\"")
        file_name = pathlist[-1]
        if (".pdf" in file_name) or (".txt" in file_name) or (".json" in file_name) or (".html" in file_name) or (".xml" in file_name) :
            pass
        else:
            if "Content-Type" in self.header_dict.keys():
                type = self.header_dict["Content-Type"]
            else:
                type = "application/json"
            if type == "application/json" or type == "json":
                filetype = ".json"
            elif type == "text/plain" or type == "text":
                filetype = ".txt"
            elif type == "text/html" or type == "html":
                filetype = ".html"
            elif type == "text/pdf" or type == "pdf":
                filetype = ".pdf"
            elif type == "text/xml" or type == "xml":
                filetype = ".xml"
            else:
                filetype = ".txt"
            self.file_directory = self.directory + filetype
            self.patheditflag = True
            #if self.debugging:
             #   print("Searching File directory: " + self.file_directory)


    def checksecurity(self):
        if ".." in self.path:
            if (self.debugging):
                print("Access is denied for the requested path! ", self.path)
            self.error_code = 403
        else:
            self.error_code = 200


inputserver = input("Please enter the command:\n")
inputarr_serv = inputserver.split(" ")
while '' in inputarr_serv:
    inputarr_serv.remove('')

if (inputarr_serv[0] == 'httpfs'):
    if (len(inputarr_serv) > 1) and (inputarr_serv[1] == 'help'):
        print("\n\nusage: httpfs [-v] [-p PORT] [-d PATH-TO-DIR]\n")
        print("-v    Prints debugging messages")
        print("-p    Specifies the port number that the server will listen and serve at.")
        print("      Default is 8080")
        print("-d    Specifies the directory that the server will use to read/write requested files. Default is the")
        print("      current directory when launching the application.")
    else:
        current_directory = os.getcwd() + "/files"
        print(current_directory)
        httpfs(inputarr_serv[1:],current_directory).checkinput()
else:
    print("Invalid Command!")
    exit()
