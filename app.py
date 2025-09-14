from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__, template_folder='templates1')
app.secret_key = 'supersecretkey'
current_password = 'buzzly123'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, 'buzzly.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    link = db.Column(db.String(300))
    image = db.Column(db.String(300))
    likes = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='news', cascade='all, delete', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    query = request.args.get('search', '').lower()
    category = request.args.get('category', '')

    news = News.query.all()
    if query:
        news = [n for n in news if query in n.title.lower()]
    if category:
        news = [n for n in news if n.category == category]

    categories = sorted(set(n.category for n in News.query.all()))
    return render_template('index.html', news=news, categories=categories)

@app.route('/article/<int:id>', methods=['GET', 'POST'])
def view_article(id):
    article = News.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form['name']
        message = request.form['message']
        if name and message:
            comment = Comment(news_id=article.id, name=name, message=message)
            db.session.add(comment)
            db.session.commit()
            flash("💬 Comment added!")

    comments = Comment.query.filter_by(news_id=id).order_by(Comment.created_at.desc()).all()
    return render_template('article.html', article=article, comments=comments)

@app.route('/add', methods=['GET', 'POST'])
def add_news():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        content = request.form['content']
        link = request.form['link']

        image_file = request.files.get('image')
        image_filename = None
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            image_filename = filename

        new_article = News(
            title=title,
            category=category,
            content=content,
            link=link,
            image=image_filename
        )
        db.session.add(new_article)
        db.session.commit()

        flash("📰 News article added with image!")
        return redirect(url_for('index'))

    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_article(id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    article = News.query.get_or_404(id)

    if request.method == 'POST':
        article.title = request.form['title']
        article.category = request.form['category']
        article.content = request.form['content']
        article.link = request.form['link']

        db.session.commit()
        flash("✅ Article updated successfully!")
        return redirect(url_for('index'))

    return render_template('edit.html', article=article)

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_article(id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    article = News.query.get_or_404(id)

    if request.method == 'POST':
        password = request.form['password']
        if password == current_password:
            db.session.delete(article)
            db.session.commit()
            flash("🗑 Article deleted!")
            return redirect(url_for('index'))
        else:
            flash("❌ Incorrect password.")

    return render_template('confirm_delete.html', article=article)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == current_password:
            session['logged_in'] = True
            session['is_admin'] = True
            session['username'] = username
            flash("🔓 Logged in successfully!")
            return redirect(url_for('index'))
        else:
            flash("Invalid login")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("🚪 Logged out!")
    return redirect(url_for('index'))

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    global current_password

    if not session.get('is_admin'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        old = request.form['old_password']
        new = request.form['new_password']
        confirm = request.form['confirm_password']

        if old != current_password:
            flash("❌ Old password is incorrect.")
        elif new != confirm:
            flash("❗ New passwords do not match.")
        elif not new.strip():
            flash("⚠️ New password cannot be empty.")
        else:
            current_password = new
            flash("✅ Password successfully updated.")
            return redirect(url_for('index'))

    return render_template('reset_password.html')

@app.route('/like/<int:article_id>', methods=['POST'])
def like_article(article_id):
    liked = session.get('liked_articles', [])
    if article_id not in liked:
        article = News.query.get_or_404(article_id)
        article.likes += 1
        db.session.commit()
        liked.append(article_id)
        session['liked_articles'] = liked

    return redirect(request.referrer or url_for('index'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    articles = News.query.order_by(News.id.desc()).all()
    return render_template('admin.html', articles=articles)

@app.route('/admin/comments/<int:article_id>', methods=['GET', 'POST'])
def manage_comments(article_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    article = News.query.get_or_404(article_id)

    if request.method == 'POST':
        comment_id = request.form.get('comment_id')
        comment = Comment.query.get(comment_id)
        if comment:
            db.session.delete(comment)
            db.session.commit()
            flash("🗑 Comment deleted!")

    comments = Comment.query.filter_by(news_id=article_id).order_by(Comment.created_at.desc()).all()
    return render_template('admin_comments.html', article=article, comments=comments)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        session['dark_mode'] = 'dark_mode' in request.form
        session['font_size'] = request.form.get('font_size', 'medium')
        session['high_contrast'] = 'high_contrast' in request.form
        session['theme_color'] = request.form.get('theme_color', 'default')
        flash("Settings saved successfully!", "success")
        return redirect(url_for('settings'))

    return render_template(
        'settings.html',
        dark_mode=session.get('dark_mode', False),
        font_size=session.get('font_size', 'medium'),
        high_contrast=session.get('high_contrast', False),
        theme_color=session.get('theme_color', 'default')
    )

@app.route("/categories")
def categories():
    category_list = ["Politics", "Business", "Technology", "Health", "Entertainment", "Sports", "Education", "Lifestyle"]
    return render_template("category.html", categories=category_list)

@app.route("/category/<name>")
def show_category(name):
    articles = News.query.filter_by(category=name.capitalize()).all()
    return render_template("index.html", news=articles, categories=[name.capitalize()])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
