import cv2
import numpy as np
from deepface import DeepFace
import mediapipe as mp
from flask import Flask, Response, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# Initialize MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["emotion_database"]  # Database name
collection = db["emotion_logs"]  # Collection name

# Initialize OpenCV Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def save_to_mongodb(emotion, confidence):
    """Save detected emotion to MongoDB with timestamp."""
    data = {
        "emotion": emotion,
        "confidence": confidence,
        "timestamp": datetime.utcnow()
    }
    collection.insert_one(data)
    print(f"Saved: {data}")

def analyze_emotion(frame):
    """Detects face and predicts emotion using DeepFace."""
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) == 0:
            return "No face detected", 0.0

        for (x, y, w, h) in faces:
            face_roi = frame[y:y+h, x:x+w]  # Crop the detected face
            rgb_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)

            # Run emotion analysis on the detected face
            result = DeepFace.analyze(rgb_face, actions=['emotion'], enforce_detection=False)

            if isinstance(result, list) and len(result) > 0:
                emotion = result[0].get('dominant_emotion', 'Unknown')
                confidence = result[0]['emotion'].get(emotion, 0.0)

                # Ignore low-confidence predictions
                if confidence < 20:
                    return "Uncertain", 0.0

                # Save detected emotion to MongoDB
                save_to_mongodb(emotion, confidence)

                return emotion, confidence
        return "No face detected", 0.0
    except Exception as e:
        print("Error in emotion detection:", e)
        return "Error", 0.0

def generate_frames():
    cap = cv2.VideoCapture(0)

    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1000)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 700)

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Resize frame
        frame = cv2.resize(frame, (1000, 700))

        # Perform emotion analysis
        emotion, confidence = analyze_emotion(frame)
        text = f'Emotion: {emotion} ({confidence:.2f}%)'

        # Display text on frame
        cv2.putText(frame, text, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 5)

        # Encode frame to stream
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/get-emotion-data", methods=["GET"])
def get_emotion_data():
    """Fetch emotion data from MongoDB for admin dashboard."""
    emotions = collection.find({}, {"_id": 0})  # Exclude MongoDB ID
    emotion_list = list(emotions)
    return jsonify(emotion_list)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5003, debug=True)
