from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_vip = db.Column(db.Boolean, default=False)

    avatar = db.Column(db.String(200), default=None)
    articles = db.relationship('Article', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    likes = db.relationship('Like', backref='user', lazy='dynamic')
    wallet_balance = db.Column(db.Integer, default=0)  # 文币余额

    def set_password(self, password):
        self.password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()

    def check_password(self, password):
        return self.password_hash == hashlib.md5(password.encode('utf-8')).hexdigest()

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500))
    category = db.Column(db.String(100))
    tags = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_private = db.Column(db.Boolean, default=False)
    password = db.Column(db.String(100))
    require_vip = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    
    comments = db.relationship('Comment', backref='article', lazy='dynamic')
    likes = db.relationship('Like', backref='article', lazy='dynamic')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NetworkStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    latency = db.Column(db.Float)
    throughput = db.Column(db.Float)
    active_connections = db.Column(db.Integer)