from flask import Flask, render_template, request, url_for, flash, session, redirect, make_response
import os

from flask_assets import Environment, Bundle
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from db import Database
from validation.Validation import Validation

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

UPLOAD_FOLDER = os.path.join('static/uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.secret_key = os.urandom(24)


@app.route('/')
def index():
  if 'user_id' in session:
    return redirect(url_for('main_page'))
  return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
  errors = {}
  if request.method == 'POST':
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    errors = validation.register(request.form)
    if errors:
      return render_template('register.html', errors=errors)

    password_hash = generate_password_hash(password)

    name_cookies = request.cookies.get('username')
    resp = make_response(redirect(url_for('login')))

    user = db.get_user_by_email(email)

    if not user:
      db.add_user(username or name_cookies, email, password_hash)
      user = db.get_user_by_email(email)

      if user:
        resp.set_cookie('userid', str(user[0]), max_age=60 * 60 * 24 * 7)  # Куки будет 7 дней
        resp.set_cookie('username', username or name_cookies, max_age=60 * 60 * 24 * 7)  # Куки будет 7 дней

    return resp

  return render_template('register.html', errors=errors)


# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():

  if request.method == 'POST':
    email = request.form.get('email')
    password = request.form.get('password')

    if 'user' not in user_cache:
      user = db.get_user_by_email(email)
      user_cache['user'] = user
    else:
      user = user_cache['user']

    if user and check_password_hash(user[3], password):
      session['user_id'] = [user[0], user[1]]
      resp = make_response(redirect(url_for('main_page')))
      resp.set_cookie('userid', str(user[0]), max_age=60 * 60 * 24 * 7)  # Куки будет 7 дней
      return resp

    return render_template('login.html', error='Invalid email or password')

  return render_template('login.html')


# Выход
@app.route('/logout')
def logout():
  session.pop('user_id', None)
  response = make_response(redirect(url_for('login')))
  response.set_cookie('username', '', expires=0)
  return response


@app.route('/main')
def main_page():
  return render_template(
    'main.html',
    name=session['user_id'][1],
    button_text="Logout"
  )


@app.route('/account', methods=['GET', 'POST'])
def account():
  user_id = request.cookies.get('userid')

  if 'user' in user_cache:
    user = user_cache['user']
  else:
    user = db.get_user_by_id(user_id)

  username = user[1]
  email = user[2]
  tel = user[4]
  avatar = user[5]
  filename = "placeholder.png"

  if request.method == 'POST':
    if 'username' in request.form:
      username = request.form.get('user')
      email = request.form.get('email')
      tel = request.form.get('tel')

      db.update_user_info(user_id, username, email, tel)

    else:
      new_avatar = request.files['photo']

      filename = secure_filename(new_avatar.filename)
      avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
      new_avatar.save(avatar_path)

      avatar = db.update_user_avatar(user_id, filename)

  return render_template(
    'account.html',
    button_text='Sign out',
    username=username,
    email=email,
    tel=tel if tel is not None else '',
    avatar=f"/static/uploads/{avatar}" if avatar else f"/static/uploads/{filename}",
  )


db = Database()
validation = Validation()
user_cache = {}

if __name__ == '__main__':
  app.run(debug=True)
