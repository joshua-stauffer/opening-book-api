from flask import request, abort, jsonify
from flask_praetorian import auth_required, current_user
from . import api
from .. import guard, db, limiter
from ..models import User, Move


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
    old_token = request.get_data()
    new_token = guard.refresh_jwt_token(old_token)
    response = {'access_token': new_token}
    return response


@api.route('/add-move', methods=['POST'])
@auth_required
def add_move():
    r = request.get_json(force=True)
    fen = r.get('fen', None)
    san = r.get('san', None)
    perspective = r.get('perspective', None)
    parent_id = r.get('parent_id', None)
    # confirm that values exist
    args = [fen, san, perspective]
    if not all(args):
        required_args_names = ['fen', 'san', 'perspective']
        error_list = []
        for i, arg in enumerate(args):
            if arg == None:
                error_list.append(required_args_names[i])
        abort(404, f'Missing value {", ".join(error_list)} in POST json')
    user_id = current_user().id
    new_move_id = Move.create_move(
        user_id,
        parent_id,
        fen,
        san,
        perspective
    )
    if new_move_id is not None:
        return {'new_move_id': new_move_id}, 200

    #return {'message': f'protected endpoint (allowed user {current_user().username})'}

@api.route('/play', methods=['POST'])
@auth_required
def play():
    """
    expects a json with the following keys:
    color: 'white' or 'black'
    first_move: bool
    last_move_id: parent move
    score: int between 0-5 (inclusive)
        represents supermemo2 score

    returns a json with keys move and next
    """
    # get values from json and coerce into correct types
    user_id = current_user().id
    r = request.get_json(force=True)
    color = r.get('color', None)
    if not color:
        abort(404, 'Missing argument color')
    first_move = bool(r.get('first_move', None))
    last_move_id = int(r.get('last_move_id', 0))
    score = r.get('score', None)
    if score:
        score = int(score)

    if first_move:
        if color == 'white':
            return Move.get_whites_first_book_moves(user_id)
        elif color == 'black':
            return Move.get_blacks_first_book_move(user_id)

    # check for valid move id
    if not last_move_id > 0:
        abort(404, 'invalid move id')
    
    return Move.get_next_moves(last_move_id, score)


@api.route('/study', methods=['POST'])
@auth_required
def study():
    """
    expects a json with the following keys:
    color: 'white' or 'black'
    last_move_id: id of last move (if any)
    score: int between 0-5 (inclusive)
        represents supermemo2 score to associate with last move

    returns a json with keys move and next
    """
    user_id = current_user().id
    r = request.get_json()
    if r:
        color = r.get('color', None)
        last_move_id = int(r.get('last_move_id', 0))
        score = r.get('score', None)
    else: 
        color = None
        score = None
        last_move_id = 0
    if score:
        score = int(score)

    # add SMTwo score for the last request, if provided
    if last_move_id > 0 and score:
        Move.add_study_session(last_move_id, score)

    return Move.get_move_by_next_review(user_id, color)