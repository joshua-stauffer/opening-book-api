from flask import request
from flask_praetorian import auth_required, current_user
from . import api
from .. import guard, db, limiter
from ..models import User


@api.route('/login', methods=['POST'])
@limiter.limit("10/minute")
@limiter.limit("1/second")
def login():
    r = request.get_json(force=True)
    username = r.get('username', None)
    password = r.get('password', None)

    user = guard.authenticate(username, password)
    response = {'access_token': guard.encode_jwt_token(user)}
    return response


@api.route('/refresh', methods=['POST'])
@limiter.limit("1/minute")
def refresh():
    old_token = refresh.get_data()
    new_token = guard.refresh_jwt_token(old_token)
    response = {'access_token': new_token}
    return response


@api.route('/get-move', methods=['GET'])
@auth_required
def get_move():
    return {'message': f'protected endpoint (allowed user {current_user().username})'}