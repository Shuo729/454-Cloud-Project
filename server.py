from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from google.cloud import storage
import os
from werkzeug.security import check_password_hash


app = Flask(__name__)
CORS(app) 


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///photos.db'  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

client = storage.Client()
bucket_name = 'your-cloud-storage-bucket'
bucket = client.bucket(bucket_name)


def allowed_file(filename):
    last_dot_index = -1  
    for i, char in enumerate(filename):
        if char == '.':
            last_dot_index = i  
    
    if last_dot_index == -1:
        return False

    file_type = filename[last_dot_index + 1:].lower()  
    return file_type in ALLOWED_EXTENSIONS






        




@app.route('/')
def home():
    return render_template('index.html')





@app.route('/login')
def login():
    return render_template('login.html')


def login_form():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return jsonify({'success': True, 'redirect': url_for('home')})
        else:
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401

    return render_template('login.html')


@app.route('/signup-form', methods=['GET', 'POST'])
def signup_form():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'error': 'Username already exists'}), 400

        hashed_password = generate_password_hash(password)

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id

        return jsonify({'success': True, 'redirect': url_for('home')})

    return render_template('signup.html')



@app.route('/signup')
def signup():
    return render_template('signup.html')



@app.route('/profile')
def profile():
    return render_template('profile.html')



@app.route('/upload')
def upload():
    return render_template('upload.html')






@app.route('/albums')
def albums():
    return render_template('albums.html')



@app.route('/upload-image', methods=['POST'])
def upload_photo():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    filename = secure_filename(file.filename)
    blob = bucket.blob(filename)
    blob.upload_from_file(file, content_type=file.content_type)

    blob.make_public()

    return jsonify({'url': blob.public_url})






if __name__ == '__main__':
    app.run(debug=True)
