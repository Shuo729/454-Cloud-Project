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

#load environment variables
INSTANCE_CONNECTION_NAME = "single-archive-476003-d7:us-west1:snapclouddb"
DB_USER = "testuser"
DB_PASSWORD = "Thisisatest1*" 
DB_NAME = "snapclouddb"


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

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    photos = db.relationship('Photo', backref='owner', lazy=True)

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
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_file(file, content_type=file.content_type)
    blob.make_public()
    return blob.public_url

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
    user = User.query.get(session['user_id'])
    photos = user.photos
    return render_template('profile.html', user=user, photos=photos)

@app.route('/upload')
@login_required
def upload():
    return render_template('upload.html')

@app.route('/albums')
@login_required
def albums():
    user = User.query.get(session['user_id'])
    photos = user.photos
    return render_template('albums.html', photos=photos)

@app.route('/signup-form', methods=['POST'])
def signup_form():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'error': 'Missing username or password'}), 400

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
        return jsonify({'success': True, 'redirect': url_for('profile')})
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
    
    upload_to_gcs(file, unique_name, bucket_name)

    #else:
        #filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        #file.save(filepath)
        #file_url = f"/{app.config['UPLOAD_FOLDER']}/{unique_name}"

    #user_id = session.get('user_id')
    #new_photo = Photo(filename=unique_name, user_id=user_id, url=file_url)
    #db.session.add(new_photo)
    #db.session.commit()

    #return jsonify({'url': file_url})

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
