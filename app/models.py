from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

class User(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	username = db.Column(db.String(64), index=True, unique = True)
	password_hash = db.Column(db.String(128))
	admin = db.Column(db.Boolean, default = False)
	expenses = db.relationship('Expense', backref = 'SpentBy', lazy='dynamic')
	incomes = db.relationship('Income', backref = 'EarnedBy', lazy='dynamic')

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)
		

	def __repr__(self):
		return '<User:>'+self.username

class Expense(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	category = db.Column(db.String(64), index=True)
	amount = db.Column(db.Float)
	date = db.Column(db.DateTime, index=True, default=date.today())
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	private = db.Column(db.Boolean, default=False)


class Income(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	source = db.Column(db.String(64), index=True)
	amount = db.Column(db.Float)
	date = db.Column(db.DateTime, index=True, default=date.today())
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))