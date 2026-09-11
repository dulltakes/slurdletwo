import pytest
from src.slurs import generate_slur, generate_other_targets, assemble_question

def test_generate_slur():
    slur = generate_slur()
    assert slur is not None
    assert len(slur) == 3 # slur, target, origin

def test_generate_other_targets():
    slur = generate_slur()
    targets = generate_other_targets(slur)
    assert len(targets) == 4
    assert slur[1] not in targets

def test_assemble_question():
    slur = ("test_slur", "test_target", "test_origin")
    other_targets = ["target1", "target2", "target3", "target4"]
    question = assemble_question(slur, other_targets)
    
    assert question["slur"] == "test_slur"
    assert question["correct_target"] == "test_target"
    assert question["origin"] == "test_origin"
    assert len(question["targets"]) == 5
    assert "test_target" in question["targets"]
    assert "target1" in question["targets"]
