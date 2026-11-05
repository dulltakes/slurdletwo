from slurdletwo.extensions import db


class Slur(db.Model):
    __tablename__ = "slurs"

    slur = db.Column(db.String, primary_key=True)
    target = db.Column(db.String)
    origins = db.Column(db.String)
