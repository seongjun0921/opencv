import socket
import threading
import sys

#SERVER_IP는 자기 컴퓨터에 있는  IPv4 주소 (cmd- ipconfig) 확인
SERVER_IP = "192.168.0.215"
PORT = 5001

my_nick = ""


def recv_loop(sock: socket.socket):
    global my_nick
    try:
        while True:
            data = sock.recv(4096)
            if not data:
                print("\n[서버 연결 종료] 서버가 끊겼거나 종료됨.")
                break

            text = data.decode("utf-8", errors="ignore")

            if my_nick and (f"@{my_nick}" in text):
                print("★ [내가 언급됨!]\n" + text, end="")
            else:
                print(text, end="")

    except Exception:
        print("\n[수신 스레드 종료] 연결 문제 발생.")
    finally:
        try:
            sock.close()
        except:
            pass
        sys.exit(0)


def main():
    global my_nick
    nickname = input("닉네임 입력: ").strip()
    if not nickname:
        nickname = "익명"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((SERVER_IP, PORT))
    except Exception as e:
        print(f" 서버 접속 실패: {e}")
        print(" 체크: 서버 실행 중? IP 맞음? 같은 와이파이? 방화벽 포트 열림?")
        return

    # 닉네임 전송
    try:
        q = sock.recv(1024).decode("utf-8", errors="ignore")
        if "NICK?" in q:
            sock.sendall((nickname + "\n").encode("utf-8"))
    except Exception as e:
        print(f" 닉네임 송신 실패: {e}")
        sock.close()
        return

    my_nick = nickname

    threading.Thread(target=recv_loop, args=(sock,), daemon=True).start()

    print("\n 채팅 시작")
    print(" - 종료: /quit")
    print(" - 귓속말: /w 닉네임 메시지")
    print(" - 강퇴(관리자): /kick 닉네임")
    print(" - 언급: @닉네임\n")

    try:
        while True:
            msg = input()
            if msg.strip() == "":
                continue
            sock.sendall((msg + "\n").encode("utf-8"))
            if msg.strip() == "/quit":
                break
    except KeyboardInterrupt:
        try:
            sock.sendall("/quit\n".encode("utf-8"))
        except:
            pass
    finally:
        try:
            sock.close()
        except:
            pass


if __name__ == "__main__":
    main()