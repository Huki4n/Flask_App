import base64
import json
import os

from flask import Flask, render_template, request, url_for, flash, session, redirect, make_response
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
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}  # Разрешенные расширения файлов
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.secret_key = os.urandom(24)


def b64encode_filter(value):
  return base64.b64encode(value.encode()).decode()


app.jinja_env.filters['b64encode'] = b64encode_filter


def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def save_file(request_files, filename):
  image_url = None

  if filename in request_files:
    file = request_files[filename]

    if file and allowed_file(file.filename):
      filename = secure_filename(file.filename)
      file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
      file.save(file_path)
      image_url = f"uploads/{filename}"

  return image_url


@app.route('/')
def index():
  if 'user_id' in session or request.cookies.get('user_id'):
    return redirect(url_for('main'))
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
    else:
      errors['register'] = 'Account by this email already exists.'
      return render_template('register.html', errors=errors)

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
      resp = make_response(redirect(url_for('main')))

      resp.set_cookie('userid', str(user[0]), max_age=60 * 60 * 24 * 7)
      resp.set_cookie('username', str(user[1]), max_age=60 * 60 * 24 * 7)

      return resp

    return render_template('login.html', error='Invalid email or password')

  return render_template('login.html')


# Выход
@app.route('/logout')
def logout():
  session.pop('user_id', None)
  response = make_response(redirect(url_for('login')))
  response.set_cookie('username', '', expires=0)
  response.set_cookie('userid', '', expires=0)
  return response


@app.route('/main')
def main():
  user_id = request.cookies.get('userid')
  user_name = request.cookies.get('username')
  posts = db.get_posts()

  return render_template(
    'main.html',
    logo_link='main',
    user_signin=True,

    user_id=user_id,
    name=user_name,
    posts=posts,
  )


@app.route('/profile', methods=['GET', 'POST'])
def profile():
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
  print(user)
  if request.method == 'POST':
    if 'user' in request.form:
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
    'profile.html',
    logo_link='main',
    user_signin=True,

    username=username,
    email=email,
    tel=tel if tel is not None else '',
    avatar=f"/static/uploads/{avatar}" if avatar else f"/static/uploads/{filename}",
  )


@app.route('/profile/<author_name>', methods=['GET'])
def profile_user(author_name):
  author_id = request.args.get('author_id')
  user = db.get_user_by_id(author_id)

  username = author_name
  email = user[2]
  tel = user[4]
  avatar = user[5]
  filename = "placeholder.png"

  return render_template(
    'profile_user.html',
    logo_link='main',
    user_signin=True,

    username=username,
    email=email,
    tel=tel if tel is not None else '',
    avatar=f"/static/uploads/{avatar}" if avatar else f"/static/uploads/{filename}",
  )


@app.route('/create_post', methods=['POST'])
def create_post():
  title = request.form.get('title')
  content = request.form.get('content')
  user_id = request.cookies.get('userid') or session['user_id'][1]
  image_url = save_file(request.files, 'image_file')

  tags_json = request.form.get('tags')
  tags = json.loads(tags_json) if tags_json else []

  db.create_post(user_id, title, content, tags, image_url)

  flash("Пост успешно создан!", "success")
  return redirect(url_for('main'))


@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
  if request.method == 'POST':
    title = request.form.get('title')
    content = request.form.get('content')
    image_url = save_file(request.files, 'edit_image_file')

    if image_url is None:
      image_url = request.form.get('edit_image_name')

    tags_json = request.form.get('edit-tags')
    tags = json.loads(tags_json) if tags_json else []

    db.update_post(post_id, title, content, image_url, tags)

  return redirect(url_for('main'))


@app.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
  db.delete_post(post_id)
  return redirect(url_for('main'))


@app.route('/search', methods=['GET'])
def search():
  user_id = request.cookies.get('userid')
  user_name = request.cookies.get('username')
  tag = request.args.get('tags-search')

  if tag:
    posts = db.search_posts_by_tag(tag)
  else:
    return redirect(url_for('main'))

  return render_template(
    'main.html',
    logo_link='main',
    user_signin=True,
    search_tag=tag,

    user_id=user_id,
    name=user_name,
    posts=posts,
  )


db = Database()
validation = Validation()
user_cache = {}
posts_cache = {}

if __name__ == '__main__':
  app.run(debug=True)
