"""Gameplay routes for the Slurdle trivia game."""

from flask import Blueprint, jsonify, render_template, request, session

from slurdletwo.game import (
    assemble_question,
    format_typographic_quotes,
    get_other_targets,
)
from slurdletwo.repository import get_random_slur_record

game_bp = Blueprint("game", __name__)


def make_question() -> dict:
    slur_record = get_random_slur_record()
    other_targets = get_other_targets(slur_record)
    return assemble_question(slur_record, other_targets)


@game_bp.route("/")
def slurdle():
    data = make_question()

    session["correct_target"] = data["correct_target"]
    session["slur"] = data["slur"]
    session["origin"] = data["origin"]

    return render_template("index.jinja", data=data)


@game_bp.route("/next", methods=["GET"])
def next_question():
    data = make_question()

    session["correct_target"] = data["correct_target"]
    session["slur"] = data["slur"]
    session["origin"] = data["origin"]

    return jsonify(data)


@game_bp.route("/guess", methods=["POST"])
def guess():
    body = request.get_json(silent=True) or {}
    user_guess = body.get("target")

    # .get() prevents server crashes if session expires
    correct = session.get("correct_target")

    if user_guess == correct:
        raw_message = (
            f"{session.get('slur')} refers to {correct}. {session.get('origin')}"
        )
        return jsonify(
            {
                "correct": True,
                "message": format_typographic_quotes(raw_message),
            }
        )
    else:
        return jsonify({"correct": False})
