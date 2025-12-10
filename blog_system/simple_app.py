from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime
import os
import random
import sys
import time
import threading

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入简化模型
from simple_models import init_db, User, Article, Comment, Like, NetworkStats

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# 模拟网络监控
class SimpleNetworkMonitor:
    def __init__(self):
        self.request_times = []
        self.active_connections = 0
        self.lock = threading.Lock()
        
    def record_request(self):
        with self.lock:
            current_time = time.time()
            self.request_times.append(current_time)
            self.active_connections += 1
            
            cutoff_time = current_time - 60
            self.request_times = [t for t in self.request_times if t > cutoff_time]
    
    def get_current_latency(self):
        if len(self.request_times) > 10:
            return 50 + (len(self.request_times) % 20)
        return 50
    
    def get_current_throughput(self):
        cutoff_time = time.time() - 60
        recent_requests = [t for t in self.request_times if t > cutoff_time]
        return len(recent_requests)
    
    def get_active_connections(self):
        return self.active_connections
    
    def start_background_task(self):
        def stats_collector():
            while True:
                time.sleep(60)
                NetworkStats.create(
                    self.get_current_latency(),
                    self.get_current_throughput(),
                    self.get_active_connections()
                )
        
        thread = threading.Thread(target=stats_collector)
        thread.daemon = True
        thread.start()

monitor = SimpleNetworkMonitor()

@app.before_request
def before_request():
    if request.endpoint and request.endpoint != 'static':
        monitor.record_request()

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取文章列表
    articles = Article.get(is_private=False, limit=per_page, offset=(page-1)*per_page)
    
    # 获取热门文章
    popular_articles = Article.get(is_private=False, limit=5)
    
    # 获取分类统计
    conn = simple_models.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT category, COUNT(*) as count 
        FROM articles 
        WHERE is_private = 0 
        GROUP BY category
    ''')
    categories = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', 
                         articles=articles,
                         popular_articles=popular_articles,
                         categories=categories)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('密码不一致')
            return redirect(url_for('register'))
        
        user = User.create(username, email, password)
        if not user:
            flash('用户名或邮箱已存在')
            return redirect(url_for('register'))
        
        flash('注册成功，请登录')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = bool(request.form.get('remember'))
        
        user = User.get(username=username)
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_vip'] = user.is_vip
            
            if remember:
                session.permanent = True
                
            flash('登录成功')
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('您已退出登录')
    return redirect(url_for('index'))

@app.route('/article/<int:article_id>')
def article_detail(article_id):
    articles = Article.get(article_id=article_id)
    if not articles:
        flash('文章不存在')
        return redirect(url_for('index'))
    
    article = articles[0]
    
    if article.is_private:
        if 'user_id' not in session:
            flash('请先登录查看此文章')
            return redirect(url_for('login'))
            
        if article.require_vip and not session.get('is_vip'):
            flash('此文章需要VIP权限')
            return redirect(url_for('vip_purchase'))
            
        if article.password:
            if not request.args.get('password'):
                return render_template('article_password.html', article=article)
            if request.args.get('password') != article.password:
                flash('密码错误')
                return render_template('article_password.html', article=article)
    
    article.increment_view_count()
    
    # 获取评论
    comments = Comment.get(article_id=article_id, parent_id=None)
    
    # 获取点赞数和用户点赞状态
    like_count = Like.count(article_id)
    user_liked = False
    if 'user_id' in session:
        user_likes = Like.get(user_id=session['user_id'], article_id=article_id)
        user_liked = len(user_likes) > 0
    
    # 获取作者信息
    author = User.get(user_id=article.user_id)
    
    return render_template('article.html', 
                         article=article, 
                         comments=comments,
                         like_count=like_count,
                         user_liked=user_liked,
                         author=author)

@app.route('/write', methods=['GET', 'POST'])
def write_article():
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        tags = request.form['tags']
        summary = request.form.get('summary', '')
        
        is_private = bool(request.form.get('is_private'))
        require_vip = bool(request.form.get('require_vip'))
        password = request.form.get('password', '')
        
        article = Article.create(
            title=title,
            content=content,
            user_id=session['user_id'],
            category=category,
            tags=tags,
            summary=summary,
            is_private=is_private,
            require_vip=require_vip,
            password=password
        )
        
        flash('文章发布成功')
        return redirect(url_for('article_detail', article_id=article.id))
        
    return render_template('write_article.html')

@app.route('/search')
def search():
    keyword = request.args.get('q', '')
    category = request.args.get('category', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 简化搜索实现
    conn = simple_models.get_db()
    cursor = conn.cursor()
    
    query = 'SELECT a.*, u.username as author_username FROM articles a JOIN users u ON a.user_id = u.id WHERE a.is_private = 0'
    params = []
    
    if keyword:
        query += ' AND (a.title LIKE ? OR a.content LIKE ? OR a.tags LIKE ?)'
        keyword_pattern = f'%{keyword}%'
        params.extend([keyword_pattern, keyword_pattern, keyword_pattern])
        
    if category:
        query += ' AND a.category = ?'
        params.append(category)
        
    query += ' ORDER BY a.created_at DESC LIMIT ? OFFSET ?'
    params.extend([per_page, (page-1)*per_page])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    articles = [Article(**dict(row)) for row in rows]
    
    # 获取分类统计
    cursor.execute('''
        SELECT category, COUNT(*) as count 
        FROM articles 
        WHERE is_private = 0 
        GROUP BY category
    ''')
    categories = cursor.fetchall()
    
    conn.close()
    
    return render_template('search.html', 
                         articles=articles, 
                         keyword=keyword,
                         category=category,
                         categories=categories)

@app.route('/profile/<username>')
def profile(username):
    user = User.get(username=username)
    if not user:
        flash('用户不存在')
        return redirect(url_for('index'))
    
    articles = Article.get(user_id=user.id, is_private=False, limit=10)
    
    return render_template('profile.html', user=user, articles=articles)

@app.route('/comment', methods=['POST'])
def add_comment():
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
        
    article_id = request.form['article_id']
    content = request.form['content']
    parent_id = request.form.get('parent_id')
    
    if not content.strip():
        flash('评论内容不能为空')
        return redirect(url_for('article_detail', article_id=article_id))
    
    Comment.create(
        content=content,
        user_id=session['user_id'],
        article_id=article_id,
        parent_id=parent_id if parent_id else None
    )
    
    flash('评论成功')
    return redirect(url_for('article_detail', article_id=article_id))

@app.route('/like', methods=['POST'])
def like_article():
    if 'user_id' not in session:
        return jsonify({'error': '请先登录'}), 401
        
    article_id = request.form['article_id']
    
    existing_likes = Like.get(user_id=session['user_id'], article_id=article_id)
    
    if existing_likes:
        Like.delete(session['user_id'], article_id)
        action = 'unlike'
    else:
        Like.create(session['user_id'], article_id)
        action = 'like'
    
    like_count = Like.count(article_id)
    
    return jsonify({
        'action': action,
        'like_count': like_count
    })

@app.route('/network/stats')
def network_stats():
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
        
    stats = NetworkStats.get(limit=100)
    
    current_stats = {
        'latency': monitor.get_current_latency(),
        'throughput': monitor.get_current_throughput(),
        'active_connections': monitor.get_active_connections(),
        'timestamp': datetime.utcnow()
    }
    
    return render_template('network_stats.html', 
                         stats=stats,
                         current_stats=current_stats)

@app.route('/api/network/current')
def api_network_current():
    return jsonify({
        'latency': monitor.get_current_latency(),
        'throughput': monitor.get_current_throughput(),
        'active_connections': monitor.get_active_connections(),
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/vip/purchase')
def vip_purchase():
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
        
    user = User.get(user_id=session['user_id'])
    return render_template('vip_purchase.html', user=user)

@app.route('/vip/upgrade', methods=['POST'])
def vip_upgrade():
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
        
    user = User.get(user_id=session['user_id'])
    # 简化实现，直接更新VIP状态
    conn = simple_models.get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_vip = 1 WHERE id = ?', (user.id,))
    conn.commit()
    conn.close()
    
    session['is_vip'] = True
    flash('VIP升级成功！')
    return redirect(url_for('profile', username=user.username))

@app.route('/change_avatar', methods=['GET', 'POST'])
def change_avatar():
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
        
    default_dir = "C:/Users/17906/Desktop/blog_system/static/images/默认图像"
    if os.path.exists(default_dir):
        files = os.listdir(default_dir)
        images = [f"images/默认图像/{f}" for f in files if f.endswith(('.jpg', '.png', '.jpeg'))]
    else:
        images = []

    if request.method == 'POST':
        avatar = request.form['avatar']
        user = User.get(user_id=session['user_id'])
        
        # 更新头像
        conn = simple_models.get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET avatar = ? WHERE id = ?', (avatar, user.id))
        conn.commit()
        conn.close()
        
        flash("头像已更新")
        return redirect(url_for("profile", username=user.username))

    return render_template("change_avatar.html", images=images)

@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
        
    file = request.files['file']
    if not file:
        flash("请选择文件")
        return redirect(url_for('change_avatar'))

    filename = file.filename
    save_path = os.path.join(
        "C:/Users/17906/Desktop/blog_system/static/images/用户头像",
        filename
    )

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    file.save(save_path)

    user = User.get(user_id=session['user_id'])
    
    # 更新头像
    conn = simple_models.get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET avatar = ? WHERE id = ?', (f"images/用户头像/{filename}", user.id))
    conn.commit()
    conn.close()

    flash("自定义头像上传成功")
    return redirect(url_for('profile', username=user.username))

@app.route("/wallet")
def wallet():
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
        
    user = User.get(user_id=session['user_id'])
    return render_template("wallet.html", user=user)

@app.route("/wallet/recharge", methods=["POST"])
def wallet_recharge():
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
        
    user = User.get(user_id=session['user_id'])
    money = int(request.form["money"])
    coins = money * 10   # 10 元 = 100 文币 → 1 : 10

    # 首次充值赠送 15%
    if user.wallet_balance == 0:
        bonus = int(coins * 0.15)
        coins += bonus
        flash(f"首次充值奖励 +{bonus} 文币！")

    # 更新余额
    conn = simple_models.get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET wallet_balance = ? WHERE id = ?', (user.wallet_balance + coins, user.id))
    conn.commit()
    conn.close()

    flash(f"充值成功！获得 {coins} 文币")
    return redirect(url_for("wallet"))

@app.route("/vip/pay_with_wallet", methods=["POST"])
def vip_pay_with_wallet():
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
        
    user = User.get(user_id=session['user_id'])

    if user.wallet_balance < 300:
        flash("文币余额不足，请先充值")
        return redirect(url_for("vip_purchase"))

    # 更新余额和VIP状态
    conn = simple_models.get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET wallet_balance = ?, is_vip = ? WHERE id = ?', 
                  (user.wallet_balance - 300, 1, user.id))
    conn.commit()
    conn.close()

    session["is_vip"] = True

    flash("成功使用文币开通 VIP！")
    return redirect(url_for("profile", username=user.username))

def main():
    # 初始化数据库
    print("正在初始化数据库...")
    init_db()
    
    # 启动网络监控
    print("启动网络监控...")
    monitor.start_background_task()
    
    print("博客系统启动成功!")
    print("访问地址: http://localhost:5000")
    print("测试账号: admin / admin123")
    print("按 Ctrl+C 停止服务")
    
    # 启动应用
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()