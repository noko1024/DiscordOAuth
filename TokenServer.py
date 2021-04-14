import socket

soc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
soc.bind(("127.0.0.1", 51994))
soc.listen(1)

oneTimeURL = []

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
            oneTimeURL.remove(recv.lstrip("AUTH-"))
        else:
            connection.send(bytes("False","utf-8"))
    
    elif recv.lstrip("DEL-") in oneTimeURL:
        oneTimeURL.remove(recv.lstrip("DEL-"))
        connection.send(bytes("True","utf-8"))

    print(oneTimeURL)
    connection.close()