import sqlite3
from datetime import datetime
import hashlib
import os

# 数据库文件路径
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'simple_blog.db')

def get_db():
    """获取数据库连接"""
    if not os.path.exists(os.path.dirname(DATABASE_PATH)):
        os.makedirs(os.path.dirname(DATABASE_PATH))
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_vip BOOLEAN DEFAULT 0,
        avatar TEXT,
        wallet_balance INTEGER DEFAULT 0
    )
    ''')
    
    # 创建文章表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        summary TEXT,
        category TEXT,
        tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER NOT NULL,
        is_private BOOLEAN DEFAULT 0,
        password TEXT,
        require_vip BOOLEAN DEFAULT 0,
        view_count INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # 创建评论表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER NOT NULL,
        article_id INTEGER NOT NULL,
        parent_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (article_id) REFERENCES articles (id),
        FOREIGN KEY (parent_id) REFERENCES comments (id)
    )
    ''')
    
    # 创建点赞表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        article_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (article_id) REFERENCES articles (id)
    )
    ''')
    
    # 创建网络统计表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS network_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        latency REAL,
        throughput REAL,
        active_connections INTEGER
    )
    ''')
    
    # 检查是否存在admin用户，不存在则创建
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        admin_password_hash = hashlib.md5('admin123'.encode('utf-8')).hexdigest()
        cursor.execute('''
        INSERT INTO users (username, email, password_hash, is_vip)
        VALUES (?, ?, ?, ?)
        ''', ('admin', 'admin@example.com', admin_password_hash, 1))
        
        # 创建示例文章
        cursor.execute('''
        INSERT INTO articles (title, content, summary, category, tags, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', ('欢迎使用博客系统', '这是一个基于Flask开发的博客系统，支持文章发布、评论、点赞等功能。', 
               '博客系统介绍', '技术', '博客,Flask,Python', 1))
    
    conn.commit()
    conn.close()

class User:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.username = kwargs.get('username')
        self.email = kwargs.get('email')
        self.password_hash = kwargs.get('password_hash')
        self.created_at = kwargs.get('created_at')
        self.is_vip = bool(kwargs.get('is_vip', 0))
        self.avatar = kwargs.get('avatar')
        self.wallet_balance = kwargs.get('wallet_balance', 0)
    
    @staticmethod
    def get(username=None, user_id=None):
        conn = get_db()
        cursor = conn.cursor()
        
        if username:
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        elif user_id:
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        else:
            conn.close()
            return None
            
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(**dict(row))
        return None
    
    @staticmethod
    def create(username, email, password):
        conn = get_db()
        cursor = conn.cursor()
        
        password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        
        try:
            cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
            ''', (username, email, password_hash))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return User.get(user_id=user_id)
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def set_password(self, password):
        self.password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', 
                      (self.password_hash, self.id))
        conn.commit()
        conn.close()
    
    def check_password(self, password):
        return self.password_hash == hashlib.md5(password.encode('utf-8')).hexdigest()
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at,
            'is_vip': self.is_vip,
            'avatar': self.avatar,
            'wallet_balance': self.wallet_balance
        }

class Article:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.title = kwargs.get('title')
        self.content = kwargs.get('content')
        self.summary = kwargs.get('summary')
        self.category = kwargs.get('category')
        self.tags = kwargs.get('tags')
        self.created_at = kwargs.get('created_at')
        self.updated_at = kwargs.get('updated_at')
        self.user_id = kwargs.get('user_id')
        self.is_private = bool(kwargs.get('is_private', 0))
        self.password = kwargs.get('password')
        self.require_vip = bool(kwargs.get('require_vip', 0))
        self.view_count = kwargs.get('view_count', 0)
    
    @staticmethod
    def get(article_id=None, user_id=None, is_private=None, limit=None, offset=None):
        conn = get_db()
        cursor = conn.cursor()
        
        query = 'SELECT a.*, u.username as author_username FROM articles a JOIN users u ON a.user_id = u.id WHERE 1=1'
        params = []
        
        if article_id:
            query += ' AND a.id = ?'
            params.append(article_id)
        
        if user_id:
            query += ' AND a.user_id = ?'
            params.append(user_id)
            
        if is_private is not None:
            query += ' AND a.is_private = ?'
            params.append(int(is_private))
        
        query += ' ORDER BY a.created_at DESC'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
            
        if offset:
            query += ' OFFSET ?'
            params.append(offset)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [Article(**dict(row)) for row in rows]
    
    @staticmethod
    def create(title, content, user_id, **kwargs):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO articles (title, content, user_id, summary, category, tags, is_private, password, require_vip)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, content, user_id, kwargs.get('summary'), kwargs.get('category'), 
               kwargs.get('tags'), int(kwargs.get('is_private', 0)), kwargs.get('password'), 
               int(kwargs.get('require_vip', 0))))
        
        article_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return Article.get(article_id=article_id)[0]
    
    def increment_view_count(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE articles SET view_count = view_count + 1 WHERE id = ?', (self.id,))
        conn.commit()
        conn.close()
        self.view_count += 1
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'category': self.category,
            'tags': self.tags,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'user_id': self.user_id,
            'is_private': self.is_private,
            'password': self.password,
            'require_vip': self.require_vip,
            'view_count': self.view_count
        }

class Comment:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.content = kwargs.get('content')
        self.created_at = kwargs.get('created_at')
        self.user_id = kwargs.get('user_id')
        self.article_id = kwargs.get('article_id')
        self.parent_id = kwargs.get('parent_id')
    
    @staticmethod
    def get(article_id=None, parent_id=None):
        conn = get_db()
        cursor = conn.cursor()
        
        query = 'SELECT c.*, u.username as author_username FROM comments c JOIN users u ON c.user_id = u.id WHERE 1=1'
        params = []
        
        if article_id:
            query += ' AND c.article_id = ?'
            params.append(article_id)
            
        if parent_id is not None:
            if parent_id:
                query += ' AND c.parent_id = ?'
            else:
                query += ' AND c.parent_id IS NULL'
            params.append(parent_id)
        
        query += ' ORDER BY c.created_at DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [Comment(**dict(row)) for row in rows]
    
    @staticmethod
    def create(content, user_id, article_id, parent_id=None):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO comments (content, user_id, article_id, parent_id)
        VALUES (?, ?, ?, ?)
        ''', (content, user_id, article_id, parent_id))
        
        comment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return Comment.get(article_id=article_id)[0]  # 简化，返回第一个评论
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'created_at': self.created_at,
            'user_id': self.user_id,
            'article_id': self.article_id,
            'parent_id': self.parent_id
        }

class Like:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.user_id = kwargs.get('user_id')
        self.article_id = kwargs.get('article_id')
        self.created_at = kwargs.get('created_at')
    
    @staticmethod
    def get(user_id=None, article_id=None):
        conn = get_db()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM likes WHERE 1=1'
        params = []
        
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
            
        if article_id:
            query += ' AND article_id = ?'
            params.append(article_id)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [Like(**dict(row)) for row in rows]
    
    @staticmethod
    def create(user_id, article_id):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO likes (user_id, article_id)
        VALUES (?, ?)
        ''', (user_id, article_id))
        
        like_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return Like.get(user_id=user_id, article_id=article_id)[0]
    
    @staticmethod
    def delete(user_id, article_id):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM likes WHERE user_id = ? AND article_id = ?', (user_id, article_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def count(article_id):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM likes WHERE article_id = ?', (article_id,))
        row = cursor.fetchone()
        conn.close()
        
        return row['count'] if row else 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'article_id': self.article_id,
            'created_at': self.created_at
        }

class NetworkStats:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.timestamp = kwargs.get('timestamp')
        self.latency = kwargs.get('latency')
        self.throughput = kwargs.get('throughput')
        self.active_connections = kwargs.get('active_connections')
    
    @staticmethod
    def create(latency, throughput, active_connections):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO network_stats (latency, throughput, active_connections)
        VALUES (?, ?, ?)
        ''', (latency, throughput, active_connections))
        
        stats_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return NetworkStats.get(stats_id=stats_id)[0]
    
    @staticmethod
    def get(limit=None):
        conn = get_db()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM network_stats ORDER BY timestamp DESC'
        params = []
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [NetworkStats(**dict(row)) for row in rows]
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'latency': self.latency,
            'throughput': self.throughput,
            'active_connections': self.active_connections
        }