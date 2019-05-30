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
    __table_args__ = (db.UniqueConstraint('request_id', 'username', name='req_user'),)

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), db.ForeignKey('users.username'))
    request_id = db.Column(db.String(40), nullable=True)
    form_values = db.Column(db.Text(), nullable=True)
    grid_values = db.Column(db.Text(), nullable=True)
    version = db.Column(db.Float(), nullable=True)
    submitted = db.Column(db.Boolean(), nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
    submitted_on = db.Column(db.DateTime, nullable=True)

    def add(self):
        db.session.add(self)
        db.session.commit()

    def __init__(
        self,
        username,
        version,
        request_id,
        submitted_on='test',
        created_on='test',
        form_values='{}',
        grid_values='{}',
        submitted=False,
    ):
        now = datetime.datetime.utcnow()
        self.username = username
        self.request_id = request_id
        self.version = version
        self.grid_values = grid_values
        self.form_values = form_values
        self.submitted = submitted
        self.created_on = now.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'username': self.username,
            'version': self.version,
            'request_id': self.request_id,
            'form_values': self.form_values,
            'grid_values': self.grid_values,
            'submitted': self.submitted,
            'created_on': self.created_on.strftime('%Y-%m-%d %H:%M:%S'),
            'submitted_on': self.submitted_on.strftime('%Y-%m-%d %H:%M:%S') if self.submitted_on else None,
        }


# def insert_initial_values(*args, **kwargs):
#     db.session.add(Submission(username=1))

#     db.session.commit()


# event.listen(Submission.__table__, 'after_create', insert_initial_values)
