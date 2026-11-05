"""Gameplay routes for the Slurdle trivia game."""

from flask import Blueprint, jsonify, render_template, request, session

from slurdletwo.game import (
    assemble_question,
    format_typographic_quotes,
    get_other_targets,
)
from slurdletwo.repository import get_random_slur_record

game_bp = Blueprint("game", __name__)


MAX_RECENT_QUESTIONS = 10


def record_question_session(data: dict) -> None:
    """Store active round state and preserve a rolling history of recent questions."""
    session["correct_target"] = data["correct_target"]
    session["slur"] = data["slur"]
    session["origin"] = data["origin"]

    recent = session.get("recent_questions")
    if not isinstance(recent, dict):
        recent = {}

    recent[data["slur"]] = {
        "target": data["correct_target"],
        "origin": data["origin"],
    }

    if len(recent) > MAX_RECENT_QUESTIONS:
        excess = len(recent) - MAX_RECENT_QUESTIONS
        for old_key in list(recent.keys())[:excess]:
            del recent[old_key]

    session["recent_questions"] = recent


def make_question() -> dict:
    slur_record = get_random_slur_record()
    other_targets = get_other_targets(slur_record)
    return assemble_question(slur_record, other_targets)


@game_bp.route("/")
def slurdle():
    data = make_question()
    record_question_session(data)
    return render_template("index.jinja", data=data)


@game_bp.route("/next", methods=["GET"])
def next_question():
    data = make_question()
    record_question_session(data)
    return jsonify(data)


@game_bp.route("/guess", methods=["POST"])
def guess():
    body = request.get_json(silent=True) or {}
    user_guess = body.get("target")
    slur = body.get("slur")

    # .get() prevents server crashes if session expires
    correct = session.get("correct_target")

    # 1. Primary check: direct match against active session round
    if user_guess and user_guess == correct:
        raw_message = (
            f"{session.get('slur')} refers to {correct}. {session.get('origin')}"
        )
        return jsonify(
            {
                "correct": True,
                "message": format_typographic_quotes(raw_message),
            }
        )

    # 2. Secondary check: recent question lookup for race conditions (e.g. GTM debug/prefetch probes)
    recent = session.get("recent_questions", {})
    if slur and user_guess and isinstance(recent, dict) and slur in recent:
        slur_data = recent[slur]
        if user_guess == slur_data.get("target"):
            raw_message = (
                f"{slur} refers to {user_guess}. {slur_data.get('origin', '')}"
            )
            return jsonify(
                {
                    "correct": True,
                    "message": format_typographic_quotes(raw_message),
                }
            )

    return jsonify({"correct": False})
