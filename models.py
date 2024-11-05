from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(50), nullable=False)  # donor, charity, admin, etc.
    phonenumber = db.Column(db.String(20), nullable=True)  # Changed to String to handle phone numbers better
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    donations = db.relationship('Donation', backref='donor', lazy=True)
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "user_type": self.user_type
        }

    @validates('username')
    def validate_username(self, key, username):
        if len(username) < 5:
            raise ValueError('Username must be at least 5 characters')
        return username

    @validates('email')
    def validate_email(self, key, email):
        if '@' not in email:
            raise ValueError('Invalid email format. Must contain "@"')
        return email

    @validates('password')
    def validate_password(self, key, password):
        if not any(char.isdigit() for char in password):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in password):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in password):
            raise ValueError('Password must contain at least one lowercase letter')
        return password

    @validates('user_type')
    def validate_user_type(self, key, user_type):
        if user_type not in ['donor', 'admin', 'charity']:
            raise ValueError('Invalid user type. Must be one of: donor, admin, charity')
        return user_type

class Donation(db.Model):
    __tablename__ = 'donations'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    donation_amount = db.Column(db.Float, nullable=False)
    cause_id = db.Column(db.String(255))
    agree_to_terms = db.Column(db.Boolean, default=False)
    subscribe_monthly = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Testimonial(db.Model):
    __tablename__ = 'testimonials'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Fixed foreign key reference

class AidDistribution(db.Model):
    __tablename__ = 'aid_distributions'
    
    id = db.Column(db.Integer, primary_key=True)
    beneficiary_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)

class Contact(db.Model):
    __tablename__ = 'contacts'
    
    id = db.Column(db.Integer, primary_key=True)   
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phonenumber = db.Column(db.String(20), nullable=True)  # Changed to String
    description = db.Column(db.Text, nullable=False)

class Charity(db.Model):
    __tablename__ = 'charities'
    
    id = db.Column(db.Integer, primary_key=True)   
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Integer, nullable=True)
    email = db.Column(db.String(120), nullable=False)  # Changed to String(120) for consistency
    document = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    title=db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)   
    amount = db.Column(db.Integer, nullable=True)
    email = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    username = db.Column(db.String(50), nullable=False)
    # Changed to String(120) for consistency