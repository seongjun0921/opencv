import pymysql
from pymysql.constants import CLIENT
import tkinter as tk
from sqlalchemy.orm import declarative_base
# con, cur = None, None
# data1, data2, data3, data4 = "", "", "", ""
# row = None
#
# conn = pymysql.connect(host = '127.0.0.1',  user = 'root', password = '0000', db = 'soloDB', charset='utf8')
#
# cur = conn.cursor()
#
#
# cur.execute("SELECT * FROM userTable")
# print("사용자 ID   사용자이름   이메일     출생연도")
# print("----------------------------------------")
#
# while(True):
#     row = cur.fetchone()
#     if row == None:
#         break
#     data1 = row[0]
#     data2 = row[1]
#     data3 = row[2]
#     data4 = row[3]
#     print("%5s  %15s    %20s    %d" % (data1, data2, data3, data4))
# conn.close()

# df_config = {
#     'host':'127.0.0.1',
#     'user':'root',
#     'password':'0000',
#     'charset':'utf8',
#     'client_flag': CLIENT.MULTI_STATEMENTS
# }
#
# DB_NAME = 'system_db'
#
# def init_database():
#     conn = pymysql.connect(**df_config)
#     cur=conn.cursor()
#     cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
#     cur.execute(f"CREATE DATABASE {DB_NAME}")
#     cur.execute(f"USE {DB_NAME}")
#
#     cur.execute("""
#     CREATE TABLE users (
#     userid VARCHAR(20) primary key,
#     userpw varchar(20) not null,
#     username varchar(20),
#     role varchar(10))
#     """)
#
#     sql = "insert into users values (%s,%s,%s,%s)"
#     data = [
#         ('admin', 'p@ssword_master', '시스템관리자', 'ADMIN'),
#         ('user01', '1234', '일반사용자01', 'USER')
#     ]
#     cur.executemany(sql, data)
#     conn.commit()
#     conn.close()
#     print("db init 초기화 작업, 계정생성 작업 완료")
#
# def login(u_id, u_pw):
#     conn = pymysql.connect(**df_config, db = DB_NAME)
#     cur=conn.cursor()
#     sql = f"SELECT username, role from users where userid='{u_id}' and userpw = '{u_pw}'"
#     print(f"실행한문장:{sql}")
#     cur.execute(sql)
#     user_info = cur.fetchone()
#     conn.close()
#     if user_info:
#         print(f"로그인 성공{user_info[0]}{user_info[1]}")
#     else:
#         print("로그인 실패")
#
# def safe_login(u_id, u_pw):
#     conn = pymysql.connect(**df_config, db = DB_NAME)
#     cur = conn.cursor()
#     sql = "SELECT username, role From users where userid = %s and userpw = %s"
#     print(f"실행한문장(safe):{sql}")
#     cur.execute(sql, (u_id, u_pw))
#     user_info = cur.fetchone()
#     conn.close()
#     if user_info:
#         print(f"로그인 성공{user_info[0]}{user_info[1]}")
#     else:
#         print("로그인 실패")
#
#
#
# if __name__ == "__main__":
#     init_database()
#     login('user01', '1234')
#     login('admin', 'p@ssword_master')
#     login('xxxx', '1234')
#
#     A_ID ='admin'
#     A_PW = "'or '1' = '1"
#     login(A_ID, A_PW)
#     safe_login(A_ID, A_PW) #sql구성에서 f-string 방시긍로 매개변수 넣기 x 인젝션 발생
#     #sql 구성에서는 매개변수 입력 받는 칸 %s
#     #execute함쉐서 sql문과 사용자입력값 따로 전달하는 방식으로 인젝션 방지
#
#     # B_ID = 'admin'
#     # B_PW ="'; DROP TABLE users; -- "
#     # login(B_ID, B_PW)
#
#     C_ID = 'xxxx'
#     C_PW = "' UNION SELECT userid, userpw FROM users -- "
#     login(C_ID, C_PW)
#
#
# import hashlib
# def encode_pw(password):
#     return hashlib.sha256(password.encode()).hexdigest()
#     #입력받은 문자열 password를 encode를 통해 바이트로 바꾸고 sha256방식 섞어서 16진수로 hexdigest 변환
#
# db_id = 'admin'
# db_pw = encode_pw('p@ssword123')
# print(f"db에 저장되는 비번 {db_pw}")
# input_pw = "p@ssword123"
# hased_input = encode_pw(input_pw)
# print(f"db에 사용자 입력 비번 암호화 결과 {hased_input}")
#
# if hased_input == db_pw:
#     print("값 일치(로그인 성공 경우)")



from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, declarative_base
import hashlib

# DB 연결
engine = create_engine("mysql+pymysql://root:0000@localhost:3306/system_db")
Base = declarative_base()

# ORM 테이블
class User(Base):
    __tablename__ = 'user'
    userid = Column(String(20), primary_key=True)
    userpw = Column(String(64), nullable=False)
    username = Column(String(20))

# 🔥 테이블 생성 (없으면 자동 생성)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# 비밀번호 해시
def encode_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 회원가입
def orm_signup(u_id, u_pw, u_name):
    hashed_pw = encode_pw(u_pw)
    new_user = User(userid=u_id, userpw=hashed_pw, username=u_name)
    try:
        session.add(new_user)
        session.commit()
        print(f"{u_name} 회원가입 완료")
    except Exception as e:
        session.rollback()
        print("회원가입 실패:", e)

# 로그인
def orm_login(u_id, u_pw):
    hashed_pw = encode_pw(u_pw)
    user = session.query(User).filter(
        User.userid == u_id,
        User.userpw == hashed_pw
    ).first()

    if user:
        print(f"로그인 성공: {user.username}")
        return True
    else:
        print("로그인 실패")
        return False

# 비밀번호 변경
def orm_update_pw(u_id, old_pw, new_pw):
    hashed_old_pw = encode_pw(old_pw)
    hashed_new_pw = encode_pw(new_pw)

    user = session.query(User).filter(
        User.userid == u_id,
        User.userpw == hashed_old_pw
    ).first()

    if user:
        user.userpw = hashed_new_pw
        session.commit()
        print("비밀번호 변경 성공")
    else:
        print("기존 비밀번호가 틀렸습니다")

# 테스트
if __name__ == "__main__":
    orm_signup("test", "test123", "testname")
    orm_login("test", "test123")
    orm_update_pw("test", "test123", "test123")
    orm_login("test", "test123")



df_config = {
    'host':'127.0.0.1',
    'user':'root',
    'password':'0000',
    'charset':'utf8',
    'client_flag': CLIENT.MULTI_STATEMENTS
}

DB_NAME = 'system_db'


def update_db_to_sha256():
    conn=pymysql.connect(**df_config, )
    cur=conn.cursor()
    cur.execute("SELECT userid, userpw FROM user")
    users = cur.fetchall()
    for user_id, raw_pw in users:
        if len(raw_pw) == 64:
            continue
        hashed_pw = encode_pw(raw_pw)
        update_sql="UPDATE user SET userpw = %s WHERE userid = %s"
        cur.execute(update_sql, (hashed_pw, user_id))

    conn.commit()
    conn.close()
#
# sqlalchemy
# hash
# orm
# gui tkinter
#orm세선을 통한 데이터 조회: query(User).filter(조건).first()
#orm세선을 통한 데이터 추가: add() 후 commit()
#orm세선을 통한 데이터 삭제: delete() 후 commit()
# 사용자 비밀번호가 암호화되어 db에 저장되는 로그인 회원가입 비밀번호 변경 로그인창ui

def login():
    user_id = entry_id.get()
    user_pw = entry_pw.get()
    orm_login(user_id,user_pw)

def open_signup_window():
    signup_win = tk.Toplevel(window)
    signup_win.title("회원가입")
    signup_win.geometry("300x200")
    signup_win.resizable(False, False)

    # 이름
    tk.Label(signup_win, text="이름:").place(x=20, y=20)
    entry_name = tk.Entry(signup_win)
    entry_name.place(x=100, y=20)

    # 아이디
    tk.Label(signup_win, text="아이디:").place(x=20, y=60)
    entry_s_id = tk.Entry(signup_win)
    entry_s_id.place(x=100, y=60)

    # 비밀번호
    tk.Label(signup_win, text="비밀번호:").place(x=20, y=100)
    entry_s_pw = tk.Entry(signup_win, show="*")
    entry_s_pw.place(x=100, y=100)

    # 메시지 레이블
    label_s_log = tk.Label(signup_win, text="")
    label_s_log.place(x=20, y=140)

    # 회원가입 버튼
    def signup():
        sign_user_name = entry_name.get()
        sign_user_id = entry_s_id.get()
        sign_user_pw = entry_s_pw.get()
        if sign_user_name and sign_user_id and sign_user_pw:
            orm_signup(sign_user_id, sign_user_pw, sign_user_name)
            label_s_log.config(text="회원가입에 성공하였습니다.")
        else:
            label_s_log.config(text="모든 정보를 입력해주세요")

    sign_but2 = tk.Button(signup_win, text="회원가입", command=signup)
    sign_but2.place(x=100, y=170)


def sign():
    user_id = entry_id.get()
    user_pw = entry_pw.get()
    # #user_name = entry_name.get()
    # if user_id and user_pw and user_name:
    #     orm_signup(user_id, user_pw, user_name)
    # else:
    #     label_log.config(text="모든 정보를 입력해주세요")


window = tk.Tk()
window.title("GUI")
window.geometry("600x400")
window.resizable(False, False)


label_log = tk.Label(window, text = "")
label_log.place(x = 0, y = 150)


#아이디 창
label_id = tk.Label(window, text = "아이디: ")
entry_id = tk.Entry(window)

#비번 창
label_pw = tk.Label(window, text = "비밀번호:")
entry_pw = tk.Entry(window)

label_id.place(x = 0, y = 60)
label_pw.place(x = 0, y = 90)
entry_id.place(x = 60,y =  60)
entry_pw.place(x = 60,y =  90)

log_but = tk.Button(window, text = "로그인", command = login).place(x = 60, y = 120)
sign_but = tk.Button(window, text = "회원가입", command = open_signup_window).place(x = 120, y = 120)
window.mainloop()