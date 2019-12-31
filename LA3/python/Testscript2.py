from threading import Thread
from LA3.python.http import http


def test_concurrent_write(name,index):
    URL = "http://localhost/foo/" + name
    i = str(index)
    headerstr = "Content-Type: application/json\r\nThread_no: "+i+"\r\n"
    bodyvalue = "I am Thread no. " + str(index) + " and I am writing the file."
    http(URL, bodyvalue, headerstr, True, False, "", "post").post_request(True)


no_of_threads = input("Enter no. of clients: ")
print("\n")
for i in range(0, int(no_of_threads)):
    Thread(target=test_concurrent_write, args=("out.txt", i)).start()