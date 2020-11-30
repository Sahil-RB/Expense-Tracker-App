from app import app, db
import datetime
from flask import request, jsonify
from functools import wraps
from app.models import User, Expense, Income
import jwt
from datetime import date
from calendar import monthrange

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


@app.route('/add_expense', methods = ['POST'])
@token_required
def add_expense(current_user):
	category = request.args.get('category')
	amount = request.args.get('amount')
	dt = request.args.get('date')
	private = request.args.get('private')
	if not category or not amount:
		return jsonify({'message':'Insufficient parameters'}), 400
	exp = Expense(category=category, amount=amount, SpentBy=current_user)
	if dt:
		exp.date = dt
	if private:
		exp.private = private
	db.session.add(exp)
	db.session.commit()
	return jsonify({'message':'Expense added'}), 201


@app.route('/add_income', methods = ['POST'])
@token_required
def add_income(current_user):
	source = request.args.get('source')
	amount = request.args.get('amount')
	dt = request.args.get('date')
	if not source or not amount:
		return jsonify({'message':'Insufficient parameters'}), 400
	inc = Income(source=source, amount=amount, EarnedBy=current_user)
	if dt:
		inc.date = dt
	db.session.add(inc)
	db.session.commit()
	return jsonify({'message':'Income added'}), 201

@app.route('/month_exp', methods = ['GET'])
@token_required
def month_exp(current_user):
	cur = date.today()
	first_day_of_month = cur.replace(day = monthrange(cur.year, cur.month)[0])
	last_day_of_month = cur.replace(day = monthrange(cur.year, cur.month)[1])
	ret = []
	total = 0
	for exp in Expense.query.filter(Expense.user_id == current_user.id and Expense.date >= first_day_of_month and Expense.date <= last_day_of_month).all():
		ret.append({'date':exp.date.date(), 'category':exp.category, 'amount':exp.amount})
		total += exp.amout
	return jsonify({'message':'succesful', 'ans':ret, 'total':total}), 200

@app.route('/month_inc', methods = ['GET'])
@token_required
def month_inc(current_user):
	cur = date.today()
	first_day_of_month = cur.replace(day = monthrange(cur.year, cur.month)[0])
	last_day_of_month = cur.replace(day = monthrange(cur.year, cur.month)[1])
	ret = []
	total = 0
	for inc in Income.query.filter(Income.user_id == current_user.id and Income.date >= first_day_of_month and Income.date <= last_day_of_month).all():
		ret.append({'date':inc.date.date(), 'source':inc.source, 'amount':inc.amount})
		total += inc.amount
	return jsonify({'message':'succesful', 'ans':ret, 'total':total}), 200


