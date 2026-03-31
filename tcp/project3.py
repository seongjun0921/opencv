import socket
import threading
import datetime
import random
from datetime import *

HOST = "192.168.0.51"
PORT = 50007
ADMIN_PASSWORD = "0000"

vte = None
count,count1,count2 = 0,0,0
users = {}
lock = threading.Lock()
pool = threading.Semaphore(30)
votes = []
user_db = {}
bad_words_list = ["ㅅㅂ", "ㅄ", "ㅂㅅ", "ㅈㄴ", "ㅉㅉ", "ㄲㅈ", "ㅗ", "ㅆㅂ", "ㄷㅊ", "ㄴㅁ", "ㅁㅊ",
    "시발", "씨발", "존나", "졸라", "개새끼", "병신", "등신", "닥쳐",
    "꺼져", "미친", "호로", "씨부랄", "지랄", "염병", "상놈", "쓰레기",
    "찐따", "호구", "노답", "망할", "빡치네", "빡침","년아"]

emoticon = {"고양이": "🐸🐸🐸🐸🐸 ", "강아지": "U ´ᴥ` U", "돼지": "⍝◜ᐢ•⚇•ᐢ◝⍝", "표정": "(ง ͠° ͟ل͜ ͡°)ง"}


def send_to(conn, msg: str):
   try:
       conn.sendall((msg + "\n").encode("utf-8"))
   except:
       pass


def broadcast(msg: str, exclude=None):
   data = (msg + "\n").encode("utf-8")
   with lock:
       dead = []
       for c in list(users.keys()):
           if c is exclude:
               continue
           try:
               c.sendall(data)
           except:
               dead.append(c)


       for c in dead:
           users.pop(c, None)
           try:
               c.close()
           except:
               pass

#비속어 필터
def bad_words(msg):
    for word in bad_words_list:
        if word in msg:
            msg = msg.replace(word, len(word) * "*")
    return msg


#이모티콘
def emotion(msg):
    for key in emoticon:
        if f"/e{key}" in msg:
            msg = msg.replace(f"/e{key}", emoticon[key])
    return msg

def kick_conn(target_conn, reason="[관리자] 강제퇴장되었습니다."):
   send_to(target_conn, reason)
   try:
       target_conn.shutdown(socket.SHUT_RDWR)
   except:
       pass
   try:
       target_conn.close()
   except:
       pass
   with lock:
       users.pop(target_conn, None)


def handle_client(conn, addr):
   global count,vte,count1,count2, bad_words_list, user_db
   user_db[conn] = {"badword_count": 0, "mute_time": datetime.now(), "last_chat_time": datetime.now(), "chat_count": 0}
   conn.settimeout(None)
   with pool:
       print(f"[접속] {addr}")


       # 닉네임 받기
       send_to(conn, "닉네임을 입력하세요:")
       try:
           nickname = conn.recv(1024).decode("utf-8", errors="ignore").strip()
       except:
           nickname = ""


       if not nickname:
           nickname = f"{addr[0]}:{addr[1]}"


       with lock:
           used = set(info["name"] for info in users.values())
           base = nickname
           i = 2
           while nickname in used:
               nickname = f"{base}_{i}"
               i += 1

           my_color = '\033[0m'
           users[conn] = {"addr": addr, "name": nickname, "role": "USER", "color" : my_color}


       broadcast(f"[입장] {nickname} 님이 입장했습니다.")
       send_to(conn, "명령: 나가기: /quit 접속자 확인: /who 귓속말: /w 닉네임 메시지 관리자 승격: /admin 비번")
       # conn.settimeout(30.0)
       try:
           while True:
               data = conn.recv(4096)
               if not data:
                   break


               msg = data.decode("utf-8", errors="ignore").strip()
               if not msg:
                   continue

               now = datetime.now()

               if now < user_db[conn]["mute_time"]:
                   remain = int((user_db[conn]["mute_time"] - now).total_seconds())
                   conn.sendall(f"현재 {remain}초만큼 채팅금지".encode())
                   continue

               diff_time = (now - user_db[conn]["last_chat_time"]).total_seconds()
               user_db[conn]["last_chat_time"] = now
               if diff_time < 1:
                   user_db[conn]["chat_count"] += 1
                   if user_db[conn]["chat_count"] >= 5:
                       user_db[conn]["mute_time"] = datetime.now() + timedelta(seconds=5)
                       user_db[conn]["chat_count"] = 0
                       conn.sendall(f"도배로 5초간 채팅 금지".encode())
                       continue
               else:
                   user_db[conn]["chat_count"] = 0

               filtered = bad_words(msg)
               if filtered != msg:
                   msg = filtered
                   user_db[conn]["badword_count"] += 1
                   current_count = user_db[conn]["badword_count"]
                   if current_count >= 3:
                       user_db[conn]["mute_time"] = now + timedelta(seconds=5)
                       user_db[conn]["badword_count"] = 0
                       conn.sendall((f"욕설 3회 이상 5초간 채팅 금지".encode()))
                       continue

               if "/e" in msg:
                   msg = emotion(msg)

               with lock:
                   info = users.get(conn)
               if not info:
                   break


               me = info["name"]
               role = info["role"]



               if msg == "/quit":
                   break


               if msg == "/who":
                   with lock:
                       names = ", ".join(i["name"] for i in users.values())
                   send_to(conn, f"[접속자] {names}")
                   continue


               if msg.startswith("/w "):
                   parts = msg.split(" ", 2)
                   if len(parts) < 3:
                       send_to(conn, "[사용법] /w 대상닉 메시지")
                       continue
                   target_name, whisper = parts[1], parts[2]


                   target_conn = None
                   with lock:
                       for c, i in users.items():
                           if i["name"] == target_name:
                               target_conn = c
                               break


                   if not target_conn:
                       send_to(conn, f"[오류] '{target_name}' 사용자를 찾을 수 없습니다.")
                       continue


                   send_to(target_conn, f"[귓속말] {me} -> {target_name}: {whisper}")
                   send_to(conn, f"[귓속말] {me} -> {target_name}: {whisper}")
                   continue


               if msg.startswith("/admin "):
                   pw = msg.split(" ", 1)[1]
                   if pw == ADMIN_PASSWORD:
                       with lock:
                           users[conn]["role"] = "ADMIN"
                       send_to(conn, "[관리자] 관리자 권한이 부여되었습니다.")
                       broadcast(f"[시스템] {me} 님이 관리자가 되었습니다.")
                   else:
                       send_to(conn, "[오류] 관리자 비밀번호가 틀렸습니다.")
                   continue


               if msg.startswith("/notice "):
                   if role != "ADMIN":
                       send_to(conn, "[오류] 관리자만 공지를 보낼 수 있습니다.")
                       continue
                   notice = msg.split(" ", 1)[1]
                   broadcast(f"[공지] {notice}")
                   continue

               if msg.startswith("/color "):
                   par = msg.split(" ",2)
                   color = par[1].lower()
                   if color == "red":
                       users[conn]["color"] = "\033[91m"
                       send_to(conn,"빨간색으로 변경되었습니다.")
                   elif color == "blue":
                       users[conn]["color"] = "\033[94m"
                       send_to(conn, "파란색으로 변경되었습니다.")
                   elif color == "yellow":
                       users[conn]["color"] = "\033[93m"
                       send_to(conn, "노란색으로 변경되었습니다.")
                   elif color == "white":
                       users[conn]["color"] = "\033[0m"
                       send_to(conn, "하양색으로 변경되었습니다.")
                   else:
                       send_to(conn,"[오류] 지정된 색이 아닙니다. ")
                   continue

               if msg.startswith("/upgrade"):
                   a = random.randrange(1,100)
                   if a < 90:
                       count += 1
                       broadcast(f"""강화성공 
     _________________
     |                 |
     |                 |================================----------
     |      {count}강            |
     |                 |================================----------
     |_________________|
""")

                   else:
                       count = 0
                       broadcast(r"""
강화실패 장비가 터졌습니다.
 ___________________________________________
|                                           |
|  ██████╗  ██████╗  ██████╗ ███╗   ███╗    |
|  ██╔══██╗██╔═══██╗██╔═══██╗████╗ ████║    |
|  ██████╔╝██║   ██║██║   ██║██╔████╔██║    |
|  ██╔══██╗██║   ██║██║   ██║██║╚██╔╝██║    |
|  ██████╔╝╚██████╔╝╚██████╔╝██║ ╚═╝ ██║    |
|  ╚═════╝  ╚═════╝  ╚═════╝ ╚═╝     ╚═╝    |
|                                           |
 -------------------------------------------
""")
                   continue



               if msg.startswith("/vote_start "):
                   if role != "ADMIN":
                       send_to(conn, "[오류] 관리자만 공지를 보낼 수 있습니다.")
                       continue
                   vte = msg.split(" ", 1)[1]
                   broadcast(f'[투표]{vte}')
                   continue

               if msg.startswith("/vote "):
                   vt = msg.split(" ", 1)[1]
                   if users[conn]["name"] in votes:
                       send_to(conn,"이미투표를하셨습니다.")
                       continue
                   else:
                       if vt == "1":
                           count1 +=1
                           votes.append(users[conn]["name"])
                           send_to(conn,"1번을 투표하셨습니다.")
                       elif vt == "2":
                           count2 +=1
                           votes.append(users[conn]["name"])
                           send_to(conn,"2번을 투표하셨습니다.")
                       else:
                           send_to(conn, "투표번호가 아닙니다.")
                       continue

               if msg.startswith("/vote_state"):
                   broadcast(f"""       {vte} 투표 
            1번 투표수 : {count1} 2번 투표수 : {count2}
""")
                   continue



               if msg.startswith("/kick "):
                   if role != "ADMIN":
                       send_to(conn, "[오류] 관리자만 강제퇴장할 수 있습니다.")
                       continue


                   target_name = msg.split(" ", 1)[1]
                   target_conn = None
                   with lock:
                       for c, i in users.items():
                           if i["name"] == target_name:
                               target_conn = c
                               break


                   if not target_conn:
                       send_to(conn, f"[오류] '{target_name}' 사용자를 찾을 수 없습니다.")
                       continue


                   kick_conn(target_conn)
                   broadcast(f"[시스템] {target_name} 님이 강제퇴장되었습니다.")
                   continue
               broadcast(f"{info['color']}{me}: {msg}")


       except Exception as e:
           print(f"[오류] {addr} 처리 중 예외: {e}")
       finally:
           with lock:
               info = users.pop(conn, None)


           try:
               conn.close()
           except:
               pass


           if info:
               broadcast(f"[퇴장] {info['name']} 님이 나갔습니다.")
           print(f"[종료] {addr}")

def main():
   server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   server.bind((HOST, PORT))
   server.listen(50)
   print("채팅 서버 실행")


   while True:
       conn, addr = server.accept()
       threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
   main()
