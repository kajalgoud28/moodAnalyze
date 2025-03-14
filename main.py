from flask import Flask, jsonify, render_template
from flask_pymongo import PyMongo
from collections import defaultdict
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/emotion_database"
mongo = PyMongo(app)

@app.route('/')
def index():
    return render_template('mood_history.html')

@app.route('/get_mood_history')
def get_mood_history():
    collection = mongo.db.emotion_logs
    data = list(collection.find())  # Fetch all records from MongoDB

    if not data:
        print("❌ No data found in MongoDB!")  # Debugging log
        return jsonify([])  # Return empty response

    print("✅ Data found in MongoDB:", data)  # Debug fetched data

    mood_data = defaultdict(lambda: {"happy": 0, "sad": 0, "neutral": 0, "angry": 0, "fear": 0})

    for entry in data:
        timestamp = entry.get("timestamp")
        emotion = entry.get("emotion", "").lower()  # Ensure lowercase for consistency

        # Handle timestamp format (string or datetime object)
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", ""))  # Convert ISO format
        elif isinstance(timestamp, datetime):
            pass  # Already a datetime object
        else:
            continue  # Skip if timestamp is invalid

        date = timestamp.strftime("%Y-%m-%d")  # Extract only date

        # Only count valid emotions
        if emotion in mood_data[date]:
            mood_data[date][emotion] += 1  # Increment mood count

    response = [{"date": date, "moods": moods} for date, moods in sorted(mood_data.items())]
    print("📊 Processed Mood Data:", response)  # Debugging output

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5005)
