    # # Echo client program
    # import socket
    #
    # HOST = '192.168.0.204'    # The remote host
    # PORT = 50007              # The same port as used by the server
    # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #     s.connect((HOST, PORT))
    #     s.sendall(b'Hello, world1')
    #     data = s.recv(1024)
    #     print(data)
    #     s.sendall(b'Hello, world2')
    #     data = s.recv(1024)
    #     print(data)
    #     s.sendall(b'Hello, world3')
    #     data = s.recv(1024)
    #     print(data)
    # print('Received', repr(data))
    #------------------------------------------------------------------------------------------
    import socket

    HOST = 192.168.0.204
    PORT = 50007

    print("안내메시지(메뉴얼~~~~~)")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))

        while True:
            message = input("Client: ").strip()
            client_socket.sendall(message.encode("utf-8"))

            data = client_socket.recv(1024)
            reply = data.decode("utf-8")
            print("Server:", reply)

            if message == "exit":
                break
    #------------------------------------------------------------------------------------------
    # import socket
    #
    # HOST = '192.168.0.187'
    # PORT = 50007
    # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #     s.connect((HOST, PORT))
    #     print("서버 연결됨")
    #     while True:
    #         msg=input("서버에 보낼 메시지를 입력하세요: ")
    #         if not msg: continue
    #         s.sendall(msg.encode('utf-8'))
    #         data = s.recv(1024)
    #         print(f"서버로부터 받은 답장 : {data.decode('utf-8')}")