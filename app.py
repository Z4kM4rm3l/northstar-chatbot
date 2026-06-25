import uuid
from flask import Flask, request, jsonify, render_template, session
from chatbot import chatbot

app = Flask(__name__)
app.secret_key = "northstar-secret-key"


@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

    session_id = session["session_id"]
    response = chatbot.process_message(session_id, user_message)

    return jsonify({"response": response})


@app.route("/reset", methods=["POST"])
def reset():
    session_id = session.get("session_id")

    if session_id and hasattr(chatbot, 'sessions'):
        chatbot.sessions.pop(session_id, None)

    session["session_id"] = str(uuid.uuid4())
    return jsonify({"status": "reset"})


if __name__ == "__main__":
    app.run(debug=True)