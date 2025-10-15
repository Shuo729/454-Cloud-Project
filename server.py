from flask import Flask, request, jsonify, render_template, session, url_for, redirect
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import os

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///photos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'supersecretkey'

db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    photos = db.relationship('Photo', backref='owner', lazy=True)

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    user_id = session.get('user_id')
    new_photo = Photo(filename=filename, user_id=user_id)
    db.session.add(new_photo)
    db.session.commit()

    file_url = f"/{app.config['UPLOAD_FOLDER']}/{filename}"
    return jsonify({'url': file_url})

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)
