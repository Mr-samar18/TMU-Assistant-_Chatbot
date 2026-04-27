from flask import Flask, render_template, request, jsonify
from rapidfuzz import fuzz
from datetime import datetime
import re, json, random, os
from ai_helper import ask_llama

print("APP STARTING...")
app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_data():
    path = os.path.join(BASE_DIR, "data", "tmu_data.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

tmu_data = load_data()

def clean_text(text):
    text = (text or "").lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text

# Each tag needs at least one of these words present in user input
KEYWORD_GATE = {
    "greeting":       ["hi", "hello", "hey", "hlo", "morning", "evening"],
    "tmu_info":       ["tmu", "teerthanker", "university", "moradabad", "established"],
    "tmu_contact":    ["tmu", "contact", "website", "email", "phone", "number"],
    "courses":        ["course", "courses", "program", "programs", "offered"],
    "bca":            ["bca"],
    "mca":            ["mca"],
    "btech":          ["btech", "b tech", "engineering"],
    "mtech":          ["mtech", "m tech"],
    "bba":            ["bba"],
    "mba":            ["mba"],
    "commerce":       ["bcom", "mcom", "commerce"],
    "law":            ["law", "llb"],
    "pharmacy":       ["pharmacy", "pharm"],
    "nursing":        ["nursing", "gnm", "anm"],
    "medical":        ["medical", "mbbs", "dental", "paramedical"],
    "agriculture":    ["agriculture", "agri"],
    "admission":      ["admission", "apply", "enroll", "document"],
    "fees_scholarship":["fee", "fees", "scholarship"],
    "facilities":     ["hostel", "library", "wifi", "transport", "facility", "campus", "infrastructure"],
    "placements":     ["placement", "placements", "company", "recruit", "package", "job"],
    "student_life":   ["campus life", "events", "fest", "club", "extracurricular"],
    "bot":            ["who are you", "what can you", "thank", "bye", "created you"],
}

def find_best_match(user_input, intents):
    best_score = 0
    best_responses = None
    best_tag = None

    for intent in intents:
        tag = intent["tag"]

        # keyword gate — skip intent if none of its keywords found in input
        if tag in KEYWORD_GATE:
            required = KEYWORD_GATE[tag]
            if not any(kw in user_input for kw in required):
                continue

        for pattern in intent["patterns"]:
            score = fuzz.token_sort_ratio(user_input, pattern)
            if score > best_score:
                best_score = score
                best_responses = intent["responses"]
                best_tag = tag

    print(f"MATCH: '{user_input}' → tag='{best_tag}' score={best_score}")
    return best_score, best_responses

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data_req = request.get_json(silent=True) or {}
        user_question = data_req.get("question", "")
        cleaned = clean_text(user_question)
        timestamp = datetime.now().strftime("%H:%M")

        if not cleaned:
            return jsonify({"answer": "Please type a question.", "timestamp": timestamp})

        SHORT_KEYWORDS = {
            "hi", "hello", "hey", "hlo", "bye", "thanks",
            "bca", "mca", "btech", "mba", "bba", "bcom", "law",
            "mtech", "gnm", "anm", "llb", "medical", "dental",
            "hostel", "placements", "admission", "fees", "courses",
            "nursing", "pharmacy", "agriculture", "tmu"
        }

        if len(cleaned.split()) == 1 and cleaned not in SHORT_KEYWORDS:
            return jsonify({
                "answer": (
                    "Please ask a complete question. Examples:\n"
                    "• BCA fees in TMU\n"
                    "• Does TMU have hostel facilities?\n"
                    "• What courses are offered in TMU?"
                ),
                "timestamp": timestamp
            })

        score, responses = find_best_match(cleaned, tmu_data["intents"])

        college_context = (
            "TMU (Teerthanker Mahaveer University) is a private university in Moradabad, UP. "
            "Established in 2008. Offers BCA, B.Tech, MBA, BBA, MCA, B.Com, Law, Pharmacy, "
            "Nursing, Agriculture, Medical courses. Has hostel, library, WiFi, placements "
            "(TCS, Infosys, Wipro, HCL), and scholarships."
        )

        if score >= 75 and responses:
            answer = random.choice(responses)
        elif score >= 60 and responses:
            answer = "Here's what I found:\n\n" + random.choice(responses)
        else:
            # falls to Ollama
            answer = ask_llama(user_question, college_context)

        return jsonify({"answer": answer, "timestamp": timestamp})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "answer": "Server error. Please try again.",
            "timestamp": datetime.now().strftime("%H:%M")
        })

if __name__ == "__main__":
    app.run(debug=True)