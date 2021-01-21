"""
Base blueprint for flask app, returning main site functionality
"""
from flask import Blueprint

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return '<h1>Opening Book API</h1>'

