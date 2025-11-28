from flask import Flask, request, jsonify, render_template, session, url_for, redirect
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from google.cloud import storage
from google.cloud.sql.connector import Connector, IPTypes
import pg8000
import os
import uuid
from datetime import datetime, timezone, timedelta
from google.oauth2 import service_account

#load environment variables
INSTANCE_CONNECTION_NAME = "single-archive-476003-d7:us-west1:snapclouddb"
DB_USER = "testuser"
DB_PASSWORD = "Thisisatest1*" 
DB_NAME = "snapclouddb"
GCP_PROJECT_ID = "single-archive-476003-d7"
SERVICE_ACCOUNT_KEY_FILE = 'service-account-key.json'


app = Flask(__name__)
CORS(app)

#app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///photos.db')
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.secret_key = os.environ.get('SECRET_KEY', 'test_secret_key')

USE_GCS = True #os.environ.get('USE_GCS', 'false').lower() == 'true'
GCS_BUCKET = True #os.environ.get('GCS_BUCKET', None)
bucket_name = "cloudsnap_bucket_upload"



#db = SQLAlchemy(app)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

#if not USE_GCS:
    #os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_connector():
    with Connector(refresh_strategy="lazy") as connector:
        conn = connector.connect(
            INSTANCE_CONNECTION_NAME,
            "pg8000",
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
            ip_type=IPTypes.PUBLIC,
            enable_iam_auth=True
        )
    return conn

app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql+pg8000://{DB_USER}@127.0.0.1:5432/{DB_NAME}"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "creator": init_connector,
    "pool_size": 5,
    "max_overflow": 2,
    "pool_timeout": 30,
    "pool_recycle": 1800,
    }

db = SQLAlchemy(app)

# Association table for Likes (many-to-many: user <-> moment)
likes_table = db.Table('likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('moment_id', db.Integer, db.ForeignKey('moment.id'), primary_key=True)
)

class Moment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    photo_url = db.Column(db.String(500), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    author = db.relationship('User', back_populates='moments')
    comments = db.relationship('Comment', backref='moment', lazy='dynamic', cascade="all, delete-orphan")
    likes = db.relationship('User', secondary=likes_table, back_populates='liked_moments')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(300), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    moment_id = db.Column(db.Integer, db.ForeignKey('moment.id'), nullable=False)
    
    author = db.relationship('User', back_populates='comments')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    avatar_url = db.Column(db.String(500), nullable=True)
    photos = db.relationship('Photo', backref='owner', lazy=True)
    moments = db.relationship('Moment', back_populates='author', lazy='dynamic', cascade="all, delete-orphan")
    comments = db.relationship('Comment', back_populates='author', lazy='dynamic', cascade="all, delete-orphan")
    liked_moments = db.relationship('Moment', secondary=likes_table, back_populates='likes', lazy='dynamic')

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    url = db.Column(db.String(500), nullable=True)  

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def upload_to_gcs(file, filename, bucket_name):
    """Upload a file to Google Cloud Storage and return its public URL."""
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY_FILE)
    client = storage.Client(project=GCP_PROJECT_ID, credentials=credentials)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_file(file, content_type=file.content_type)
    return blob.name

def generate_signed_url(filename, bucket_name):
    """Generates a v4 signed URL for a private GCS object."""
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY_FILE)
    client = storage.Client(project=GCP_PROJECT_ID, credentials=credentials)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(filename)

    # Set expiration time for the URL
    expiration = timedelta(hours=1)

    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=expiration,
        method="GET"
    )
    return signed_url

# ---------------------
# Routes
# ---------------------
@app.route('/')
def root():
    return redirect(url_for('login'))

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/profile')
@login_required
def profile():
    user = db.session.get(User, session['user_id'])
    photos_for_template = []
    for photo in user.photos:
        try:
            signed_url = generate_signed_url(photo.url, bucket_name)
            display_name = photo.filename.split('_', 1)[1] if '_' in photo.filename else photo.filename
            photos_for_template.append({
                'filename': display_name,
                'url': signed_url
            })
        except Exception as e:
            print(f"Error generating signed URL for {photo.url}: {e}")
    
    # Avatar URL
    avatar_url = None
    if user.avatar_url:
         try:
            avatar_url = generate_signed_url(user.avatar_url, bucket_name)
         except Exception as e:
            print(f"Error generating avatar URL: {e}")

    # Calculate Stats
    likes_count = user.liked_moments.count()
    albums_count = 0

    return render_template('profile.html', user=user, avatar_url=avatar_url, photos=photos_for_template, likes_count=likes_count, albums_count=albums_count)

@app.route('/api/update-profile', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json()
    new_password = data.get('password')
    
    if not new_password:
        return jsonify({'success': False, 'error': 'Password is required'}), 400
        
    if len(new_password) > 64:
         return jsonify({'success': False, 'error': 'Password is too long'}), 400

    user = db.session.get(User, session['user_id'])
    user.password = generate_password_hash(new_password)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/upload-avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    unique_name = f"avatar_{session['user_id']}_{uuid.uuid4()}_{secure_filename(file.filename)}"
    
    try:
        uploaded_filename = upload_to_gcs(file, unique_name, bucket_name)
    except Exception as e:
        return jsonify({'error': f'Failed to upload to GCS: {e}'}), 500

    user = db.session.get(User, session['user_id'])
    user.avatar_url = uploaded_filename
    db.session.commit()
    
    try:
        signed_url = generate_signed_url(uploaded_filename, bucket_name)
        return jsonify({'success': True, 'url': signed_url})
    except Exception as e:
         return jsonify({'error': f'Failed to generate URL: {e}'}), 500

@app.route('/upload')
@login_required
def upload():
    return render_template('upload.html')

@app.route('/albums')
@login_required
def albums():
    user = db.session.get(User, session['user_id']) 
    photos_for_template = []
    for photo in user.photos:
        try:
            signed_url = generate_signed_url(photo.url, bucket_name)
            photos_for_template.append({
                'filename': photo.filename,
                'url': signed_url
            })
        except Exception as e:
            print(f"Error generating signed URL for {photo.url}: {e}")

    return render_template('albums.html', photos=photos_for_template)

@app.route('/signup-form', methods=['POST'])
def signup_form():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'error': 'Missing username or password'}), 400
    
    if len(username) > 80:
        return jsonify({'success': False, 'error': 'Username must be under 80 characters'}), 400
    if len(password) > 64:
        return jsonify({'success': False, 'error': 'Password is too long'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'error': 'Username already exists'}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    session['user_id'] = new_user.id
    return jsonify({'success': True, 'redirect': url_for('profile')})

@app.route('/login-form', methods=['POST'])
def login_form():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        return jsonify({'success': True, 'redirect': url_for('home')})
    else:
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/upload-image', methods=['POST'])
@login_required
def upload_photo():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    unique_name = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
    
    try:
        uploaded_filename = upload_to_gcs(file, unique_name, bucket_name)
    except Exception as e:
        return jsonify({'error': f'Failed to upload to GCS: {e}'}), 500

    user_id = session.get('user_id')
    if not user_id:
         return jsonify({'error': 'User session not found'}), 401
    
    try:
        new_photo = Photo(filename=unique_name, user_id=user_id, url=uploaded_filename)
        db.session.add(new_photo)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to save to database: {e}'}), 500

    try:
        signed_url = generate_signed_url(uploaded_filename, bucket_name)
        return jsonify({'url': signed_url, 'success': True}) 
    except Exception as e:
        return jsonify({'error': f'Upload succeeded but failed to generate URL: {e}'}), 500

@app.route('/moments')
@login_required
def moments():
    return render_template('moments.html')

# ---------------------
# API Routes
# ---------------------

@app.route('/api/moments', methods=['GET'])
@login_required
def get_moments():
    moments = Moment.query.order_by(Moment.timestamp.desc()).all()
    current_user_id = session['user_id']
    
    moments_data = []
    for moment in moments:
        is_liked = any(user.id == current_user_id for user in moment.likes)
        
        comments_data = []
        for comment in moment.comments.order_by(Comment.timestamp.asc()):
            comments_data.append({
                'id': comment.id,
                'text': comment.text,
                'timestamp': comment.timestamp.isoformat(),
                'author_username': comment.author.username
            })
        
        signed_photo_url = None
        if moment.photo_url:
            try:
                signed_photo_url = generate_signed_url(moment.photo_url, bucket_name)
            except Exception as e:
                print(f"Error generating signed URL for {moment.photo_url}: {e}")
        
        moments_data.append({
            'id': moment.id,
            'text': moment.text,
            'photo_url': signed_photo_url,
            'timestamp': moment.timestamp.isoformat(),
            'author_username': moment.author.username,
            'like_count': len(moment.likes),
            'is_liked_by_user': is_liked,
            'comments': comments_data
        })
        
    return jsonify(moments_data)

@app.route('/api/moments', methods=['POST'])
@login_required
def create_moment():
    if 'text' not in request.form:
        return jsonify({'error': 'No text provided'}), 400

    text = request.form['text']
    if len(text) > 500:
        return jsonify({'error': 'Moment text exceeds 500 character limit'}), 400
    user_id = session['user_id']
    photo_url = None

    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '' and allowed_file(file.filename):
            try:
                unique_name = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
                photo_url = upload_to_gcs(file, unique_name, bucket_name)
            except Exception as e:
                return jsonify({'error': f'Failed to upload photo: {e}'}), 500
        elif file.filename != '':
            return jsonify({'error': 'File type not allowed'}), 400

    try:
        new_moment = Moment(text=text, photo_url=photo_url, user_id=user_id)
        db.session.add(new_moment)
        db.session.commit()
        signed_photo_url = None
        if new_moment.photo_url: 
            signed_photo_url = generate_signed_url(new_moment.photo_url, bucket_name)

        return jsonify({
            'success': True,
            'id': new_moment.id,
            'text': new_moment.text,
            'photo_url': signed_photo_url,
            'timestamp': new_moment.timestamp.isoformat(),
            'author_username': new_moment.author.username,
            'like_count': 0,
            'is_liked_by_user': False,
            'comments': []
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {e}'}), 500


@app.route('/api/moments/<int:moment_id>/like', methods=['POST'])
@login_required
def like_moment(moment_id):
    moment = Moment.query.get_or_404(moment_id)
    user = User.query.get(session['user_id'])
    
    if user in moment.likes:
        moment.likes.remove(user)
        db.session.commit()
        return jsonify({'success': True, 'action': 'unliked', 'like_count': len(moment.likes)})
    else:
        moment.likes.append(user)
        db.session.commit()
        return jsonify({'success': True, 'action': 'liked', 'like_count': len(moment.likes)})

@app.route('/api/moments/<int:moment_id>/comment', methods=['POST'])
@login_required
def post_comment(moment_id):
    data = request.get_json()
    if not data or 'text' not in data or not data['text']:
        return jsonify({'error': 'Comment text is required'}), 400
    if len(data['text']) > 300:
        return jsonify({'error': 'Comment text exceeds 300 character limit'}), 400
    moment = Moment.query.get_or_404(moment_id)
    user_id = session['user_id']
    
    try:
        new_comment = Comment(text=data['text'], user_id=user_id, moment_id=moment.id)
        db.session.add(new_comment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'comment': {
                'id': new_comment.id,
                'text': new_comment.text,
                'timestamp': new_comment.timestamp.isoformat(),
                'author_username': new_comment.author.username
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {e}'}), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
