import pytest
from app import app
from src.repository import get_random_slur_record
from src.slurs import assemble_question, get_other_targets


def test_get_random_slur_record():
    with app.app_context():
        slur_record = get_random_slur_record()
        assert slur_record is not None
        assert slur_record.slur is not None
        assert slur_record.target is not None

def test_get_other_targets():
    with app.app_context():
        slur_record = get_random_slur_record()
        if slur_record is None:
            pytest.skip("No slurs in DB")
            
        targets = get_other_targets(slur_record)
        assert len(targets) == 4
        assert slur_record.target not in targets

def test_assemble_question():
    class DummySlur:
        slur = "test_slur"
        target = "test_target"
        origins = "test_origin"
    
    slur_record = DummySlur()
    other_targets = ["target1", "target2", "target3", "target4"]
    question = assemble_question(slur_record, other_targets)
    
    assert question["slur"] == "test_slur"
    assert question["correct_target"] == "test_target"
    assert question["origin"] == "test_origin"
    assert len(question["targets"]) == 5
    assert "test_target" in question["targets"]
    assert "target1" in question["targets"]
