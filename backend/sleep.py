from flask import Flask, Response, render_template
import cv2
import dlib
import time
import datetime
from scipy.spatial import distance
from pymongo import MongoClient
import pygame
import numpy as np

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("localhost", 27017)
db = client["emotion_database"]
collection = db["sleep_detection"]

# Load face detector and landmark predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# Indices for eyes
LEFT_EYE = list(range(42, 48))
RIGHT_EYE = list(range(36, 42))

# Initialize pygame for alarm
pygame.mixer.init()
pygame.mixer.music.load("alarm.wav")  # ✅ Add an alarm sound file

# Eye Aspect Ratio (EAR) calculation
def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def detect_sleepiness():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1000)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 700)
    
    COUNTER = 0
    ALARM_ON = False
    SLEEP_COUNT = 0  # Track how many times sleep is detected

    # EAR Thresholds
    EAR_THRESHOLD = 0.25
    FRAME_CHECK = 15  # Frames needed to confirm sleep

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (1000, 700))  # Ensure frame size consistency

        # Convert to grayscale for faster processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        for face in faces:
            landmarks = predictor(gray, face)
            left_eye = [(landmarks.part(i).x, landmarks.part(i).y) for i in LEFT_EYE]
            right_eye = [(landmarks.part(i).x, landmarks.part(i).y) for i in RIGHT_EYE]

            left_EAR = eye_aspect_ratio(left_eye)
            right_EAR = eye_aspect_ratio(right_eye)
            EAR = (left_EAR + right_EAR) / 2.0  # Average EAR

            # Draw eyes landmarks
            for (x, y) in left_eye + right_eye:
                cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

            if EAR < EAR_THRESHOLD:
                COUNTER += 1
                if COUNTER >= FRAME_CHECK:
                    if not ALARM_ON:
                        ALARM_ON = True
                        pygame.mixer.music.play()
                        SLEEP_COUNT += 1

                        # Save to MongoDB
                        sleep_event = {
                            "timestamp": datetime.datetime.now(),
                            "sleep_count": SLEEP_COUNT,
                            "day": datetime.datetime.now().strftime("%A")
                        }
                        collection.insert_one(sleep_event)

                    cv2.putText(frame, "SLEEPY!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 5)
            else:
                COUNTER = 0
                ALARM_ON = False
                pygame.mixer.music.stop()

            # Display EAR value
            cv2.putText(frame, f"EAR: {EAR:.2f}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 3)

        # Encode and stream video
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()
    cv2.destroyAllWindows()

@app.route('/video_feed')
def video_feed():
    return Response(detect_sleepiness(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('sleep_detection.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5004, debug=True)
