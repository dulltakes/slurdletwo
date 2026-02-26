from flask import Flask, jsonify, render_template, request, session

from src.slurs import assemble_question, generate_other_targets, generate_slur

app = Flask(__name__)
app.secret_key = "your-secret-key"


def make_question():
    slur = generate_slur()
    other_targets = generate_other_targets(slur)
    return assemble_question(slur, other_targets)


@app.route("/")
def slurdle():
    data = make_question()

    session["correct_target"] = data["correct_target"]
    session["slur"] = data["slur"]
    session["origin"] = data["origin"]

    return render_template("index.jinja", data=data)


@app.route("/guess", methods=["POST"])
def guess():
    body = request.get_json()
    user_guess = body.get("target")

    # .get() prevents server crashes if session expires
    correct = session.get("correct_target")

    if user_guess == correct:
        return jsonify(
            {
                "correct": True,
                "message": f"{session.get('slur')} refers to {correct}. {session.get('origin')}",
            }
        )
    else:
        return jsonify({"correct": False})
