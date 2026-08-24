from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    skills = db.relationship('Skill', backref='owner', lazy=True, cascade='all, delete-orphan')
    swap_requests_sent = db.relationship('SwapRequest', foreign_keys='SwapRequest.requester_id', backref='requester', lazy=True)
    swap_requests_received = db.relationship('SwapRequest', foreign_keys='SwapRequest.target_id', backref='target', lazy=True)

class Skill(db.Model):
    __tablename__ = 'skills'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    skill_type = db.Column(db.Enum('teach', 'learn'), nullable=False, default='teach')
    skill_level = db.Column(db.Enum('beginner', 'intermediate', 'advanced'), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SwapRequest(db.Model):
    __tablename__ = 'swap_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_offered_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    skill_wanted_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    status = db.Column(db.Enum('pending', 'accepted', 'rejected'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    skill_offered = db.relationship('Skill', foreign_keys=[skill_offered_id])
    skill_wanted = db.relationship('Skill', foreign_keys=[skill_wanted_id])

class Availability(db.Model):
    __tablename__ = 'availability'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    day_of_week = db.Column(db.Enum('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'))
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    timezone = db.Column(db.String(50), default='Asia/Kolkata')

class ScheduledMeeting(db.Model):
    __tablename__ = 'scheduled_meetings'
    
    id = db.Column(db.Integer, primary_key=True)
    swap_request_id = db.Column(db.Integer, db.ForeignKey('swap_requests.id'), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meeting_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    meeting_link = db.Column(db.String(500))
    status = db.Column(db.Enum('scheduled', 'completed', 'cancelled', 'rescheduled'), default='scheduled')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    swap_request = db.relationship('SwapRequest', backref='meetings')
    organizer = db.relationship('User', foreign_keys=[organizer_id])
    participant = db.relationship('User', foreign_keys=[participant_id])