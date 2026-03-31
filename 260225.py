import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import QTimer
import serial
import serial.tools.list_ports
from PyQt5.QtCore import Qt

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 & pyserial App")
        self.ser = None

        self.input = QLineEdit(self)
        self.input.setPlaceholderText("보낼 내용을 입력하세요")
        self.send_btn = QPushButton("전송", self)
        self.result = QLabel("수신: (아직 없음)", self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.input)
        layout.addWidget(self.send_btn)
        layout.addWidget(self.result)
        self.setLayout(layout)

        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if "Arduino" in port.description:
                    self.ser = serial.Serial(port.device, 9600, timeout=0.05)
                    print(f"{port.device}에 연결되었습니다.")
                    break
        except Exception as e:
            self.ser = None
            self.result.setText(f"포트 열기 실패: {e}")

        self.send_btn.clicked.connect(self.send_text)
        self.input.returnPressed.connect(self.send_text)

        self.timer = QTimer(self)
        self.timer.setInterval(30)  # 30ms마다 수신 확인 (가볍고 UI 멈춤 없음)
        self.timer.timeout.connect(self.read_serial)
        self.timer.start()

    def send_text(self):
        if not self.ser or not self.ser.is_open:
            self.result.setText("오류: 시리얼 포트가 열리지 않았습니다.")
            return
        data = self.input.text()
        if data == "":
            return
        try:
            self.ser.write(data.encode())
        except Exception as e:
            self.result.setText(f"전송 오류: {e}")

    def read_serial(self):
        if not self.ser or not self.ser.is_open:
            return
        try:
            n = self.ser.in_waiting
            if n > 0:
                raw = self.ser.read(n)
                text = raw.decode("utf-8")
                self.result.setText(text)
                self.result.setAlignment(Qt.AlignCenter)
                self.result.setText(f"수신: {text}")
        except Exception as e:
            self.result.setText(f"수신 오류: {e}")

    def closeEvent(self, event):
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except:
            pass
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MyWindow()
    w.resize(500, 140)
    w.show()
    sys.exit(app.exec_())
