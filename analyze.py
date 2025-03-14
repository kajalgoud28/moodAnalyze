from flask import Flask, request, jsonify, render_template, url_for
import os
from deepface import DeepFace
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["mood_analyzer"]
mood_collection = db["moods"]

# Emoji Map
EMOJI_MAP = {
    "happy": "😊", "sad": "😢", "angry": "😠",
    "neutral": "😐", "surprise": "😲", "fear": "😨", "disgust": "🤬"
}

# Mood-Based Song Recommendations (Title and URL)
SONG_RECOMMENDATIONS = {
    "happy": [
        {"name": "Happy - Pharrell Williams", "url": "https://youtu.be/ZbZSe6N_BXs"},
        {"name": "Can't Stop the Feeling - Justin Timberlake", "url": "https://youtu.be/ru0K8uYEZWw"}
    ],
    "sad": [
        {"name": "Someone Like You - Adele", "url": "https://youtu.be/hLQl3WQQoQ0"},
        {"name": "Let Her Go - Passenger", "url": "https://youtu.be/RBumgq5yVrA"}
    ],
    "angry": [
        {"name": "Break Stuff - Limp Bizkit", "url": "https://youtu.be/ZpUYjpKg9KY"},
        {"name": "Stronger - Kanye West", "url": "https://youtu.be/PsO6ZnUZI0g"}
    ],
    "neutral": [
        {"name": "Photograph - Ed Sheeran", "url": "https://youtu.be/nSDgHBxUbVQ"},
        {"name": "Counting Stars - OneRepublic", "url": "https://youtu.be/hT_nvWreIhg"}
    ],
    "surprise": [
        {"name": "Uptown Funk - Mark Ronson ft. Bruno Mars", "url": "https://youtu.be/OPf0YbXqDm0"},
        {"name": "Take On Me - a-ha", "url": "https://youtu.be/djV11Xbc914"}
    ],
    "fear": [
        {"name": "Thriller - Michael Jackson", "url": "https://youtu.be/sOnqjkJTMaA"},
        {"name": "Disturbia - Rihanna", "url": "https://youtu.be/E1mU6h4Xdxc"}
    ],
    "disgust": [
        {"name": "Boulevard of Broken Dreams - Green Day", "url": "https://youtu.be/Soa3gO7tL-c"},
        {"name": "Creep - Radiohead", "url": "https://youtu.be/XFkzRNyygfk"}
    ]
}

@app.route("/")
def index():
    return render_template("analyze.html")

@app.route("/analyze", methods=["POST"])
def analyze_mood():
    """Handle image upload and mood analysis."""
    if "image" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    try:
        analysis = DeepFace.analyze(file_path, actions=["emotion"], detector_backend="opencv", enforce_detection=False)
        emotions = analysis[0]["emotion"]
        dominant_emotion = max(emotions, key=emotions.get)
        confidence = round(emotions[dominant_emotion], 2)

        # Save to MongoDB
        mood_data = {
            "mood": dominant_emotion.capitalize(),
            "confidence": confidence,
            "image_url": file_path
        }
        mood_collection.insert_one(mood_data)

        return jsonify({
            "mood": dominant_emotion.capitalize(),
            "emoji": EMOJI_MAP.get(dominant_emotion, "😐"),
            "songs": SONG_RECOMMENDATIONS.get(dominant_emotion, []),
            "image_url": url_for("static", filename=f"uploads/{filename}"),
            "confidence": confidence
        })
    except Exception as e:
        return jsonify({"error": f"Mood detection failed: {e}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5007)
