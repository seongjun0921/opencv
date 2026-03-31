import socket
import threading
from datetime import *
import random

HOST = "192.168.0.51"
PORT = 50007
ADMIN_PASSWORD = "0000"

vte = None
count, count1, count2 = 0, 0, 0
users = {}

# [수정 1] Lock을 RLock(재진입 가능 락)으로 변경하여 데드락 방지
lock = threading.RLock()
pool = threading.Semaphore(30)
votes = []
user_db = {}
rooms = {}
bad_words_list = ["ㅅㅂ", "ㅂㅅ", "ㅈㄴ", "ㅉㅉ", "ㄲㅈ", "ㅗ", "ㅆㅂ", "ㄷㅊ", "ㄴㅁ", "ㅁㅊ",
                  "시발", "씨발", "존나", "졸라", "개새끼", "병신", "등신", "닥쳐",
                  "꺼져", "미친", "호로", "씨부랄", "지랄", "염병", "상놈", "쓰레기",
                  "찐따", "호구", "노답", "망할", "빡치네", "빡침", "년아"]

emoticon = {"이모티콘1": r"""
      |\      _,,,---,,_
ZZZzz /,`.-'`'    -.  ;-;;,_
     |,4-  ) )-,_. ,\ (  `'-'
    '---''(_/--'  `-'\_)
    <  야옹! 채팅 서버에 왔다옹! >

    """, "이모티콘2": "U ´ᴥ` U", "이모티콘3": "⍝◜ᐢ•⚇•ᐢ◝⍝", "이모티콘4": "(ง ͠° ͟ل͜ ͡°)ง"}


def send_to(conn, msg: str):
    try:
        conn.sendall((msg + "\n").encode("utf-8"))
    except:
        pass


def broadcast_all(msg):
    with lock:
        for c in users.keys():
            send_to(c, msg)


def broadcast_room(room, msg):
    now = datetime.now()
    data = (
        f"{msg}\t"
        f"{now.month}월 {now.day}일 "
        f"{now.hour}시 {now.minute}분 {now.second}초\n"
    ).encode("utf-8")

    with lock:
        for c in rooms.get(room, []):
            try:
                c.sendall(data)
            except:
                pass


def bad_words(msg):
    for word in bad_words_list:
        if word in msg:
            msg = msg.replace(word, len(word) * "*")
    return msg


def emotion(msg):
    for key in emoticon:
        if f"/e{key}" in msg:
            msg = msg.replace(f"/e{key}", emoticon[key])
    return msg


def kick_conn(target_conn, reason="[관리자] 강제퇴장되었습니다."):
    send_to(target_conn, reason)
    try:
        target_conn.close()
    except:
        pass
    with lock:
        users.pop(target_conn, None)
        for r in rooms.values():
            if target_conn in r:
                r.remove(target_conn)


def handle_client(conn, addr):
    global count, vte, count1, count2, bad_words_list, user_db
    user_db[conn] = {"badword_count": 0, "mute_time": datetime.now(), "last_chat_time": datetime.now(), "chat_count": 0}
    conn.settimeout(None)
    with pool:
        print(f"[접속] {addr}")

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
            users[conn] = {"addr": addr, "name": nickname, "role": "USER", "color": my_color, "room": None}

        broadcast_all(f"[입장] {nickname} 님이 입장했습니다.")
        send_to(conn,
                "명령: 나가기: /quit 접속자 확인: /who 귓속말: /w 닉네임 메시지 관리자 승격: /admin 비번 색 변경: /color (red,blue,white,yellow) "
                "투표시작: vote_start 투표 현황: vote_state 투표: vote 강화게임: /upgrade 이모티콘: /e이모티콘(1,2,3,4) ")
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
                room = info["room"]

                if msg == "/quit":
                    break

                if msg.startswith("/room list"):
                    with lock:
                        if not rooms:
                            send_to(conn, "[방 목록] 없음")
                        else:
                            for room_name, members in rooms.items():
                                send_to(conn, f"{room_name} ({len(members)}명)")
                    continue

                # 방 생성
                if msg.startswith("/room create "):
                    room_name = msg.split(" ", 2)[2]
                    with lock:
                        rooms.setdefault(room_name, [])
                    send_to(conn, f"[시스템] 방 '{room_name}' 생성 완료")
                    continue

                # 방 참가
                if msg.startswith("/room join "):
                    room_name = msg.split(" ", 2)[2]
                    with lock:
                        if room_name not in rooms:
                            send_to(conn, "[오류] 방이 없습니다")
                            continue
                        if room:
                            rooms[room].remove(conn)
                        rooms[room_name].append(conn)
                        info["room"] = room_name
                    broadcast_room(room_name, f"[입장] {me}")
                    continue

                # 방 나가기
                if msg.startswith("/room leave"):
                    if room:
                        with lock:
                            rooms[room].remove(conn)
                            info["room"] = None
                        broadcast_room(room, f"[퇴장] {me}")
                        # [수정 2] room_name 변수가 없으므로 room으로 변경
                        send_to(conn, f"{room}방을 나갔습니다.")
                    continue

                if msg == "/who":
                    if not room:
                        send_to(conn, "[안내] 방에 들어가세요")
                        continue
                    with lock:
                        names = ", ".join(users[c]["name"] for c in rooms[room])
                    send_to(conn, f"[방 인원] {names}")
                    continue

                if msg.startswith("/w "):
                    try:
                        _, target_name, text = msg.split(" ", 2)
                        target_conn = None
                        with lock:
                            for c, i in users.items():
                                if i["name"] == target_name:
                                    target_conn = c
                                    break
                        if target_conn:
                            send_to(target_conn, f"[귓속말] {me}: {text}")
                            send_to(conn, f"[귓속말] {me}: {text}")
                        else:
                            send_to(conn, "[오류] 대상 없음")
                    except ValueError:
                        send_to(conn, "[오류] /w 닉네임 메시지 형식을 지켜주세요.")
                    continue

                if msg.startswith("/admin "):
                    try:
                        pw = msg.split(" ", 1)[1]
                        if pw == ADMIN_PASSWORD:
                            with lock:
                                users[conn]["role"] = "ADMIN"
                            send_to(conn, "[관리자] 관리자 권한이 부여되었습니다.")
                            send_to(conn, "명령 공지: /notice 메세지, 강제퇴장: /kick 닉네임")
                            broadcast_room(room, f"[시스템] {me} 님이 관리자가 되었습니다.")
                        else:
                            send_to(conn, "[오류] 관리자 비밀번호가 틀렸습니다.")
                    except IndexError:
                        pass
                    continue

                if msg.startswith("/notice "):
                    if role != "ADMIN":
                        send_to(conn, "[오류] 관리자만 공지를 보낼 수 있습니다.")
                        continue
                    try:
                        notice = msg.split(" ", 1)[1]
                        broadcast_room(room, f"[공지] {notice}")
                    except IndexError:
                        pass
                    continue

                if msg.startswith("/color "):
                    par = msg.split(" ", 2)
                    colors = {"red": "\033[91m", "blue": "\033[94m", "yellow": "\033[93m", "white": "\033[0m"}
                    if len(par) > 1:
                        color = par[1].lower()
                        if color in colors:
                            users[conn]["color"] = colors[color]
                            send_to(conn, f"{color}로 변경되었습니다.")
                        else:
                            send_to(conn, "잘못된 색상입니다.")
                    continue

                if msg.startswith("/upgrade"):
                    a = random.randrange(1, 100)
                    if a < 90:
                        count += 1
                        broadcast_room(room, f"""강화성공 
      _________________
     |                 |
     |                 |================================----------
     |       {count}강           |
     |                 |================================----------
     |_________________|
""")

                    else:
                        count = 0
                        broadcast_room(room, r"""
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
                    votes.clear()
                    count1, count2 = 0, 0
                    vte = msg.split(" ", 1)[1]
                    broadcast_room(room, f'[투표]{vte}')
                    continue

                if msg.startswith("/vote "):
                    try:
                        vt = msg.split(" ", 1)[1]
                        if users[conn]["name"] in votes:
                            send_to(conn, "이미투표를하셨습니다.")
                            continue
                        else:
                            if vt == "1":
                                count1 += 1
                                votes.append(users[conn]["name"])
                                send_to(conn, "1번을 투표하셨습니다.")
                            elif vt == "2":
                                count2 += 1
                                votes.append(users[conn]["name"])
                                send_to(conn, "2번을 투표하셨습니다.")
                            else:
                                send_to(conn, "투표번호가 아닙니다.")
                            continue
                    except IndexError:
                        pass
                    continue

                if msg.startswith("/vote_state"):
                    broadcast_room(room, f"""       {vte} 투표 
            1번 투표수 : {count1} 2번 투표수 : {count2}
""")
                    continue

                if msg.startswith("/kick "):
                    if role != "ADMIN":
                        send_to(conn, "[오류] 관리자만 강제퇴장할 수 있습니다.")
                        continue

                    try:
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
                        broadcast_room(room, f"[시스템] {target_name} 님이 강제퇴장되었습니다.")
                    except IndexError:
                        pass
                    continue

                if not room:
                    send_to(conn, "[안내] 방에 먼저 입장하세요")
                    continue

                # [수정 3] f-string 문법 안전하게 수정 (따옴표 충돌 방지)
                broadcast_room(room, f'{info["color"]}{me}: {msg}')


        except Exception as e:
            print(f"[오류] {addr} 처리 중 예외: {e}")
        finally:
            # 1. 방/유저 정보부터 조용히 삭제 (메시지 전송보다 먼저!)
            with lock:
                info = users.pop(conn, None)
                user_db.pop(conn, None)

                if info:
                    r_name = info.get("room")
                    nickname = info.get("name", "알 수 없음")

                    # 방 목록에서 내 소켓 제거
                    if r_name and r_name in rooms:
                        if conn in rooms[r_name]:
                            rooms[r_name].remove(conn)

                        # 방 사람들에게 알림
                        # 기존 코드에서는 여기서 Deadlock이 발생했습니다.
                        # (finally 블록의 lock 안에서 broadcast_room의 lock을 다시 호출)
                        # RLock을 사용하면 이 문제가 해결됩니다.
                        try:
                            broadcast_room(r_name, f"[퇴장] {nickname} 님이 나갔습니다.")
                        except:
                            pass

            # 2. 소켓 자원 반환
            try:
                conn.close()
            except:
                pass

            print(f"[종료] {addr} - 자원 정리 완료")


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