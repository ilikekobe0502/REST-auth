#!/usr/bin/env python
import os
from flask import Flask, abort, request, g, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from errorHandler import InvalidUsage
from statusCode import Code,response
import json

# initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# extensions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(64))
    email = db.Column(db.String(128))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user

# Internal function

@auth.error_handler
def auth_error_handler():
    result = response(Code.login_failed)
    return json.dumps(result)

@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True

# API

@app.route('/api/users', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    email = request.json.get('email')
    if username is None or password is None or email is None:
        #raise InvalidUsage('missing argument', status_code=400)
        result = response(Code.missing_argument)
        return json.dumps(result)

    if username == '' or password == '' or email == '':
        #raise InvalidUsage('something is empty', status_code=400)
        result = response(Code.something_empty)
        return json.dumps(result)

    if User.query.filter_by(username=username).first() is not None:
        #raise InvalidUsage('user already exists', status_code=400)
        result = response(Code.user_exisit)
        return json.dumps(result)

    user = User(username=username,email=email)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    result = response(Code.succeed,'user create success')
    return (json.dumps(result), 201,
            {'Location': url_for('get_user', id=user.id, _external=True)})


@app.route('/api/users/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if not user:
        #abort(400)
        result = response(Code.user_do_not_exisit,'Can not find user ')
    else:
        result = response(Code.succeed,dict({'username':user.username}))
    return json.dumps(result)


@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    result = response(Code.succeed,dict({'token':token.decode('ascii'),'duration':600}))
    return json.dumps(result)


@app.route('/api/login')
@auth.login_required
def get_login():
    result = response(Code.succeed,'login success')
    return json.dumps(result)

@app.route('/')
def test():
    result = response(Code.succeed,'Hello world')
    return json.dumps(result)

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = json.dumps(error.to_dict())
    response.status_code = error.status_code
    return response

if __name__ == '__main__':
    if not os.path.exists('db.sqlite'):
        db.create_all()
    app.run(debug=True)
