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
        abort(400, f'Missing value {", ".join(error_list)} in POST json')
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


@api.route('/del-move', methods=['POST'])
@auth_required
def del_move():
    r = request.get_json(force=True)
    move_id = r.get('move_id', None)
    if not move_id:
        abort(400)
    user_id = current_user().id

    Move.delete_move(user_id, move_id)
    return {'message': 'success'}, 200


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

    first_move = bool(r.get('first_move', None))
    last_move_list = r.get('last_move_id', [])
    score = r.get('score', None)
    if score:
        score = int(score)

    print(f'Got a request to play: first move: {first_move} color: {color} last move id: {last_move_list} score: {score}')

    if first_move:
        if not color:
            abort(400, 'Missing argument color')
        if color == 'white':
            return Move.get_whites_first_book_moves(user_id)
        elif color == 'black':
            return Move.get_blacks_first_book_move(user_id)

    # did player miss a move with a list of options? set them all to 0
    if len(last_move_list) > 1:
        for move_id in last_move_list:
            Move.add_study_session(move_id, score)
    # now take first value and call it a day
    last_move_id = last_move_list[0]

    # check for valid move id
    if not last_move_id > 0:
        abort(400, 'invalid move id')
    #TODO:  in case of fail, this is currently adding the score twice
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
    r = request.get_json(force=True)
    print('got a request to STUDY with the following args: ', r)

    #color = r.get('color', None)
    last_move_id = r.get('last_move_id', [])
    print('got last move id ', last_move_id)
    score = r.get('score', -1)


    # check for a list of moves to update SMTwo score
    if len(last_move_id) and score >= 0:
        print(f'got a list of length {len(last_move_id)}')
        for move_id in last_move_id:
            Move.add_study_session(move_id, score)
            print(f"just added score {score} for move {move_id}")
    else:
        print(f"couldn't use {last_move_id} or {score}")
    return Move.get_move_by_next_review(user_id)

    


@api.route('/explore', methods=['POST'])
@auth_required
def explore():
    """Returns all moves for a given position
    expects to be passed a json with either of the following keys:
    color: 'w' or 'b'
        starts from beginning of user's database from given color's perspective
    last_move_id: int
        gives all the database moves following from given move
    """
    print('entering explore')
    user_id = current_user().id
    r = request.get_json(force=True)

    color = r.get('color', None)
    last_move_id = int(r.get('last_move_id', 0))
    if not color and not last_move_id:
        print(f'missing something: {color} {last_move_id}')
        abort(400, 'missing color or last_move_id parameters')

    #NOTE: these are lists, so must be jsonified
    if last_move_id:
        print('getting response in Explore view based on move id')
        response = Move.get_descendent_moves(last_move_id)
    else:
        print(f'getting response in Explore view based on color {color}')
        response = Move.get_book_start(user_id, color)
    return jsonify(response)
    