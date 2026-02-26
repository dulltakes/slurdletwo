from flask import (
    Flask,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

app = Flask(__name__)
app.secret_key = "your-secret-key"


@app.route("/")
def slurdle():
    data = current_app.config.get("DATA", "")
    session["correct_target"] = data["correct_target"]
    session["slur"] = data["slur"]
    session["origin"] = data["origin"]
    return render_template("index.jinja", data=data)


@app.route("/guess", methods=["POST"])
def guess():
    body = request.get_json()
    user_guess = body["target"]
    correct = session.get("correct_target")

    if user_guess == correct:
        return jsonify(
            {
                "correct": True,
                "message": f"{session['slur']} refers to {correct}. {session['origin']}",
            }
        )
    else:
        return jsonify({"correct": False})


@app.route("/next")
def next_question():
    make_question = current_app.config.get("MAKE_QUESTION")
    app.config["DATA"] = make_question()
    return redirect(url_for("slurdle"))


if __name__ == "__main__":
    app.run()
