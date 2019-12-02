import os
import sys
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spell.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    twofa = db.Column(db.String(256), nullable=False)

class Log(db.Model):
    __tablename__ = 'log'

    username = db.Column(db.String(64), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    logintime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    logouttime = db.Column(db.DateTime, default=None)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(User)

class Spell(db.Model):
    __tablename__ = 'results'

    username = db.Column(db.String(64), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    subtext = db.Column(db.Text, nullable=False)
    restext = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(User)


if __name__ == "__main__":
    db.create_all()

