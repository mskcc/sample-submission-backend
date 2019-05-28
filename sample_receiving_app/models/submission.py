import datetime
from random import randint

from flask_sqlalchemy import event
from sqlalchemy.sql import func

from sample_receiving_app import app, db



class Submission(db.Model):
    """
    Token Model for storing JWT tokens
    """

    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    request_id = db.Column(db.Integer, nullable=True)
    form_values = db.Column(db.Text(), nullable=True)
    grid_values = db.Column(db.Text(), nullable=True)
    submitted = db.Column(db.Boolean(), nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
    submitted_on = db.Column(db.DateTime, nullable=True)

    def add(self):
        db.session.add(self)
        db.session.commit()

    def __init__(
        self,
        user_id,
        request_id=randint(100000, 999999),
        submitted_on='test',
        created_on='test',
        form_values='{}',
        grid_values='{}',
        submitted=False,
    ):
        now = datetime.datetime.now()
        self.user_id = user_id
        self.request_id = request_id
        self.grid_values = grid_values
        self.form_values = form_values
        self.submitted = submitted
        self.created_on = now.strftime('%Y-%m-%d %H:%M:%S')


def insert_initial_values(*args, **kwargs):
    db.session.add(Submission(user_id=1))

    db.session.commit()


event.listen(Submission.__table__, 'after_create', insert_initial_values)
