from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from config import Config

from sqlalchemy import or_ 
from models import db, User, Article, Comment, Like, NetworkStats
from utils.decorators import login_required, vip_required
from utils.network_monitor import NetworkMonitor
from datetime import datetime
import os
import random
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

monitor = NetworkMonitor(app)



@app.before_request
def before_request():
    if request.endpoint and request.endpoint != 'static':
        monitor.record_request()

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    articles = Article.query.filter_by(is_private=False).order_by(
        Article.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    popular_articles = Article.query.filter_by(is_private=False).order_by(
        Article.view_count.desc()
    ).limit(5).all()
    
    categories = db.session.query(
        Article.category, db.func.count(Article.id)
    ).filter_by(is_private=False).group_by(Article.category).all()
    
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
            
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        default_dir = "C:/Users/17906/Desktop/blog_system/static/images/默认图像"
        files = os.listdir(default_dir)
        images = [f for f in files if f.endswith(('.jpg', '.png', '.jpeg'))]
        if images:
            user.avatar = f"images/默认图像/{random.choice(images)}"
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = bool(request.form.get('remember'))
        
        user = User.query.filter_by(username=username).first()
        
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
    article = Article.query.get_or_404(article_id)
    
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
    
    article.view_count += 1
    db.session.commit()
    
    comments = Comment.query.filter_by(article_id=article_id, parent_id=None).order_by(
        Comment.created_at.desc()
    ).all()
    
    like_count = Like.query.filter_by(article_id=article_id).count()
    user_liked = False
    if 'user_id' in session:
        user_liked = Like.query.filter_by(
            user_id=session['user_id'], 
            article_id=article_id
        ).first() is not None
    
    return render_template('article.html', 
                         article=article, 
                         comments=comments,
                         like_count=like_count,
                         user_liked=user_liked)

@app.route('/write', methods=['GET', 'POST'])
@login_required
def write_article():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        tags = request.form['tags']
        summary = request.form.get('summary', '')
        
        is_private = bool(request.form.get('is_private'))
        require_vip = bool(request.form.get('require_vip'))
        password = request.form.get('password', '')
        
        article = Article(
            title=title,
            content=content,
            category=category,
            tags=tags,
            summary=summary,
            user_id=session['user_id'],
            is_private=is_private,
            require_vip=require_vip,
            password=password
        )
        
        db.session.add(article)
        db.session.commit()
        
        flash('文章发布成功')
        return redirect(url_for('article_detail', article_id=article.id))
        
    return render_template('write_article.html')

@app.route('/search')
def search():
    keyword = request.args.get('q', '')
    category = request.args.get('category', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Article.query.filter_by(is_private=False)
    
    if keyword:
        query = query.filter(
            or_(
                Article.title.contains(keyword),
                Article.content.contains(keyword),
                Article.tags.contains(keyword)
            )
        )
        
    if category:
        query = query.filter(Article.category == category)
        
    articles = query.order_by(Article.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # 固定分类列表（与写文章的分类完全一致）
    fixed_categories = ["技术", "生活", "学习", "工作", "其他"]
    # 构建包含分类名称和对应文章数的列表
    categories = []
    for cate in fixed_categories:
        count = Article.query.filter_by(category=cate, is_private=False).count()
        categories.append((cate, count))
    
    return render_template('search.html', 
                         articles=articles, 
                         keyword=keyword,
                         category=category,
                         categories=categories)  # 传递固定分类数据


@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    articles = Article.query.filter_by(user_id=user.id, is_private=False).order_by(
        Article.created_at.desc()
    ).limit(10).all()
    
    return render_template('profile.html', user=user, articles=articles)

@app.route('/comment', methods=['POST'])
@login_required
def add_comment():
    article_id = request.form['article_id']
    content = request.form['content']
    parent_id = request.form.get('parent_id')
    
    if not content.strip():
        flash('评论内容不能为空')
        return redirect(url_for('article_detail', article_id=article_id))
    
    comment = Comment(
        content=content,
        user_id=session['user_id'],
        article_id=article_id,
        parent_id=parent_id if parent_id else None
    )
    
    db.session.add(comment)
    db.session.commit()
    
    flash('评论成功')
    return redirect(url_for('article_detail', article_id=article_id))

@app.route('/like', methods=['POST'])
@login_required
def like_article():
    article_id = request.form['article_id']
    
    existing_like = Like.query.filter_by(
        user_id=session['user_id'], 
        article_id=article_id
    ).first()
    
    if existing_like:
        db.session.delete(existing_like)
        action = 'unlike'
    else:
        like = Like(user_id=session['user_id'], article_id=article_id)
        db.session.add(like)
        action = 'like'
    
    db.session.commit()
    
    like_count = Like.query.filter_by(article_id=article_id).count()
    
    return jsonify({
        'action': action,
        'like_count': like_count
    })

@app.route('/network/stats')
@login_required
def network_stats():
    stats = NetworkStats.query.order_by(NetworkStats.timestamp.desc()).limit(100).all()
    
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
@login_required
def vip_purchase():
    user = User.query.get(session['user_id'])
    return render_template('vip_purchase.html', user=user)


@app.route('/vip/upgrade', methods=['POST'])
@login_required
def vip_upgrade():
    user = User.query.get(session['user_id'])
    user.is_vip = True
    db.session.commit()
    
    session['is_vip'] = True
    flash('VIP升级成功！')
    return redirect(url_for('profile', username=user.username))

def init_db():
    with app.app_context():
        db.create_all()
        
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@example.com')
            admin.set_password('admin123')
            admin.is_vip = True
            db.session.add(admin)
            
            article = Article(
                title='欢迎使用博客系统',
                content='这是一个基于Flask开发的博客系统，支持文章发布、评论、点赞等功能。',
                summary='博客系统介绍',
                category='技术',
                tags='博客,Flask,Python',
                user_id=1
            )
            db.session.add(article)
            db.session.commit()

@app.route('/change_avatar', methods=['GET', 'POST'])
@login_required
def change_avatar():
    default_dir = "C:/Users/17906/Desktop/blog_system/static/images/默认图像"
    files = os.listdir(default_dir)

    images = [f"images/默认图像/{f}" for f in files if f.endswith(('.jpg', '.png', '.jpeg'))]

    if request.method == 'POST':
        avatar = request.form['avatar']
        user = User.query.get(session['user_id'])
        user.avatar = avatar
        db.session.commit()
        flash("头像已更新")
        return redirect(url_for("profile", username=user.username))

    return render_template("change_avatar.html", images=images)

@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
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

    user = User.query.get(session['user_id'])
    user.avatar = f"images/用户头像/{filename}"
    db.session.commit()

    flash("自定义头像上传成功")
    return redirect(url_for('profile', username=user.username))
@app.route("/wallet")
@login_required
def wallet():
    user = User.query.get(session['user_id'])
    return render_template("wallet.html", user=user)
@app.route("/wallet/recharge", methods=["POST"])
@login_required
def wallet_recharge():
    user = User.query.get(session['user_id'])
    money = int(request.form["money"])

    coins = money * 10   # 10 元 = 100 文币 → 1 : 10

    # 首次充值赠送 15%
    if user.wallet_balance == 0:
        bonus = int(coins * 0.15)
        coins += bonus
        flash(f"首次充值奖励 +{bonus} 文币！")

    user.wallet_balance += coins
    db.session.commit()

    # 检查是否是AJAX请求
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'coins': coins
        })
    
    flash(f"充值成功！获得 {coins} 文币")
    return redirect(url_for("wallet"))

@app.route("/qrcode/payment")
def qrcode_payment():
    if 'user_id' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
    
    money = int(request.args.get('money', 30))
    coins = int(request.args.get('coins', 300))
    total = int(request.args.get('total', 300))
    
    # 计算首充奖励
    bonus = 0
    user = User.query.get(session['user_id'])
    if user.wallet_balance == 0:
        bonus = total - coins
    
    # 生成订单ID（实际应用中应该更复杂）
    import uuid
    order_id = str(uuid.uuid4())
    
    return render_template("qrcode_payment.html", 
                         money=money, 
                         coins=coins, 
                         bonus=bonus,
                         total_coins=total,
                         order_id=order_id)

@app.route("/api/payment/status", methods=["POST"])
def api_payment_status():
    if 'user_id' not in session:
        return jsonify({'error': '请先登录'}), 401
    
    data = request.get_json()
    order_id = data.get('order_id')
    
    # 在实际应用中，这里应该查询支付系统验证订单状态
    # 这里模拟随机支付成功
    import random
    if random.random() > 0.7:  # 30%概率支付成功
        return jsonify({'status': 'completed'})
    else:
        return jsonify({'status': 'pending'})

@app.route("/vip/pay_with_wallet", methods=["POST"])
@login_required
def vip_pay_with_wallet():
    user = User.query.get(session['user_id'])

    if user.wallet_balance < 300:
        flash("文币余额不足，请先充值")
        return redirect(url_for("vip_purchase"))

    user.wallet_balance -= 300
    user.is_vip = True
    db.session.commit()

    session["is_vip"] = True

    flash("成功使用文币开通 VIP！")
    return redirect(url_for("profile", username=user.username))

if __name__ == '__main__':
    init_db()
    monitor.start_background_task()
    app.run(host='0.0.0.0', port=5000, debug=True)