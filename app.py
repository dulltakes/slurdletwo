import os

from flask import Flask, jsonify, render_template, request, session

from src.config import SQLALCHEMY_DATABASE_URI
from src.ml_service import ml_service
from src.models import db
from src.repository import get_random_slur_record
from src.slurs import assemble_question, get_other_targets

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    ml_service.load()


def make_question():
    slur_record = get_random_slur_record()
    other_targets = get_other_targets(slur_record)
    return assemble_question(slur_record, other_targets)


@app.route("/")
def slurdle():
    data = make_question()

    session["correct_target"] = data["correct_target"]
    session["slur"] = data["slur"]
    session["origin"] = data["origin"]

    return render_template("index.jinja", data=data)


@app.route("/next", methods=["GET"])
def next_question():
    data = make_question()

    session["correct_target"] = data["correct_target"]
    session["slur"] = data["slur"]
    session["origin"] = data["origin"]

    return jsonify(data)


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
