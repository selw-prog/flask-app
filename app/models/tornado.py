from ..db import db


class TornadoEvent(db.Model):
    __bind_key__ = 'tornado'
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    event_date = db.Column(db.Date, nullable=False)
    state = db.Column(db.String(100), nullable=False, index=True)
    county = db.Column(db.String(100), nullable=False)
    scale = db.Column(db.String(3))
    location = db.Column(db.String(100))
