import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy import create_engine, MetaData, Table, column, String, Column, DateTime
from sqlalchemy.orm import sessionmaker
import hashlib
from sqlalchemy import create_engine, MetaData, Table, column, String, Column
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(String(20), primary_key=True)
    userpw = Column(String(64), nullable=False)
    username = Column(String(20), nullable=False)
    role = Column(String(20))


def encode_pw(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


class Login(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        id_lb = ttk.Label(self, text="ID")
        self.id_ent = tk.Entry(self)
        pw_lb = ttk.Label(self, text="Password")
        self.pw_ent = PasswordField(self, tk.StringVar())
        self.msg_lb = ttk.Label(self, text="")
        self.login_btn = ttk.Button(self, text="Login")
        self.login_btn.bind("<Button>", lambda e: self.check_filled())
        self.sign_up_btn = ttk.Button(self, text="Sign Up")

        id_lb.pack()
        self.id_ent.pack()
        pw_lb.pack()
        self.pw_ent.pack()
        self.msg_lb.pack(expand=True, fill="x")
        self.login_btn.pack()
        self.sign_up_btn.pack()


    def check_filled(self):
        if self.id_ent.get() == "" or self.pw_ent.get() == "":
            self.set_message("Please fill all fields.")

    def get_credentials(self):
        return self.id_ent.get(), self.pw_ent.get()

    def set_message(self, msg):
        self.msg_lb.config(text=msg)

    def clear(self):
        self.id_ent.delete(0, tk.END)
        self.pw_ent.delete(0, tk.END)
        self.msg_lb.config(text="")

class MemberPage(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.name_lb = ttk.Label(self, text="ID")
        self.reset_password_btn = ttk.Button(self, text="Reset Password")
        self.logout_btn = ttk.Button(self, text="Logout")

        self.name_lb.pack(expand=True, fill="x")
        self.reset_password_btn.pack()
        self.logout_btn.pack()

    def set_info(self, info):
        self.name_lb.config(text=f"Hello {info["username"]}.")


class PasswordField(ttk.Frame):
    def __init__(self, master, textvariable, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.is_showing = False

        self.ent = ttk.Entry(self, show="*", textvariable=textvariable)
        self.ent.grid(row=0, column=0, sticky="ew")
        self.show_btn = ttk.Button(self, text="show")
        self.show_btn.grid(row=0, column=1)

        self.columnconfigure(0, weight=1)
        self.show_btn.bind("<Button>", lambda e: self.show())

    def get(self):
        return self.ent.get()

    def delete(self, *args, **kwargs):
        return self.ent.delete(*args, **kwargs)

    def show(self):
        self.is_showing = not self.is_showing
        if self.is_showing:
            self.ent.config(show = "")
        else:
            self.ent.config(show="*")

class SignUpPage(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        pw = tk.StringVar()
        repeat = tk.StringVar()
        pw.trace_add(mode="write", callback=lambda e1, e2, e3: self.pw_changed())
        repeat.trace_add(mode="write", callback=lambda e1, e2, e3: self.pw_changed())

        id_lb = ttk.Label(self, text="ID")
        self.id_ent = tk.Entry(self)
        name_lb = ttk.Label(self, text="Name")
        self.name_ent = tk.Entry(self)
        pw_lb = ttk.Label(self, text="Password")
        self.pw_ent = PasswordField(self, pw)
        repeat_lb = ttk.Label(self, text="Repeat password")
        self.repeat_ent = PasswordField(self, repeat)

        self.msg_lb = ttk.Label(self)
        self.submit_btn = ttk.Button(self, text="Sign Up")


        id_lb.pack()
        self.id_ent.pack()
        name_lb.pack()
        self.name_ent.pack()
        pw_lb.pack()
        self.pw_ent.pack()
        repeat_lb.pack()
        self.repeat_ent.pack()
        self.msg_lb.pack()
        self.submit_btn.pack()

        self.pw_ent.bind("<<")

    def is_pw_same(self) -> bool:
        pw_a, pw_b = self.pw_ent.get(), self.repeat_ent.get()
        return pw_a == pw_b

    def get(self):
        return self.id_ent.get(), self.name_ent.get(), self.pw_ent.get()

    def pw_changed(self):
        if not self.is_pw_same():
            self.msg_lb.config(text="Passwords do not match.")
        else:
            self.msg_lb.config(text="")

    def set_message(self, msg):
        self.msg_lb.config(text=msg)

class ResetPassword(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        lb1 = ttk.Label(self, text="Current password")
        self.current_ent = PasswordField(self, tk.StringVar())
        lb2 = ttk.Label(self, text="New password")
        self.new_ent = PasswordField(self, tk.StringVar())
        lb3 = ttk.Label(self, text="Repeat new password")
        self.repeat_ent = PasswordField(self, tk.StringVar())
        self.reset_btn = ttk.Button(self, text="reset")
        self.reset_btn.pack()

        lb1.pack()
        self.current_ent.pack()
        lb2.pack()
        self.new_ent.pack()
        lb3.pack()
        self.repeat_ent.pack()

    def get(self):
        return self.current_ent.get(), self.new_ent.get()

    def is_pw_same(self) -> bool:
        pw_a, pw_b = self.new_ent.get(), self.repeat_ent.get()
        return pw_a == pw_b


class UserManager:
    def __init__(self, url):
        engine = create_engine(url, echo=False)
        Base.metadata.create_all(engine)    #base user구성대로
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def login(self, user_id, user_pw) -> tuple[dict, str]:
        user = self.session.query(User).where(User.id == user_id, User.userpw == user_pw).first()
        if user:
            return {
                "user_id": user.id,
                "username": user.username
            }, ""
        else:
            return {}, "There's no matched user."

    def sign_up(self, user_id, user_pw, user_name, user_role = None) -> tuple[dict, str]:
        user = self.session.query(User).where(User.id == user_id).first()
        if user:
            return {}, "That user ID is already exists."
        else:
            new_user = User(id=user_id, userpw=user_pw, username=user_name, role=user_role)
            try:
                self.session.add(new_user)
                self.session.commit()
                return {
                    "username": new_user.username
                }, ""
            except:
                self.session.rollback()
                return {}, "DB update failed."

    def reset_password(self, user_id, user_pw, new_password) -> tuple[bool, str]:
        user = self.session.query(User).where(User.id == user_id, User.userpw == user_pw).first()
        if user:
            try:
                user.userpw = new_password
                self.session.commit()
                return True, ""
            except:
                self.session.rollback()
                return False, "DB update failed."
        else:
            return False, "There's no matched user."


class MainWindow(tk.Tk):
    def __init__(self, db_manager, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("Login")
        self.geometry("400x500")
        self.db = db_manager

        self.login_page = Login(self)
        self.login_page.pack()

        self.member_page = MemberPage(self)
        self.sign_up_page = SignUpPage(self)
        self.reset_password_page = ResetPassword(self)
        self.current_member = None

        self.login_page.login_btn.bind("<Button>", lambda e: self.try_login())
        self.login_page.sign_up_btn.bind("<Button>", lambda e: self.show_sign_up())
        self.member_page.logout_btn.bind("<Button>", lambda e: self.logout())
        self.member_page.reset_password_btn.bind("<Button>", lambda e: self.show_reset_password())
        self.sign_up_page.submit_btn.bind("<Button>", lambda e: self.try_sign_up())
        self.reset_password_page.reset_btn.bind("<Button>", lambda e: self.try_reset_password())

    def show_reset_password(self):
        self.member_page.pack_forget()
        self.reset_password_page.pack()

    def try_reset_password(self):
        if self.reset_password_page.is_pw_same():
            oldpw, newpw = self.reset_password_page.get()
            hashed_old = encode_pw(oldpw)
            hashed_new = encode_pw(newpw)
            succeed, err = self.db.reset_password(self.current_member["user_id"], hashed_old, hashed_new)
            if succeed:
                self.reset_password_page.pack_forget()
                self.member_page.pack()
            else:
                messagebox.showwarning("error", err)



    def try_login(self):
        user_id, user_pw = self.login_page.get_credentials()
        hashed_pw = encode_pw(user_pw)

        info, err = self.db.login(user_id, hashed_pw)
        if err:
            self.login_page.set_message(err)
        else:
            self.login_page.clear()
            self.login_page.pack_forget()
            self.member_page.set_info(info)
            self.member_page.pack()
            self.current_member = info

    def try_sign_up(self):
        if not self.sign_up_page.is_pw_same():
            self.sign_up_page.set_message("Password do not match.")
            return

        user_id, user_name, user_pw = self.sign_up_page.get()
        hashed_pw = encode_pw(user_pw)

        info, err = self.db.sign_up(user_id, hashed_pw, user_name)
        if err:
            self.sign_up_page.set_message(err)
        else:
            self.sign_up_page.pack_forget()
            self.login_page.pack()

    def show_sign_up(self):
        self.login_page.clear()
        self.login_page.pack_forget()
        self.sign_up_page.pack()

    def logout(self):
        self.member_page.pack_forget()
        self.login_page.pack()
        self.current_member = None

    def run(self):
        self.mainloop()


if __name__ == "__main__":
    db_session = UserManager('mysql+pymysql://root:0000@localhost:3306/system_db')
    mw = MainWindow(db_session)
    mw.run()