from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Slur(db.Model):
    __tablename__ = 'slurs'
    
    slur = db.Column(db.String, primary_key=True)
    target = db.Column(db.String, nullable=False)
    origins = db.Column(db.String)
