from flask import Flask, render_template, request, jsonify
from PIL import Image
import pytesseract
import requests
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ✅ Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\User 2\Downloads\tesseract.exe"

# ✅ Gemini setup
GEMINI_API_KEY = #"your api key"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ DB init
def initialize_database():
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_filename TEXT,
            prompt TEXT,
            gemini_response TEXT,
            timestamp DATETIME
        )
    """)
    conn.commit()
    conn.close()

initialize_database()

def apply_language(prompt, language):
    return f"Please respond in {language}.\n\n{prompt}"

# ✅ Home redirects to Dashboard
@app.route("/")
def home():
    return render_template("dashboard.html")

# ✅ Dashboard
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ✅ Prompt page
@app.route("/prompt")
def prompt_page():
    return render_template("prompt.html")

# ✅ Upload page
@app.route("/upload")
def upload_page():
    return render_template("upload.html")

# ✅ Visual page
@app.route("/visual")
def visual_page():
    return render_template("visual.html")

# ✅ Planner page
@app.route("/planner")
def planner_page():
    return render_template("planner.html")

# ✅ Prompt only API
@app.route("/prompt-only", methods=["POST"])
def prompt_only():
    try:
        prompt_text = request.json.get("prompt", "")
        language = request.json.get("language", "English")

        final_prompt = apply_language(prompt_text, language)

        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": final_prompt}]}]}

        response = requests.post(GEMINI_URL, headers=headers, json=data)

        if response.status_code == 200:
            result = response.json()["candidates"][0]["content"]["parts"][0]["text"]

            conn = sqlite3.connect("history.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO history (image_filename, prompt, gemini_response, timestamp)
                VALUES (?, ?, ?, ?)
            """, ("(None)", prompt_text, result, datetime.now()))
            conn.commit()
            conn.close()

            return jsonify({"response": result})
        else:
            error_info = response.json().get("error", {}).get("message", "Unknown error")
            return jsonify({"error": f"Gemini failed: {error_info}"}), 500

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ✅ Upload image + prompt API
@app.route("/upload-image", methods=["POST"])
def upload_image():
    try:
        image = request.files["image"]
        prompt = request.form.get("prompt", "")
        grade = request.form.get("grade", "")
        language = request.form.get("language", "English")

        filepath = os.path.join(UPLOAD_FOLDER, image.filename)
        image.save(filepath)

        extracted_text = pytesseract.image_to_string(Image.open(filepath))

        final_prompt = f"You are helping a teacher with a worksheet for {grade}.\n\nWorksheet Text:\n{extracted_text}\n\nTeacher's Prompt:\n{prompt}"
        final_prompt = apply_language(final_prompt, language)

        response = requests.post(GEMINI_URL, headers={"Content-Type": "application/json"}, json={
            "contents": [{"parts": [{"text": final_prompt}]}]
        })

        if response.status_code == 200:
            result = response.json()["candidates"][0]["content"]["parts"][0]["text"]

            conn = sqlite3.connect("history.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO history (image_filename, prompt, gemini_response, timestamp)
                VALUES (?, ?, ?, ?)
            """, (image.filename, prompt, result, datetime.now()))
            conn.commit()
            conn.close()

            return jsonify({"response": result})
        else:
            return jsonify({"error": "Gemini failed to respond"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Visual Aid Generator API
@app.route("/visual-aid", methods=["POST"])
def visual_aid():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "")
        language = data.get("language", "English")

        final_prompt = apply_language(prompt, language)

        response = requests.post(GEMINI_URL, headers={"Content-Type": "application/json"}, json={
            "contents": [{"parts": [{"text": final_prompt}]}]
        })

        if response.status_code == 200:
            result = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            return jsonify({"response": result})
        else:
            return jsonify({"error": "Gemini failed to respond"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Planner API
@app.route("/generate-plan", methods=["POST"])
def generate_plan():
    try:
        data = request.get_json()
        grade = data.get("grade", "Grade 1")
        start_date = data.get("start_date", "")
        end_date = data.get("end_date", "")
        topics = data.get("topics", "")
        language = data.get("language", "English")

        prompt = f"""
        Create a weekly lesson plan for {grade} from {start_date} to {end_date}.
        Topics: {topics}.
        Include teaching activities, worksheets, and fun tasks.
        """

        final_prompt = apply_language(prompt, language)

        response = requests.post(GEMINI_URL, headers={"Content-Type": "application/json"}, json={
            "contents": [{"parts": [{"text": final_prompt}]}]
        })

        if response.status_code == 200:
            result = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            return jsonify({"response": result})
        else:
            return jsonify({"error": "Gemini failed to respond"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ View history
@app.route("/history")
def view_history():
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return render_template("history.html", rows=rows)

# ✅ Run the app
if __name__ == "__main__":
    app.run(debug=True)
