from os import stat_result
import socket
import string
import random

soc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
soc.bind(("127.0.0.1", 51994))
soc.listen(1)

oneTimeURL = []

#会長、副会長、会計のID
adminToken = {
            420123114014375946 : "",
            482477830664355850 : "",
            562308096538705930 : ""
                }

try:
    while True:
        connection, address = soc.accept()
        recv = connection.recv(4096).decode()
        print(oneTimeURL)
        print(recv)

        if recv.startswith("GEN-"):
            oneTimeURL.append(recv.lstrip("GEN-"))
        
        elif recv.startswith("AUTH-"):
            if recv.lstrip("AUTH-") in oneTimeURL:
                connection.send(bytes("True","utf-8"))
            else:
                connection.send(bytes("False","utf-8"))
    
        elif recv.startswith("DEL-"):
            if recv.lstrip("DEL-") in oneTimeURL:
                oneTimeURL.remove(recv.lstrip("DEL-"))
                connection.send(bytes("True","utf-8"))

        elif recv.startswith("ADMINAUTH-"):
            if recv.lstrip("ADMINAUTH-") in adminToken:
                connection.send(bytes("True","utf-8"))
            else:
                connection.send("False","utf-8")
        
        elif recv.startswith("ADMINGEN-"):
            userID = int(recv.lstrip("ADMINGEN-"))
            if userID in adminToken:
                adminToken[userID] = ''.join(random.choices(string.ascii_letters + string.digits, k=30))
                connection.send(["True",adminToken[userID]],"utf-8")
            else:
                connection.send(["False"],"utf-8")

        print(oneTimeURL)
        connection.close()

except KeyboardInterrupt:
    print(oneTimeURL)
    soc.close()