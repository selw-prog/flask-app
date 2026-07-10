from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import distinct
from ..db import db
from ..models.tornado import TornadoEvent

tornado_bp = Blueprint('tornado', __name__)


@tornado_bp.route('/')
def index():
    states = [
        row[0] for row in
        db.session.query(distinct(TornadoEvent.state)).order_by(TornadoEvent.state).all()
    ]
    return render_template('tornado/index.html', states=states)


@tornado_bp.route('/api/events')
def get_events():
    state = request.args.get('state', '').upper()
    if not state:
        return jsonify([])
    events = (
        TornadoEvent.query
        .filter_by(state=state)
        .order_by(TornadoEvent.event_date)
        .all()
    )
    return jsonify([{
        'id': e.id,
        'event_date': e.event_date.isoformat(),
        'state': e.state,
        'county': e.county,
        'scale': e.scale,
        'location': e.location,
    } for e in events])
