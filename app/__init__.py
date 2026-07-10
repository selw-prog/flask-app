import os
from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics
from .db import db
from .routes.main import main_bp
from .routes.tornado import tornado_bp


def create_app():
    app = Flask(__name__, static_folder='static')

    base_uri = 'mysql+pymysql://{user}:{pwd}@{host}:{port}'.format(
        user=os.environ['DB_USER'],
        pwd=os.environ['DB_PASSWORD'],
        host=os.environ['DB_HOST'],
        port=os.environ['DB_PORT'],
    )

    app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
    app.config['SQLALCHEMY_DATABASE_URI'] = f"{base_uri}/{os.environ['DB_NAME']}"
    app.config['SQLALCHEMY_BINDS'] = {
        'tornado': f"{base_uri}/tornado_events",
    }

    db.init_app(app)
    PrometheusMetrics(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(tornado_bp, url_prefix='/projects/tornado')

    return app
