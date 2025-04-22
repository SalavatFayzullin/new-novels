from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from sqlalchemy import func, Table, Column, Integer, ForeignKey

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Define Novel-Genre association table
novel_genres = db.Table('novel_genres',
    db.Column('novel_id', db.Integer, db.ForeignKey('novel.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    novels = db.relationship('Novel', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    ratings = db.relationship('Rating', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    def __repr__(self):
        return f"Genre('{self.name}')"

class Novel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    synopsis = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    icon = db.Column(db.String(100), nullable=True, default='default_icon.png')
    comments = db.relationship('Comment', backref='novel', lazy=True, cascade='all, delete-orphan')
    ratings = db.relationship('Rating', backref='novel', lazy=True, cascade='all, delete-orphan')
    genres = db.relationship('Genre', secondary=novel_genres, lazy='subquery',
                            backref=db.backref('novels', lazy=True))
    
    @property
    def average_rating(self):
        result = db.session.query(func.avg(Rating.value)).filter(Rating.novel_id == self.id).first()
        return round(result[0] or 0, 1)
    
    @property
    def rating_count(self):
        return Rating.query.filter_by(novel_id=self.id).count()

    def __repr__(self):
        return f"Novel('{self.title}', '{self.date_posted}')"

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    novel_id = db.Column(db.Integer, db.ForeignKey('novel.id'), nullable=False)

    def __repr__(self):
        return f"Comment('{self.content[:20]}...', '{self.date_posted}')"

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)  # 1-10 stars
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    novel_id = db.Column(db.Integer, db.ForeignKey('novel.id'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'novel_id', name='unique_user_novel_rating'),)

    def __repr__(self):
        return f"Rating({self.value}, '{self.date_posted}')"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@app.route('/home')
@login_required
def home():
    novels = Novel.query.order_by(Novel.date_posted.desc()).all()
    return render_template('home.html', novels=novels)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check username and password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        username_exists = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first()
        
        if username_exists:
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
        
        if email_exists:
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/write', methods=['GET', 'POST'])
@login_required
def write_novel():
    genres = Genre.query.all()
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        synopsis = request.form.get('synopsis')
        genre_ids = request.form.getlist('genres')
        
        if not title or not content:
            flash('Title and content are required!', 'danger')
            return redirect(url_for('write_novel'))
        
        # Default icon
        icon_filename = 'default_icon.png'
        
        # Check if an icon was uploaded
        if 'icon' in request.files:
            icon = request.files['icon']
            if icon and icon.filename != '' and allowed_file(icon.filename):
                # Secure the filename and save the file
                filename = secure_filename(icon.filename)
                # Use timestamp to make filename unique
                icon_filename = f"{datetime.utcnow().timestamp():.0f}_{filename}"
                icon.save(os.path.join(app.config['UPLOAD_FOLDER'], icon_filename))
        
        novel = Novel(title=title, content=content, synopsis=synopsis, author=current_user, icon=icon_filename)
        
        # Add selected genres
        if genre_ids:
            selected_genres = Genre.query.filter(Genre.id.in_(genre_ids)).all()
            for genre in selected_genres:
                novel.genres.append(genre)
        
        db.session.add(novel)
        db.session.commit()
        
        flash('Your novel has been published!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('write.html', genres=genres)

@app.route('/profile')
@login_required
def profile():
    novels = Novel.query.filter_by(user_id=current_user.id).order_by(Novel.date_posted.desc()).all()
    return render_template('profile.html', novels=novels)

@app.route('/novel/<int:novel_id>')
def novel(novel_id):
    novel = Novel.query.get_or_404(novel_id)
    comments = Comment.query.filter_by(novel_id=novel_id).order_by(Comment.date_posted.desc()).all()
    user_rating = None
    if current_user.is_authenticated:
        user_rating = Rating.query.filter_by(novel_id=novel_id, user_id=current_user.id).first()
    
    # Get related novels (same author or similar genres)
    related_by_author = Novel.query.filter(Novel.user_id == novel.user_id, Novel.id != novel.id).limit(3).all()
    
    return render_template('novel.html', novel=novel, comments=comments, user_rating=user_rating, related_novels=related_by_author)

@app.route('/novel/<int:novel_id>/comment', methods=['POST'])
@login_required
def add_comment(novel_id):
    novel = Novel.query.get_or_404(novel_id)
    comment_content = request.form.get('comment')
    
    if comment_content:
        comment = Comment(content=comment_content, novel=novel, author=current_user)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added!', 'success')
    
    return redirect(url_for('novel', novel_id=novel.id))

@app.route('/novel/<int:novel_id>/rate', methods=['POST'])
@login_required
def rate_novel(novel_id):
    novel = Novel.query.get_or_404(novel_id)
    rating_value = int(request.form.get('rating'))
    
    if rating_value < 1 or rating_value > 10:
        flash('Rating must be between 1 and 10', 'danger')
        return redirect(url_for('novel', novel_id=novel.id))
    
    existing_rating = Rating.query.filter_by(novel_id=novel_id, user_id=current_user.id).first()
    
    if existing_rating:
        existing_rating.value = rating_value
        flash('Your rating has been updated!', 'success')
    else:
        rating = Rating(value=rating_value, novel=novel, user=current_user)
        db.session.add(rating)
        flash('Your rating has been added!', 'success')
    
    db.session.commit()
    return redirect(url_for('novel', novel_id=novel.id))

@app.route('/api/novel/<int:novel_id>/rate', methods=['POST'])
@login_required
def api_rate_novel(novel_id):
    novel = Novel.query.get_or_404(novel_id)
    data = request.get_json()
    rating_value = int(data.get('rating'))
    
    if rating_value < 1 or rating_value > 10:
        return jsonify({'success': False, 'error': 'Rating must be between 1 and 10'}), 400
    
    existing_rating = Rating.query.filter_by(novel_id=novel_id, user_id=current_user.id).first()
    
    if existing_rating:
        existing_rating.value = rating_value
    else:
        rating = Rating(value=rating_value, novel=novel, user=current_user)
        db.session.add(rating)
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'average_rating': novel.average_rating,
        'rating_count': novel.rating_count
    })

# Create default genres if they don't exist
def create_default_genres():
    default_genres = [
        'Fantasy', 'Science Fiction', 'Mystery', 'Thriller', 
        'Romance', 'Horror', 'Historical Fiction', 'Young Adult',
        'Children\'s', 'Biography', 'Memoir', 'Autobiography',
        'Self-help', 'Business', 'Travel', 'Poetry', 'Drama',
        'Adventure', 'Dystopian', 'Humor'
    ]
    
    for genre_name in default_genres:
        if not Genre.query.filter_by(name=genre_name).first():
            genre = Genre(name=genre_name)
            db.session.add(genre)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_genres()
    app.run(debug=True) 