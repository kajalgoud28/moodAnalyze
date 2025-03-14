from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from collections import defaultdict
from datetime import datetime
import threading
import json
import os
import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QListWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QUrl, pyqtSlot, QObject

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["mental_health_db"]
users_collection = db["users"]
login_history_collection = db["login_history"]
sleep_collection = db["sleep_detection"]
mood_collection = db["emotion_logs"]
feedback_collection = client["emotion_database"]["feedbacks"]  # Added Feedback Collection

# Store current user session
current_user = None

class WebEngineBridge(QObject):
    @pyqtSlot(str, str, str, result=str)
    def register_user(self, username, email, password):
        if users_collection.find_one({"email": email}):
            return "Email already registered!"
        users_collection.insert_one({"username": username, "email": email, "password": password})
        return "success"

    @pyqtSlot(str, str, result=str)
    def login_user(self, email, password):
        global current_user
        user = users_collection.find_one({"email": email, "password": password})
        if user:
            current_user = email
            login_history_collection.insert_one({
                "email": email,
                "username": user["username"],
                "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            return "success"
        return "Invalid email or password!"

    @pyqtSlot(result=str)
    def isUserLoggedIn(self):
        return "true" if current_user else "false"

    @pyqtSlot(result=str)
    def logout_user(self):
        global current_user
        current_user = None
        return "Logged out successfully!"

    @pyqtSlot(str, result=str)
    def submit_feedback(self, feedback_text):
        global current_user
        if not current_user:
            return "❌ You must be logged in to submit feedback!"
        
        feedback_data = {
            "email": current_user,
            "feedback": feedback_text,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        feedback_collection.insert_one(feedback_data)
        return "✅ Thank you for your feedback!"

    @pyqtSlot(result=str)
    def get_mood_history(self):
        return json.dumps(fetch_mood_history())

class MoodAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mood Analyzer")
        self.setGeometry(100, 100, 900, 600)
        self.templates_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../templates"))
        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout()
        self.sidebar = QListWidget()
        self.sidebar.addItems([
            "🏠 Home", "📝 Feedback","Tips ",  "🔑 Login", 
            "😃 Mood Analysis", "😴 Sleep Detection", 
            "📊 Mood History", "📊 Sleep History","Analyze mood ", "❌ Exit"
        ])
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: #2C3E50;
                color: white;
                font-size: 16px;
                border-right: 2px solid #1A252F;
            }
            QListWidget::item:selected {
                background-color: #18BC9C;
                font-weight: bold;
            }
            QListWidget::item {
                padding: 10px;
            }
        """)
        self.sidebar.clicked.connect(self.handle_menu_click)
        self.web_view = QWebEngineView()
        self.channel = QWebChannel()
        self.bridge = WebEngineBridge()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        main_widget = QWidget()
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.web_view)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.load_page("login.html")

    def handle_menu_click(self, index):
        menu_item = self.sidebar.item(index.row()).text()
        pages = {
            "🏠 Home": "home.html",
            "📝 Feedback": "feedback.html",
            "Tips ": "tips.html",
            "🔑 Login": "login.html",
            "😃 Mood Analysis": "mood_analysis.html",
            "😴 Sleep Detection": "sleep_detection.html",
            "📊 Mood History": "mood_history.html",
            "📊 Sleep History": "sleep_history.html",
            "Analyze mood ": "analyze.html",
            "❌ Exit": None
        }
        if menu_item == "🔓 Logout":
            self.bridge.logout_user()
            self.load_page("login.html")
        elif menu_item == "❌ Exit":
            self.close()
        elif menu_item in pages:
            self.load_page(pages[menu_item])

    def load_page(self, filename):
        file_path = os.path.abspath(os.path.join(self.templates_dir, filename))
        if not os.path.exists(file_path):
            self.web_view.setHtml("<h2 style='color:red;'>Error: Page not found!</h2>")
            return
        self.web_view.setUrl(QUrl.fromLocalFile(file_path))

flask_app = Flask(__name__)
CORS(flask_app)

def fetch_mood_history():
    collection = db["emotion_logs"]
    data = list(collection.find({}, {"_id": 0, "timestamp": 1, "emotion": 1}))
    mood_data = defaultdict(lambda: {"happy": 0, "sad": 0, "neutral": 0, "angry": 0, "fear": 0})
    for entry in data:
        timestamp = entry.get("timestamp")
        emotion = entry.get("emotion", "").lower()
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", ""))
        date = timestamp.strftime("%Y-%m-%d")
        if emotion in mood_data[date]:
            mood_data[date][emotion] += 1
    return [{"date": date, "moods": moods} for date, moods in sorted(mood_data.items())]

@flask_app.route('/get_mood_history')
def get_mood_history():
    return jsonify(fetch_mood_history())

@flask_app.route('/get_feedbacks')
def get_feedbacks():
    feedbacks = list(feedback_collection.find({}, {"_id": 0}))
    return jsonify(feedbacks)

def run_flask():
    
    flask_app.run( port=5008, debug=True)


if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    mood_process = subprocess.Popen(["python", "main.py"])
    sleep_process = subprocess.Popen(["python", "sleep_his.py"])
    analyze_process = subprocess.Popen(["python", "analyze.py"])
    sleep_process = subprocess.Popen(["python", "sleep.py"])
    moodhis_process = subprocess.Popen(["python", "mood.py"])
    sleep_process = subprocess.Popen(["python", "sleep_his.py"])
    qt_app = QApplication(sys.argv)
    window = MoodAnalyzerApp()
    window.show()
    sys.exit(qt_app.exec_())
