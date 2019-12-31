class httplib:
    def __init__(self, status, msg, dict):
        self.status = status
        self.msg = msg
        self.header = dict
        self.headerstr = ""


    def get_response_msg(self):
        msg = ""
        if self.status == 200:
            msg = "OK"
        elif self.status == 400:
            msg = "Bad Request"
        elif self.status == 404:
            msg = "File Not Found"
        elif self.status == 405:
            msg = "Method Not Allowed"
        elif self.status == 403:
            msg = "Security Error"
        else:
            msg = "Unknown Error"
        return msg

    def create_header(self, header, bodyvalue):  # to convert header dictionary to header_string
        print("Inside create header")
        header_string = ""
        if "Content-Type" in header:
            pass
        else:
            header["Content-Type"] = "application/json"

        if "Content-Disposition" in header:
            pass
        else:
            header["Content-Disposition"] = "inline"

        header["Content-Length"] = str(len(self.msg))
        header["Accept-language"] = "en"
        #print("dictionary is: ")
        #print(header)
        for key, value in header.items():
            header_string = header_string + key + ": " + value + "\r\n"
        return header_string

    def add_header(self, key, val):
        self.header[key] = val

    def response_head(self):
        respmsg = self.get_response_msg()
        self.headerstr = self.create_header(self.header, self.msg)
        resphead = "HTTP/1.1 " + str(self.status) + " " + respmsg + "\r\n" + self.headerstr + "\r\n"
        print("\n httblib Response head :\n" + resphead)
        return resphead

