from flask import Flask, request, jsonify, render_template
from flask_cors import CORS


app = Flask(__name__)
CORS(app) 


@app.route('/')
def home():
    return render_template('index.html')





@app.route('/login')
def home():
    return render_template('login.html')





@app.route('/signup')
def home():
    return render_template('signup.html')



@app.route('/profile')
def home():
    return render_template('profile.html')



@app.route('/upload')
def home():
    return render_template('upload.html')


@app.route('/albums')
def home():
    return render_template('albums.html')

@app.route('/photo')
def home():
    return render_template('photo.html')



if __name__ == '__main__':
    app.run(debug=True)
