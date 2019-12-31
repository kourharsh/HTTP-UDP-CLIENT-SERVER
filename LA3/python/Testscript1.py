from threading import Thread
from LA3.python.http import http


def test_concurrent_read(name,index):
    URL = "http://localhost/foo/" + name
    i = str(index)
    headerstr = "Content-Type: application/json\r\nThread_no: "+i+"\r\n"
    http(URL, index, headerstr, True, False, "", "get").get_request(True)
    #print("Response for client " + i + " : \n")
    #print(resp)
    #print("\n\n")


no_of_threads = input("Enter no. of clients: ")
print("\n")
for i in range(0, int(no_of_threads)):
    Thread(target=test_concurrent_read, args=("output.txt", i)).start()
