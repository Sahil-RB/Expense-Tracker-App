from app import app, db
import datetime
from flask import request, jsonify
from functools import wraps
from app.models import User, Expense, Income
import jwt


def token_required(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		token = None
		if 'access_token' in request.headers:
			token = request.headers['access_token']
		if not token:
			return jsonify({'message':'Token is missing'}), 401

		try:
			data = jwt.decode(token, app.config['SECRET_KEY'])
			current_user = User.query.filter_by(id = data['id']).first()
		except:
			return jsonify({'message':'Invalid Token'}), 401

		return f(current_user, *args, **kwargs)
	return decorated


@app.route('/login', methods = ['POST'])
def login():
	username = request.headers.get('username')
	password = request.headers.get('password')

	if not username or not password:
		return jsonify({'message':'Insufficient parameters'}), 400

	else:
		user = User.query.filter_by(username = username).first()
		if not user:
			return jsonify({'message':'Invalid Username'}), 401
		if not user.check_password(password):
			return jsonify({'message':'Incorrect Password'}), 401
		else:
			token = jwt.encode({'id':user.id, 'exp':datetime.datetime.now() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
			return jsonify({'message':'Login Succesful!', 'token':token.decode('UTF-8')})


@app.route('/check_auth', methods = ['GET'])
@token_required
def check_auth(current_user):
	return jsonify({'message':'Succesful', 'Current user.username':current_user.username})


@app.route('/add_user', methods = ['POST'])
@token_required
def add_user(current_user):
	if not current_user.admin:
		return jsonify({'message':'Admin access required!'}), 401
	username = request.headers.get('username')
	password = request.headers.get('password')
	admin = request.headers.get('admin')
	if not username or not password or not admin:
		return jsonify({'message':'Insufficient parameters'}), 400
	u = User.query.filter_by(username = username).first()
	if u:
		return jsonify({'message':'User already exists'}), 400
	u = User(username = username)
	if admin == 'True':
		u.admin = True
	u.set_password(password)
	db.session.add(u)
	db.session.commit()
	return jsonify({'message':'User '+username+' created'}), 201





