import sys
import re
import os
import ollama
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QTextEdit, QLineEdit, QLabel, QFrame)
from PyQt6.QtCore import (QTimer, QDateTime, Qt, QThread, pyqtSignal, 
                          QPropertyAnimation, pyqtProperty)
from PyQt6.QtGui import QFont, QColor, QPainter, QRadialGradient, QPen
from kokoro_onnx import Kokoro
import sounddevice as sd

# ==========================================
# 1. CORE JARVIS THREAD
# ==========================================
class JarvisThread(QThread):
    response_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        try:
            self.tts = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
            self.tts_ready = True
        except:
            self.tts_ready = False
        self.prompt = ""

    def run(self):
        res = ollama.chat(model="qwen2.5:1.5b", messages=[
            {"role": "system", "content": "You are JARVIS. Reply in 1 short sentence."},
            {"role": "user", "content": self.prompt}
        ])
        reply = res["message"]["content"]
        self.response_signal.emit(reply)
        if self.tts_ready:
            audio, _ = self.tts.create(reply, voice="am_puck", speed=1.4)
            sd.play(audio, 24000)
            sd.wait()

# ==========================================
# 2. ARC REACTOR WIDGET
# ==========================================
class ArcReactorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(250, 250)
        self._pulse_opacity = 200
        self.animation = QPropertyAnimation(self, b"pulse_opacity")
        self.animation.setDuration(1500)
        self.animation.setStartValue(180)
        self.animation.setEndValue(255)
        self.animation.setLoopCount(-1)
        self.animation.start()

    @pyqtProperty(int)
    def pulse_opacity(self): return self._pulse_opacity
    
    @pulse_opacity.setter
    def pulse_opacity(self, value):
        self._pulse_opacity = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() // 2, self.height() // 2
        size = min(cx, cy)
        
        # Draw reactor
        painter.setPen(Qt.PenStyle.NoPen)
        gradient = QRadialGradient(float(cx), float(cy), float(size * 0.8))
        gradient.setColorAt(0, QColor(0, 242, 255))
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(gradient)
        painter.drawEllipse(int(cx-size), int(cy-size), int(size*2), int(size*2))
        
        # Draw ring
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(0, 242, 255), 3))
        painter.drawEllipse(int(cx-(size*0.7)), int(cy-(size*0.7)), int(size*1.4), int(size*1.4))

# ==========================================
# 3. MAIN DASHBOARD
# ==========================================
class JarvisDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background-color: #030507; color: #00f2ff;")
        self.showFullScreen()
        
        central = QWidget()
        layout = QHBoxLayout(central)
        
        self.display = QTextEdit()
        self.display.setReadOnly(True)
        
        self.input = QLineEdit()
        self.input.returnPressed.connect(self.handle_cmd)
        
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel("JARVIS INTERFACE"))
        vbox.addWidget(ArcReactorWidget())
        vbox.addWidget(self.display)
        vbox.addWidget(self.input)
        
        layout.addLayout(vbox)
        self.setCentralWidget(central)
        self.jarvis = JarvisThread()
        self.jarvis.response_signal.connect(lambda t: self.display.append(f"JARVIS: {t}"))

    def handle_cmd(self):
        text = self.input.text()
        if text.lower() == "exit": sys.exit()
        self.display.append(f"YOU: {text}")
        self.jarvis.prompt = text
        self.jarvis.start()
        self.input.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JarvisDashboard()
    sys.exit(app.exec())