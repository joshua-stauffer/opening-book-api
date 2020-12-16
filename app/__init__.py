from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_praetorian import Praetorian
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import config


migrate = Migrate()


# create naming convention for Alembic migrations
# as per Flask docs: https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/#using-custom-metadata-and-naming-conventions
# with an update to "ck": https://github.com/sqlalchemy/sqlalchemy/issues/3345
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)
guard = Praetorian()
cors = CORS()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
 
    from .models import User
    guard.init_app(app, User)
    cors.init_app(app)
    limiter.init_app(app)

    # set render_as_batch=True to fix sqlite migration issues
    # as per Miguel: https://youtu.be/wpRVZFwsD70
    migrate.init_app(app, db, render_as_batch=True)
    
    if app.config['SSL_REDIRECT']:
        from flask_sslify import SSLify
        sslify = SSLify(app)


    from . import main
    app.register_blueprint(main.bp)
    # urls inside of blueprints are typically given their own namespace,
    # but in this case we want this to be the default
    app.add_url_rule('/', endpoint='index')

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app