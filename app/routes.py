from app import app, db
from flask import request, jsonify
from functools import wraps
from app.models import User, Expense, Income
import jwt
import datetime
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
			return jsonify({'message':'Login Succesful!', 'token':token.decode('UTF-8'), 'isAdmin':user.admin})


@app.route('/check_auth', methods = ['GET'])
@token_required
def check_auth(current_user):
	return jsonify({'message':'Succesful', 'Current user.username':current_user.username})


@app.route('/add_user', methods = ['POST'])
def add_user():
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

def retExp(current_user):
	from_date = datetime(year=datetime.now().year, month=datetime.datetime.now().month, day=1)
	current_month_expenses = Expense.query.filter_by(user_id=current_user.id).filter(Expense.date >= from_date).filter(Expense.date <= datetime.now()).all()
	return current_month_expenses


@app.route('/month_exp', methods = ['GET'])
@token_required
def month_exp(current_user):
	ret = []
	total = 0
	for exp in retExp(current_user):
		ret.append({'date':exp.date.date(), 'category':exp.category, 'amount':exp.amount})
		total += exp.amount
	return jsonify({'message':'succesful', 'ans':ret, 'total':total}), 200

def retInc(current_user):
	from_date = datetime(year=datetime.now().year, month=datetime.datetime.now().month, day=1)
	current_month_incomes = Income.query.filter_by(user_id=current_user.id).filter(Expense.date >= from_date).filter(Expense.date <= datetime.now()).all()
	return current_month_incomes

@app.route('/month_inc', methods = ['GET'])
@token_required
def month_inc(current_user):
	ret = []
	total = 0
	for inc in retInc(current_user):
		ret.append({'date':inc.date.date(), 'source':inc.source, 'amount':inc.amount})
		total += inc.amount
	return jsonify({'message':'succesful', 'ans':ret, 'total':total}), 200

@app.route('/exp_split', methods = ['GET'])
@token_required
def exp_split(current_user):
	l = db.session.query(Expense.category, db.func.sum(Expense.amount)).filter(Expense.user_id == current_user.id).group_by(Expense.category).all()
	total = db.session.query(db.func.sum(Expense.amount)).filter(Expense.user_id == current_user.id).all()[0][0]
	cur = 0
	ret = []
	for i in range(len(l)-1):
		val = round(l[i][1]*100/total,2)
		cur += val
		ret.append({'y':val, 'label':l[i][0]})
	val = 100-cur
	ret.append({'y':val, 'label':l[-1][0]})
	return jsonify({'message':'succesful', 'ans':ret}), 200


@app.route('/inc_split', methods = ['GET'])
@token_required
def inc_split(current_user):
	l = db.session.query(Income.source, db.func.sum(Income.amount)).filter(Income.user_id == current_user.id).group_by(Income.souce).all()
	total = db.session.query(db.func.sum(Expense.amount)).filter(Expense.user_id == current_user.id).all()[0][0]
	cur = 0
	ret = []
	for i in range(len(l)-1):
		l[i][1] = round(l[i][1]*100/total,2)
		cur += l[i][1]
		ret.append({'y':l[i][1], 'label':l[i][0]})
	l[-1][1] = 100-cur
	ret.append({'y':l[-1][1], 'label':l[-1][0]})
	return jsonify({'message':'succesful', 'ans':ret}), 200
