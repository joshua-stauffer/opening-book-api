from datetime import datetime
from random import choice
from supermemo2 import SMTwo
from . import db, guard
from .utils.sort_funcs import average_descendent_easiness, sort_by_date

# various useful variables
# a blank board
STARTING_POSITION_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
FIRST_MOVE = {'id': '', 'fen': STARTING_POSITION_FEN, 'san': ''}
COLOR_CHOICES = ['w', 'b', 'black', 'white']

# error messages
no_moves_error = {'error_message': 'No moves to display'}


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    hashed_password = db.Column(db.Text)
    roles = db.Column(db.Text) # need this for flask_praetorian
    is_active = db.Column(db.Boolean, default=True, server_default='true')
    moves = db.relationship('Move', backref='user')

    @property
    def password(self):
        return self.hashed_password

    @password.setter
    def password(self, password):
        self.hashed_password = guard.hash_password(password)

    @property
    def rolenames(self):
        try:
            return self.roles.split(',')
        except Exception:
            return []

    @classmethod
    def lookup(cls, username):
        return cls.query.filter_by(username=username).one_or_none()

    @classmethod
    def identify(cls, id):
        return cls.query.get(id)

    @property
    def identity(self):
        return self.id

    def is_valid(self):
        return self.is_active


class Move(db.Model):
    __tablename__ = 'moves'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    parent_id = db.Column(db.Integer, db.ForeignKey('moves.id'))
    fen = db.Column(db.String(128))
    children = db.relationship('Move',
                    backref=db.backref('parent', remote_side=[id]))
    san = db.Column(db.String(8))
    perspective = db.Column(db.String(1)) # w or b
    # is this a move i'm trying to memorize, or a possible opponent response?
    book_move = db.Column(db.Boolean)

    # supermemo two values
    # init as None, and will be updated on first study
    last_review = db.Column(db.DateTime, nullable=True)
    next_review = db.Column(db.DateTime, nullable=True)
    repetitions = db.Column(db.Integer, nullable=True)
    easiness = db.Column(db.Float, nullable=True)
    interval = db.Column(db.Integer, nullable=True)
    @property
    def sm2(self):
        return f"""last review: {self.last_review}
        next review: {self.next_review}
        repetitions: {self.repetitions}
        easiness {self.easiness}
        interval {self.interval}
        """

    @classmethod
    def add_study_session(cls, move_id, quality):
        """update SMTwo stats for a move"""
        move = cls.query.filter_by(id=move_id).first()
        move._add_study_session(quality)

    def _add_study_session(self, quality):
        """
        internal function to updates database values related to supermemo two

        params:
            quality: int between 0 and 5 (inclusive)
        """
        print(f'adding study session for {self.id} - {self.san}')
        print(f'adding score {quality}')
        if self.easiness == None:
            sm_two = SMTwo(quality=quality, first_visit=True)
        else:
            sm_two = SMTwo(
                quality=quality,
                interval=self.interval,
                repetitions=self.repetitions,
                easiness=self.easiness,
                #last review defaults to now
            )
        sm_two.new_sm_two()
        self.interval = sm_two.new_interval
        self.easiness = sm_two.new_easiness
        self.repetitions = sm_two.new_repetitions
        self.next_review = datetime.strptime(sm_two.next_review, '%Y-%m-%d')
        self.last_review = datetime.now()

        db.session.add(self)
        db.session.commit()

    def to_json(self):
        """returns dict with keys id, fen, and san"""
        return {
            "id": self.id,
            "fen": self.fen,
            "san": self.san,
        }


    @classmethod
    def get_next_moves(cls, move_id, score):
        """updates last move score and
        returns a dict with keys move and next
        """
        last_move = cls.query.filter_by(id=move_id).first()
        if score:
            last_move._add_study_session(score)
        possible_moves = last_move.children
        print(f'possible moves are {possible_moves}')
        possible_moves.sort(key=average_descendent_easiness)
        move = possible_moves[0]
        if not move:
            return no_moves_error
        next_moves = move.children
        return {
            'move': move.to_json(),
            'next': [m.to_json() for m in next_moves]
        }

    @classmethod
    def get_whites_first_book_moves(cls, user_id):
        """returns a dict with keys move and next"""
        moves = cls.query \
                .filter_by(user_id=user_id) \
                .filter_by(parent_id=None) \
                .filter_by(perspective='w') \
                .all()
        if not moves:
            print(f'no moves: {moves}')
            return no_moves_error
        return {
            'move': FIRST_MOVE,
            'next': [m.to_json() for m in moves]
        }

    @classmethod
    def get_blacks_first_book_move(cls, user_id):
        """returns dict with keys move and next"""
        white_moves = cls.query \
                    .filter_by(user_id=user_id) \
                    .filter_by(parent_id=None) \
                    .filter_by(perspective='b') \
                    .all()
        white_moves.sort(key=average_descendent_easiness, reverse=True)
        if not white_moves:
            return no_moves_error
        return {
            'move': white_moves[0].to_json(),
            'next': [m.to_json() for m in white_moves[0].children]
        }
    
    @classmethod
    def get_move_by_next_review(cls, user_id, color):
        #TODO: remove filter by color if user hasn't provided color
        """get the next book move to be reviewed"""
        # validate color
        if color not in COLOR_CHOICES:
            color = choice(COLOR_CHOICES)
        # get all book moves for this user
        all_moves = cls.query \
                        .filter_by(user_id=user_id) \
                        .filter_by(book_move=True) \
                        .all()
        # find all moves where the opposite color is to move
        moves = [m for m in all_moves if color[0] != m.fen.split()[1]]
        if not moves:
            return no_moves_error
        # get the move due for review soonest
        moves.sort(key=sort_by_date)
        goal_move = moves[0]
        move = cls.query.filter_by(id=goal_move.parent_id).first()
        if not move:
            move = FIRST_MOVE
            children = cls.query.filter_by(parent_id=None).all()
            return {'move': move, 'next': [m.to_json() for m in children]}
        return {
            'move': move.to_json(),
            'next': [m.to_json() for m in move.children]
        }
        

    @classmethod
    def create_move(cls, user_id, parent_id, fen, san, perspective):
        new_move = cls(
            user_id=user_id,
            parent_id=parent_id,
            fen=fen,
            san=san,
            perspective=perspective
        )
        db.session.add(new_move)
        db.session.commit()
        return new_move.id
