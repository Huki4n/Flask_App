from flask import Flask, render_template, request, url_for, flash, session, redirect, make_response
import os
from datetime import datetime

from flask_assets import Environment, Bundle
from werkzeug.security import generate_password_hash, check_password_hash

from db import Database

app = Flask(__name__)

assets = Environment(app)
bundles = {
  'base_styles': Bundle(
    'scss/styles.scss',
    filters='libsass',
    output='css/styles.css',
  )
}
assets.register(bundles)

UPLOAD_FOLDER = os.path.join('uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.secret_key = os.urandom(24)


@app.route('/')
def index():
  print(session)
  if 'user_id' in session:
    return redirect(url_for('main', user_id=session['user_id']))
  return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    password_hash = generate_password_hash(password)

    name_cookies = request.cookies.get('username')

    resp = make_response(redirect(url_for('login')))

    user = db.get_user_by_email(email)

    if not user:
      db.add_user(username or name_cookies, email, password_hash)
      resp.set_cookie('username', username or name_cookies, max_age=60 * 60 * 24 * 7)  # Куки будет 7 дней

    return resp

  return render_template('register.html')


# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    email = request.form.get('email')
    password = request.form.get('password')

    user = db.get_user_by_email(email)

    if user and check_password_hash(user[3], password):
      session['user_id'] = user[0]
      print(session)
      return render_template('main.html', name=user[1], button_text="Logout")

    flash('Invalid email or password', 'error')
    return render_template('login.html', error='Invalid email or password')

  return render_template('login.html')


# Выход
@app.route('/logout')
def logout():
  session.pop('user_id', None)
  response = make_response(redirect(url_for('index')))
  response.set_cookie('username', '', expires=0)
  return response


db = Database()

if __name__ == '__main__':
  app.run(debug=True)
