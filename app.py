from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
import os, uuid, json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey-change-in-production-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///socialfeed.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# Mail
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_user'
app.config['MAIL_PASSWORD'] = 'your_pass'
app.config['MAIL_DEFAULT_SENDER'] = 'noreply@socialfeed.mg'

ALLOWED_IMAGE = {'png','jpg','jpeg','gif','webp'}
ALLOWED_VIDEO = {'mp4','webm','mov','avi'}
ALLOWED_AUDIO = {'mp3','wav','ogg','m4a'}

db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter.'
login_manager.login_message_category = 'warning'
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# ── MODELS ──────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    avatar = db.Column(db.String(300), default='')
    cover = db.Column(db.String(300), default='')
    bio = db.Column(db.String(500), default='')
    location = db.Column(db.String(100), default='')
    website = db.Column(db.String(200), default='')
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy=True, foreign_keys='Post.user_id')
    likes = db.relationship('Like', backref='user', lazy=True)
    bookmarks = db.relationship('Bookmark', backref='user', lazy=True)

    def set_password(self, p): self.password_hash = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.password_hash, p)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    media_url = db.Column(db.String(500), default='')
    media_type = db.Column(db.String(20), default='')  # image/video/audio/url
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.relationship('Like', backref='post', lazy=True)
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')
    bookmarks = db.relationship('Bookmark', backref='post', lazy=True)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author = db.relationship('User', backref='comments')

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    price = db.Column(db.Float, nullable=False)  # in Ariary
    image_url = db.Column(db.String(300))
    category = db.Column(db.String(50))
    badge = db.Column(db.String(30), default='')
    stock = db.Column(db.Integer, default=100)
    clicks = db.relationship('ProductClick', backref='product', lazy=True)
    cart_items = db.relationship('CartItem', backref='product', lazy=True)

class ProductClick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    source = db.Column(db.String(50), default='feed')  # feed / sidebar / banner / boutique
    clicked_at = db.Column(db.DateTime, default=datetime.utcnow)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default='en attente')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items_json = db.Column(db.Text, default='[]')
    user = db.relationship('User', backref='orders')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(300))
    link = db.Column(db.String(200), default='')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='notifications')

@login_manager.user_loader
def load_user(uid): return User.query.get(int(uid))

# ── HELPERS ──────────────────────────────────────────────────────────────────

def allowed_file(filename, allowed):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

def save_upload(file, subfolder):
    original = secure_filename(file.filename)
    ext = original.rsplit('.', 1)[-1].lower() if '.' in original else 'bin'
    fname = f"{uuid.uuid4().hex}.{ext}"
    folder = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, fname))
    return f"static/uploads/{subfolder}/{fname}"

def add_notification(user_id, content, link=''):
    n = Notification(user_id=user_id, content=content, link=link)
    db.session.add(n)

def format_ariary(amount):
    return f"Ar {amount:,.0f}".replace(',', ' ')

app.jinja_env.filters['ariary'] = format_ariary

def cart_count():
    if current_user.is_authenticated:
        return CartItem.query.filter_by(user_id=current_user.id).count()
    return 0

app.jinja_env.globals['cart_count'] = cart_count

def notif_count():
    if current_user.is_authenticated:
        return Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return 0

app.jinja_env.globals['notif_count'] = notif_count

# ── AUTH ─────────────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('feed'))
    if request.method == 'POST':
        u, e, p, c = (request.form.get(x,'').strip() for x in ['username','email','password','confirm_password'])
        if not all([u,e,p]): flash('Tous les champs sont requis.','danger')
        elif p != c: flash('Mots de passe différents.','danger')
        elif len(p)<6: flash('Mot de passe trop court (min 6).','danger')
        elif User.query.filter_by(email=e).first(): flash('Email déjà utilisé.','danger')
        elif User.query.filter_by(username=u).first(): flash("Nom d'utilisateur pris.",'danger')
        else:
            user = User(username=u, email=e)
            user.set_password(p)
            db.session.add(user)
            db.session.commit()
            flash('Compte créé ! Connectez-vous.','success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('feed'))
    if request.method == 'POST':
        e = request.form.get('email','').strip()
        p = request.form.get('password','')
        rem = request.form.get('remember') == 'on'
        user = User.query.filter_by(email=e).first()
        if user and user.check_password(p):
            login_user(user, remember=rem)
            flash(f'Bienvenue, {user.username} !','success')
            return redirect(request.args.get('next') or url_for('feed'))
        flash('Email ou mot de passe incorrect.','danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Déconnecté.','info')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        e = request.form.get('email','').strip()
        user = User.query.filter_by(email=e).first()
        if user:
            token = s.dumps(e, salt='pwd-reset')
            reset_url = url_for('reset_password', token=token, _external=True)
            try:
                msg = Message('Réinitialisation — SocialFeed Madagascar', recipients=[e])
                msg.html = f'<h2>Réinitialiser votre mot de passe</h2><p><a href="{reset_url}">Cliquez ici</a> (expire dans 1h)</p>'
                mail.send(msg)
            except: pass
        flash("Si cet email existe, un lien a été envoyé.",'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET','POST'])
def reset_password(token):
    try: email = s.loads(token, salt='pwd-reset', max_age=3600)
    except:
        flash('Lien invalide ou expiré.','danger')
        return redirect(url_for('forgot_password'))
    user = User.query.filter_by(email=email).first()
    if not user: return redirect(url_for('login'))
    if request.method == 'POST':
        p = request.form.get('password','')
        c = request.form.get('confirm_password','')
        if p != c: flash('Mots de passe différents.','danger')
        elif len(p)<6: flash('Trop court.','danger')
        else:
            user.set_password(p)
            db.session.commit()
            flash('Mot de passe réinitialisé !','success')
            return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)

# ── PROFILE ───────────────────────────────────────────────────────────────────

@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc()).all()
    total_likes = sum(len(p.likes) for p in posts)
    return render_template('profile.html', user=user, posts=posts, total_likes=total_likes)

@app.route('/profile/edit', methods=['GET','POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.username = request.form.get('username', current_user.username).strip()
        current_user.bio = request.form.get('bio','').strip()[:500]
        current_user.location = request.form.get('location','').strip()
        current_user.website = request.form.get('website','').strip()

        # Avatar upload
        av = request.files.get('avatar')
        if av and av.filename and av.filename != '' and allowed_file(av.filename, ALLOWED_IMAGE):
            current_user.avatar = '/' + save_upload(av, 'images')

        # Cover upload
        cv = request.files.get('cover')
        if cv and cv.filename and cv.filename != '' and allowed_file(cv.filename, ALLOWED_IMAGE):
            current_user.cover = '/' + save_upload(cv, 'images')

        # Password change
        old_p = request.form.get('old_password','')
        new_p = request.form.get('new_password','')
        if old_p and new_p:
            if current_user.check_password(old_p):
                if len(new_p) >= 6:
                    current_user.set_password(new_p)
                    flash('Mot de passe modifié.','success')
                else:
                    flash('Nouveau mot de passe trop court.','danger')
            else:
                flash('Ancien mot de passe incorrect.','danger')

        db.session.commit()
        flash('Profil mis à jour !','success')
        return redirect(url_for('profile', user_id=current_user.id))
    return render_template('edit_profile.html')

# ── FEED ──────────────────────────────────────────────────────────────────────

@app.route('/')
@login_required
def feed():
    page = request.args.get('page',1,type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=6)
    products = Product.query.all()
    suggested_users = User.query.filter(User.id != current_user.id).limit(5).all()
    bookmarked_ids = {b.post_id for b in current_user.bookmarks}
    return render_template('feed.html', posts=posts, products=products,
                           suggested_users=suggested_users, bookmarked_ids=bookmarked_ids)

@app.route('/post/new', methods=['POST'])
@login_required
def new_post():
    content = request.form.get('content','').strip()
    if not content:
        flash('Contenu requis.','danger')
        return redirect(url_for('feed'))

    media_url = ''
    media_type = ''
    file = request.files.get('media')

    if file and file.filename and file.filename != '':
        fname = file.filename.lower()
        ext = fname.rsplit('.', 1)[-1] if '.' in fname else ''
        if ext in ALLOWED_IMAGE:
            media_url = '/' + save_upload(file, 'images')
            media_type = 'image'
        elif ext in ALLOWED_VIDEO:
            media_url = '/' + save_upload(file, 'videos')
            media_type = 'video'
        elif ext in ALLOWED_AUDIO:
            media_url = '/' + save_upload(file, 'audios')
            media_type = 'audio'
        else:
            flash('Format de fichier non supporté.','danger')
            return redirect(url_for('feed'))
    else:
        url_val = request.form.get('media_url','').strip()
        if url_val:
            media_url = url_val
            media_type = 'url'

    post = Post(content=content, media_url=media_url, media_type=media_type, user_id=current_user.id)
    db.session.add(post)
    db.session.commit()
    flash('Publication créée !','success')
    return redirect(url_for('feed'))

@app.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    ex = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if ex:
        db.session.delete(ex)
    else:
        db.session.add(Like(user_id=current_user.id, post_id=post_id))
        if post.user_id != current_user.id:
            add_notification(post.user_id,
                f'❤️ {current_user.username} a aimé votre publication',
                url_for('feed', _anchor=f'post-{post_id}'))
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        liked = not bool(ex)
        return jsonify({'likes': len(post.likes), 'liked': liked})
    return redirect(request.referrer or url_for('feed'))

@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def comment_post(post_id):
    content = request.form.get('content','').strip()
    if content:
        post = Post.query.get_or_404(post_id)
        c = Comment(content=content, user_id=current_user.id, post_id=post_id)
        db.session.add(c)
        if post.user_id != current_user.id:
            add_notification(post.user_id,
                f'💬 {current_user.username} a commenté votre publication',
                url_for('feed'))
        db.session.commit()
    return redirect(request.referrer or url_for('feed'))

@app.route('/post/<int:post_id>/bookmark', methods=['POST'])
@login_required
def bookmark_post(post_id):
    ex = Bookmark.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if ex:
        db.session.delete(ex)
        msg = 'Signet retiré.'
    else:
        db.session.add(Bookmark(user_id=current_user.id, post_id=post_id))
        msg = 'Publication sauvegardée !'
    db.session.commit()
    flash(msg,'info')
    return redirect(request.referrer or url_for('feed'))

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('Non autorisé.','danger')
        return redirect(url_for('feed'))
    db.session.delete(post)
    db.session.commit()
    flash('Publication supprimée.','info')
    return redirect(request.referrer or url_for('feed'))

@app.route('/bookmarks')
@login_required
def bookmarks():
    bms = Bookmark.query.filter_by(user_id=current_user.id).order_by(Bookmark.id.desc()).all()
    posts = [b.post for b in bms]
    bookmarked_ids = {b.post_id for b in current_user.bookmarks}
    return render_template('bookmarks.html', posts=posts, bookmarked_ids=bookmarked_ids)

@app.route('/search')
@login_required
def search():
    q = request.args.get('q','').strip()
    posts, users, prods = [], [], []
    if q:
        posts = Post.query.filter(Post.content.ilike(f'%{q}%')).order_by(Post.created_at.desc()).limit(20).all()
        users = User.query.filter(User.username.ilike(f'%{q}%')).limit(10).all()
        prods = Product.query.filter(Product.name.ilike(f'%{q}%') | Product.description.ilike(f'%{q}%')).limit(10).all()
    bookmarked_ids = {b.post_id for b in current_user.bookmarks}
    return render_template('search.html', q=q, posts=posts, users=users,
                           products=prods, bookmarked_ids=bookmarked_ids)

# ── NOTIFICATIONS ──────────────────────────────────────────────────────────────

@app.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(50).all()
    for n in notifs:
        n.is_read = True
    db.session.commit()
    return render_template('notifications.html', notifications=notifs)

# ── PRODUCTS & CART ───────────────────────────────────────────────────────────

@app.route('/products')
@login_required
def products():
    cat = request.args.get('category','')
    q = Product.query
    if cat: q = q.filter_by(category=cat)
    prods = q.all()
    cats = [c[0] for c in db.session.query(Product.category).distinct().all()]
    return render_template('products.html', products=prods, categories=cats, selected_category=cat)

@app.route('/product/<int:product_id>/click', methods=['POST'])
@login_required
def track_click(product_id):
    source = request.form.get('source','feed')
    pc = ProductClick(product_id=product_id, user_id=current_user.id, source=source)
    db.session.add(pc)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/cart')
@login_required
def cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(i.product.price * i.quantity for i in items)
    return render_template('cart.html', items=items, total=total)

@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def cart_add(product_id):
    product = Product.query.get_or_404(product_id)
    source = request.form.get('source','feed')
    # Track click
    pc = ProductClick(product_id=product_id, user_id=current_user.id, source=source)
    db.session.add(pc)
    item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        item.quantity += 1
    else:
        db.session.add(CartItem(user_id=current_user.id, product_id=product_id, quantity=1))
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        count = CartItem.query.filter_by(user_id=current_user.id).count()
        return jsonify({'ok': True, 'count': count, 'name': product.name})
    flash(f'"{product.name}" ajouté au panier !','success')
    return redirect(request.referrer or url_for('products'))

@app.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def cart_update(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        return jsonify({'error': 'Non autorisé'}), 403
    action = request.form.get('action')
    if action == 'inc': item.quantity += 1
    elif action == 'dec':
        item.quantity -= 1
        if item.quantity <= 0:
            db.session.delete(item)
            db.session.commit()
            return jsonify({'removed': True, 'count': CartItem.query.filter_by(user_id=current_user.id).count()})
    db.session.commit()
    total_item = item.product.price * item.quantity
    total = sum(i.product.price * i.quantity for i in CartItem.query.filter_by(user_id=current_user.id).all())
    return jsonify({'quantity': item.quantity, 'total_item': total_item, 'total': total, 'count': CartItem.query.filter_by(user_id=current_user.id).count()})

@app.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def cart_remove(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('Non autorisé.','danger')
        return redirect(url_for('cart'))
    db.session.delete(item)
    db.session.commit()
    flash('Article retiré.','info')
    return redirect(url_for('cart'))

@app.route('/cart/checkout', methods=['POST'])
@login_required
def checkout():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash('Panier vide.','warning')
        return redirect(url_for('cart'))
    total = sum(i.product.price * i.quantity for i in items)
    items_data = [{'name': i.product.name, 'qty': i.quantity, 'price': i.product.price} for i in items]
    order = Order(user_id=current_user.id, total=total, items_json=json.dumps(items_data))
    db.session.add(order)
    for i in items:
        db.session.delete(i)
    add_notification(current_user.id, f'✅ Commande #{order.id} confirmée — Total : {format_ariary(total)}')
    db.session.commit()
    flash(f'Commande passée ! Total : {format_ariary(total)}','success')
    return redirect(url_for('orders'))

@app.route('/orders')
@login_required
def orders():
    my_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    for o in my_orders:
        o.items_parsed = json.loads(o.items_json)
    return render_template('orders.html', orders=my_orders)

# ── ADMIN DASHBOARD ───────────────────────────────────────────────────────────

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Accès refusé.','danger')
        return redirect(url_for('feed'))
    # Stats globales
    total_users = User.query.count()
    total_posts = Post.query.count()
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total)).scalar() or 0
    # Stats produits
    products = Product.query.all()
    prod_stats = []
    for p in products:
        clicks_total = len(p.clicks)
        clicks_by_source = {}
        for c in p.clicks:
            clicks_by_source[c.source] = clicks_by_source.get(c.source, 0) + 1
        unique_users = len(set(c.user_id for c in p.clicks if c.user_id))
        prod_stats.append({
            'product': p,
            'total_clicks': clicks_total,
            'unique_users': unique_users,
            'by_source': clicks_by_source,
            'in_carts': CartItem.query.filter_by(product_id=p.id).count(),
        })
    prod_stats.sort(key=lambda x: x['total_clicks'], reverse=True)
    # Recent clicks timeline
    recent_clicks = ProductClick.query.order_by(ProductClick.clicked_at.desc()).limit(20).all()
    users = User.query.order_by(User.created_at.desc()).all()
    all_orders = Order.query.order_by(Order.created_at.desc()).limit(20).all()
    for o in all_orders:
        o.items_parsed = json.loads(o.items_json)
    return render_template('admin.html',
        total_users=total_users, total_posts=total_posts,
        total_orders=total_orders, total_revenue=total_revenue,
        prod_stats=prod_stats, recent_clicks=recent_clicks,
        users=users, all_orders=all_orders)

@app.route('/admin/user/<int:uid>/toggle-admin', methods=['POST'])
@login_required
def toggle_admin(uid):
    if not current_user.is_admin: return redirect(url_for('feed'))
    u = User.query.get_or_404(uid)
    if u.id != current_user.id:
        u.is_admin = not u.is_admin
        db.session.commit()
        flash(f"{'Admin accordé' if u.is_admin else 'Admin retiré'} à {u.username}.",'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/product/new', methods=['POST'])
@login_required
def admin_new_product():
    if not current_user.is_admin: return redirect(url_for('feed'))
    p = Product(
        name=request.form.get('name'),
        description=request.form.get('description',''),
        price=float(request.form.get('price',0)),
        image_url=request.form.get('image_url',''),
        category=request.form.get('category','Général'),
        badge=request.form.get('badge',''),
        stock=int(request.form.get('stock',100))
    )
    db.session.add(p)
    db.session.commit()
    flash('Produit ajouté.','success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/product/<int:pid>/delete', methods=['POST'])
@login_required
def admin_delete_product(pid):
    if not current_user.is_admin: return redirect(url_for('feed'))
    p = Product.query.get_or_404(pid)
    ProductClick.query.filter_by(product_id=pid).delete()
    CartItem.query.filter_by(product_id=pid).delete()
    db.session.delete(p)
    db.session.commit()
    flash('Produit supprimé.','info')
    return redirect(url_for('admin_dashboard'))

# ── THEME ─────────────────────────────────────────────────────────────────────

@app.route('/theme/toggle', methods=['POST'])
def toggle_theme():
    current = session.get('theme','dark')
    session['theme'] = 'light' if current == 'dark' else 'dark'
    return jsonify({'theme': session['theme']})

@app.context_processor
def inject_theme():
    return {'theme': session.get('theme','dark')}

# ── SEED & INIT ────────────────────────────────────────────────────────────────

def seed():
    try:
        exists = User.query.first()
    except Exception:
        # Table incomplète ou absente — on laisse db.create_all() gérer
        return
    if exists:
        return

    users = [
        User(username='alice', email='alice@demo.mg', bio='Designer UI/UX passionnée 🎨', location='Antananarivo', is_admin=True,
             avatar='https://i.pravatar.cc/150?img=47'),
        User(username='bob', email='bob@demo.mg', bio='Dev full-stack & café addict ☕', location='Toamasina',
             avatar='https://i.pravatar.cc/150?img=12'),
        User(username='clara', email='clara@demo.mg', bio='Photographe & voyageuse 📸', location='Fianarantsoa',
             avatar='https://i.pravatar.cc/150?img=32'),
    ]
    for u in users: u.set_password('password123')
    db.session.add_all(users)
    db.session.flush()

    posts = [
        Post(content='🚀 Bienvenue sur SocialFeed Madagascar ! Partagez, découvrez, et achetez directement dans votre fil.', user_id=users[0].id),
        Post(content='Mon setup de dev du moment — double écran, café et musique lo-fi 🎵', media_url='https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=600', media_type='url', user_id=users[1].id),
        Post(content='Coucher de soleil depuis Ambohimanga ce soir 🌅', media_url='https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600', media_type='url', user_id=users[2].id),
        Post(content='Tips design : l\'espace blanc n\'est pas du vide — c\'est du souffle. ✨', user_id=users[0].id),
        Post(content='Premier test de l\'API IA en Python. 10 lignes de code, des résultats bluffants ! 🤖', user_id=users[1].id),
        Post(content='La ville de Tana vue du ciel 🏙️ Toujours aussi belle.', media_url='https://images.unsplash.com/photo-1523482580672-f109ba8cb9be?w=600', media_type='url', user_id=users[2].id),
    ]
    db.session.add_all(posts)

    products = [
        Product(name='Casque Sony WH-1000XM5', description='Réduction de bruit active, son spatial premium, 30h batterie', price=549000, category='Audio', badge='Populaire', image_url='https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400'),
        Product(name='Lampe Bureau LED Pro', description='Lumière ajustable 3 températures, chargeur USB-C intégré', price=89000, category='Bureau', badge='Nouveau', image_url='https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400'),
        Product(name='Clavier Mécanique RGB', description='Switches silent Cherry MX, rétroéclairage RGB personnalisable', price=189000, category='Informatique', badge='', image_url='https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?w=400'),
        Product(name='Sac à dos Tech Pro', description='Anti-vol, imperméable, port USB externe, 30L', price=129000, category='Accessoires', badge='Promo', image_url='https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400'),
        Product(name='Montre Galaxy Watch 6', description='GPS, cardiofréquencemètre, 7 jours autonomie, AMOLED', price=399000, category='Wearables', badge='Populaire', image_url='https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400'),
        Product(name='Enceinte JBL Charge 5', description='360°, waterproof IPX7, 20h autonomie, powerbank intégré', price=249000, category='Audio', badge='', image_url='https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400'),
        Product(name='Webcam 4K Logitech', description='4K Ultra HD, autofocus, micro stéréo, HDR', price=179000, category='Informatique', badge='Nouveau', image_url='https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?w=400'),
        Product(name='Tapis de souris XXL', description='900×400mm, surface lisse, base antidérapante', price=35000, category='Bureau', badge='', image_url='https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400'),
    ]
    db.session.add_all(products)
    db.session.commit()

    # Seed some demo clicks
    import random
    sources = ['feed','sidebar','banner','boutique']
    for prod in products:
        for _ in range(random.randint(3,25)):
            pc = ProductClick(product_id=prod.id, user_id=random.choice([u.id for u in users]), source=random.choice(sources))
            db.session.add(pc)
    db.session.commit()

def migrate_db():
    """Ajoute les colonnes manquantes sans perdre les données existantes."""
    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), 'socialfeed.db')
    if not os.path.exists(db_path):
        return  # Nouvelle DB, rien à migrer

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Colonnes à ajouter si absentes : (table, colonne, définition SQL)
    migrations = [
        ('user', 'cover',    "ALTER TABLE user ADD COLUMN cover VARCHAR(300) DEFAULT ''"),
        ('user', 'location', "ALTER TABLE user ADD COLUMN location VARCHAR(100) DEFAULT ''"),
        ('user', 'website',  "ALTER TABLE user ADD COLUMN website VARCHAR(200) DEFAULT ''"),
        ('user', 'is_admin', "ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0"),
        ('post', 'media_url',"ALTER TABLE post ADD COLUMN media_url VARCHAR(500) DEFAULT ''"),
        ('post', 'media_type',"ALTER TABLE post ADD COLUMN media_type VARCHAR(20) DEFAULT ''"),
        ('post', 'image_url',""),  # ancienne colonne — on ne la supprime pas, juste ignorée
    ]

    for table, col, sql in migrations:
        if not sql:
            continue
        try:
            cur.execute(f"SELECT {col} FROM {table} LIMIT 1")
        except sqlite3.OperationalError:
            # Colonne absente → l'ajouter
            try:
                cur.execute(sql)
                print(f"[migrate] Colonne '{col}' ajoutée à '{table}'")
            except Exception as ex:
                print(f"[migrate] Erreur sur '{col}': {ex}")

    # Créer les nouvelles tables si elles n'existent pas encore
    new_tables = ['product_click', 'cart_item', 'order', 'notification', 'bookmark']
    existing = {row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    for t in new_tables:
        if t not in existing:
            print(f"[migrate] Table '{t}' sera créée par db.create_all()")

    conn.commit()
    conn.close()

with app.app_context():
    # Ensure upload directories exist
    for sub in ['images', 'videos', 'audios']:
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], sub), exist_ok=True)

    db_path = os.path.join(os.path.dirname(__file__), 'socialfeed.db')

    # Try to migrate existing DB first
    migrate_db()

    try:
        db.create_all()
        seed()
    except Exception as e:
        print(f"\n⚠️  Erreur de schéma détectée : {e}")
        print("→ Suppression de l'ancienne base et recréation automatique...\n")
        # Close all connections before deleting
        db.session.remove()
        db.engine.dispose()
        if os.path.exists(db_path):
            os.remove(db_path)
        # Recreate fresh
        db.create_all()
        seed()
        print("✅ Base de données recréée avec succès !\n")

if __name__ == '__main__':
    app.run(debug=True)
