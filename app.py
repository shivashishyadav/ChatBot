from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
from groq import Groq
import os
from dotenv import load_dotenv
import markdown

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
    if "chat_history" not in session:
        session["chat_history"] = []

    if request.method == "POST":
        user_message = request.form["message"]

        # Save user msg in plain text
        session["chat_history"].append(("user", user_message))

        try:
            # Build messages for Groq (from plain text history)
            messages = [{"role": "system", "content": "You are a helpful chatbot"}]

            for role, msg in session["chat_history"]:
                if role == "user":
                    messages.append({"role": "user", "content": msg})
                elif role == "bot":
                    messages.append({"role": "assistant", "content": msg})

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
            )

            bot_reply = response.choices[0].message.content

            # Save bot reply in plain text (not HTML)
            session["chat_history"].append(("bot", bot_reply))
            session["chat_history"] = session["chat_history"][-20:]

        except Exception as e:
            bot_reply = "Sorry, I had trouble connecting to the AI service."
            session["chat_history"].append(("bot", bot_reply))

        return redirect(url_for("home"))

    #  Convert bot replies to Markdown only when rendering
    rendered_history = []
    for role, msg in session["chat_history"]:
        if role == "bot":
            rendered_history.append(
                (role, markdown.markdown(msg, extensions=["fenced_code", "nl2br"]))
            )
        else:
            rendered_history.append((role, msg))

    return render_template("index.html", chat_history=rendered_history)


@app.route("/clear")
def clear():
    session.pop("chat_history", None)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
