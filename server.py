import os
from typing import Dict, List

from dotenv import load_dotenv
from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit

from openai_client import openai_client


load_dotenv()


PORT = int(os.getenv("PORT", "3000"))

app = Flask(
    __name__,
    static_folder="public",
    static_url_path="/",
)
socketio = SocketIO(app, cors_allowed_origins="*")


SYSTEM_PROMPT = (
    "You are an expert in public speaking, and you know how to create engaging "
    "and powerful talks. You understand how to structure them, and put them in "
    "simple language. Help me create a new talk by starting a conversation with "
    "me about what the talk will be about."
)


# Store per-connection conversation history and processing flags
conversations: Dict[str, List[Dict[str, str]]] = {}
processing_flags: Dict[str, bool] = {}


@app.route("/")
def index():
    # Serve the same index.html as the Node version
    return send_from_directory("public", "index.html")


@socketio.on("connect")
def handle_connect():
    sid = request.sid
    print(f"New client connected: {sid}")

    # Initialize conversation history for this client
    conversations[sid] = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    processing_flags[sid] = False

    # Initial assistant message, same wording as Node server.js
    initial_message = (
        "Hello! I'm here to help you create an engaging and powerful talk. "
        "Let's start by discussing what your talk will be about. What topic or "
        "idea would you like to present?"
    )
    emit("chat response", initial_message)


@socketio.on("chat message")
def handle_chat_message(message: str):
    sid = request.sid

    # Ignore if already processing a message for this client
    if processing_flags.get(sid):
        return

    processing_flags[sid] = True

    try:
        # Let the user know we're thinking
        emit("thinking", True)

        history = conversations.setdefault(
            sid, [{"role": "system", "content": SYSTEM_PROMPT}]
        )
        history.append({"role": "user", "content": message})

        completion = openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=history,
        )

        response_content = completion.choices[0].message.content
        history.append({"role": "assistant", "content": response_content})

        emit("thinking", False)
        emit("chat response", response_content)
    except Exception as exc:
        print(f"Error while processing message for {sid}: {exc}")
        emit("thinking", False)
        emit(
            "chat response",
            "Sorry, there was an error processing your request.",
        )
    finally:
        processing_flags[sid] = False


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    print(f"Client disconnected: {sid}")
    conversations.pop(sid, None)
    processing_flags.pop(sid, None)


if __name__ == "__main__":
    # Use eventlet or gevent in production; the default is fine for local dev
    socketio.run(app, host="0.0.0.0", port=PORT)

