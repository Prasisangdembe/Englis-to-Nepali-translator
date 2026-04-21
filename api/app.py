import json
import os
from pathlib import Path

from flask import Flask, jsonify, request, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from services.translation_service import TranslationService


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "web" / "templates"
app = Flask(__name__, template_folder=str(TEMPLATE_DIR))
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[os.getenv("RATE_LIMIT_PER_MINUTE", "60 per minute")],
)
translation_service = TranslationService()
FEEDBACK_FILE_PATH = Path(__file__).resolve().parent.parent / "data" / "feedback.json"


def load_feedback_store():
    """Load feedback entries from disk."""
    if not FEEDBACK_FILE_PATH.exists():
        return []

    try:
        with FEEDBACK_FILE_PATH.open("r", encoding="utf-8") as file:
            loaded = json.load(file)
            if isinstance(loaded, list):
                return loaded
    except (json.JSONDecodeError, OSError):
        pass

    return []


def save_feedback_store(entries):
    """Persist feedback entries to disk."""
    FEEDBACK_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with FEEDBACK_FILE_PATH.open("w", encoding="utf-8") as file:
        json.dump(entries, file, ensure_ascii=False, indent=2)


feedback_store = load_feedback_store()


@app.route("/", methods=["GET"])
def index():
    """Serve web interface."""
    return render_template("index.html")


@app.route("/api/translate", methods=["POST"])
@limiter.limit("10 per minute")
def translate():
    """Translate English text into Limbu."""
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()

    if not text:
        return jsonify({"success": False, "error": "Field 'text' is required"}), 400

    translation = translation_service.translate_text(text)
    return jsonify({"success": True, "translation": translation})


@app.route("/api/dictionary/search", methods=["GET"])
def search_dictionary():
    """Search dictionary by exact key or partial match."""
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({"success": False, "error": "Query parameter 'q' is required"}), 400

    normalized_query = query.lower()
    matches = []
    for english_word, limbu_entry in translation_service.dictionary.items():
        if normalized_query in english_word:
            matches.append(
                {
                    "english": english_word,
                    "limbu_romanized": limbu_entry["romanized"],
                    "limbu_script": limbu_entry["script"],
                }
            )

    return jsonify(
        {
            "success": True,
            "query": query,
            "count": len(matches),
            "results": matches,
        }
    )


@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    """Accept basic feedback for translation improvements."""
    payload = request.get_json(silent=True) or {}
    english = str(payload.get("english", "")).strip()
    suggested_limbu = str(payload.get("suggested_limbu", "")).strip()
    comment = str(payload.get("comment", "")).strip()

    if not english or not suggested_limbu:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Fields 'english' and 'suggested_limbu' are required",
                }
            ),
            400,
        )

    feedback_entry = {
        "id": len(feedback_store) + 1,
        "english": english,
        "suggested_limbu": suggested_limbu,
        "comment": comment,
        "status": "received",
    }
    feedback_store.append(feedback_entry)
    save_feedback_store(feedback_store)

    return jsonify(
        {
            "success": True,
            "message": "Feedback submitted successfully",
            "feedback": feedback_entry,
        }
    )


@app.route("/api/feedback", methods=["GET"])
def get_feedback():
    """Return all submitted feedback entries."""
    return jsonify(
        {
            "success": True,
            "count": len(feedback_store),
            "feedback": feedback_store,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
