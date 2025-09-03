from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
)
# THIS MAKES FLASK REMEMBER THINGS BETWEEN REQUESTS
app.config["SESSION_TYPE"] = "filesystem"  # store sessions in local files
Session(app)


client = Groq(api_key=os.getenv("GROQ_API_KEY"))


@app.route("/", methods=["GET", "POST"])
def home():

    # STEP-1: Make sure chat_history exists
    # session is a special dictionary provided by Flask.
    # It stores data separately for each user (like a private box).
    # Here, we’re checking: “Does this user already have a chat_history list stored?”
    # If not,j we’ll create one in the next line.
    if "chat_history" not in session:
        session["chat_history"] = []  # {"chat_history": []}

    # STEP-2: Handle form submission (when user sends a message)
    if (
        request.method == "POST"
    ):  # We only want to process messages when the user actually submits the chat form; that’s "POST"
        user_message = request.form[
            "message"
        ]  # get text from input, which name is "message"
        session["chat_history"].append(
            ("user", user_message)
        )  # session["chat_history"] == [("user", "Hello")]

        # STEP-3: Bot reply
        # bot_reply = "Hii! I am your chatbot"

        # STEP-4: Call graq API
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a helpful chatbot"},
                    {"role": "user", "content": user_message},
                ],
            )
            bot_reply = response.choices[0].message.content
            session["chat_history"].append(("bot", bot_reply))  # save bot msg
            session["chat_history"] = session["chat_history"][
                -20
            ]  # Keep only the last 20 messages
        except Exception as e:
            bot_reply = "Sorry, I had trouble connecting to the AI service."

        # Now our session dictionary something like this
        # session["chat_history"] == [
        #     ("user", "Hello"),
        #     ("bot", "Hello! I'm your chatbot.")
        # ]

        return redirect(url_for("home"))

    return render_template(
        "index.html", chat_history=session["chat_history"]
    )  # pass Python data into index.html


@app.route("/clear")
def clear():
    session.pop("chat_history", None)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
