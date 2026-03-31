# tcp 핵심 특징
# 1. 연결지향 (3way handshake)
# syn 데이터 보내도 되는지 체크
# syn-ack 데이터 받을 준비 되었음 알림
# ack 데이터 전송 시작
#
# 2. tcp는 순서를 보장
# 시퀀스 넘버: 패킷에 번호를 부여해서, 수신측에서 도착한데이터를 순서대로 풀 수 있도록함

# 확인응답 ack: 데이터 받았다는 응답, 이 응답 오지 않으면 데이터 유실로 판단하고 재전송함

#3. 흐름제어
# 받는 쪽 처리 속도가 느리면 보내는 속도를 줄인다.

#4 전이중 통신
# 데이터가 양방향으로 당시에 흐를 수 있다.



#tcp vs udp
#tcp는 신뢰성 확인 과정으로 속도가 느림, 데이터 순서가 보장됨
#udp 실시간 강조하는 환겨에 적합, 확인과정이 없어 빠름

#바이터 데이터를 문자열로 변환: 디코딩
#data.decode('utf-8')
#메세지를 보낼 때 문자열로 인코딩해서 전송
# s.sendall("안녕하세요.encode('utf-8')

import tkinter as tk
import socket

SERVER_IP = "192.168.0.187"
SERVER_PORT = 9999

def send_command(command):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            s.connect((SERVER_IP, SERVER_PORT))
            s.send(command.encode('utf-8'))

    except Exception as e:
        print("에러", e)

root = tk.Tk()
root.title("브릿지 조종")
root.geometry("400x450")

btn_frame = tk.Frame(root)
btn_frame.pack(pady=20)

def create_btn(text, cmd, r, c):
    btn = tk.Button(btn_frame, text=text, width = 10, height = 2, command= lambda: send_command(cmd))
    btn.grid(row=r, column=c,padx=10,pady=10)
    return btn

create_btn("forward", "w", 0, 1)
create_btn("left", "a", 1, 0)
create_btn("stop", "s", 1, 1)
create_btn("right", "d", 1, 2)
create_btn("backward", "x", 2, 1)

root.bind("<w>", lambda e:send_command("w"))
root.bind("<s>", lambda e:send_command("s"))
root.bind("<d>", lambda e:send_command("d"))
root.bind("<a>", lambda e:send_command("a"))
root.bind("<x>", lambda e:send_command("x"))
root.mainloop()