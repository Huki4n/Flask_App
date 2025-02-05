import psycopg2
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

DB_CONFIG = {
  'dbname': os.getenv('DATABASE_NAME'),
  'user': os.getenv('DATABASE_USER'),
  'password': os.getenv('DATABASE_PASSWORD'),
  'host': 'localhost'
}


class DatabaseConnection:
  def __init__(self, db):
    self.db = db

  def __enter__(self):
    self.conn = self.db.get_db_connection()
    self.cur = self.conn.cursor()
    return self.cur

  def __exit__(self, exc_type, exc_value, traceback):
    self.conn.commit()
    self.cur.close()
    self.conn.close()


class Database:
  def __init__(self, ):
    with DatabaseConnection(self) as cur:
      cur.execute('''
          CREATE TABLE IF NOT EXISTS users (
              id SERIAL PRIMARY KEY,
              username VARCHAR(50) NOT NULL,
              email VARCHAR(100) NOT NULL,
              password_hash VARCHAR(256) NOT NULL,
              tel VARCHAR(20),
              avatar VARCHAR(255)
          )
      ''')

  @staticmethod
  def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

  # Функция преобразования массива с данными поста в словарь
  @staticmethod
  def post_to_dict(post):
    return {
      "id": post[0],
      "title": post[1],
      "content": post[2],
      "image_url": post[-4] if post[-4] else None,
      "author_id": post[3],
      "author_name": post[-3],
      "author_avatar": post[-2],
      "created_at": datetime.strptime(post[4], '%y.%m.%d %H:%M:%s') if isinstance(post[4], str) else post[4].strftime(
        '%y.%m.%d %H:%M'),
      "tags": post[-1],
    }

  @staticmethod
  def update_tags(cur, tags, post_id):
    tags = list(set(tags))
    if not tags:
      return []

    # Добавляем новые теги, если их нет
    tag_values = ','.join(cur.mogrify("(%s)", (tag,)).decode() for tag in tags)
    cur.execute(f'''
          INSERT INTO tags (name) 
          VALUES {tag_values}
          ON CONFLICT (name) DO NOTHING
          RETURNING id, name;
      ''')

    # Получаем id новых тегов
    created_tags = dict(cur.fetchall())

    # Получаем id уже существующих тегов
    cur.execute(f'''
          SELECT id, name FROM tags WHERE name IN ({','.join(['%s'] * len(tags))});
      ''', tags)

    existing_tags = dict(cur.fetchall())

    # Объединяем id новых и существующих тегов
    tag_ids = list(created_tags.keys()) + list(existing_tags.keys())

    # 4. Привязываем новые теги к посту
    if tag_ids:
      post_tag_values = ','.join(cur.mogrify("(%s, %s)", (post_id, tag_id)).decode() for tag_id in tag_ids)
      cur.execute(f'''
             INSERT INTO post_tags (post_id, tag_id)
             VALUES {post_tag_values}
             ON CONFLICT DO NOTHING;
         ''')

  def add_user(self, username, email, password_hash):
    with DatabaseConnection(self) as cur:
      cur.execute('INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)',
                  (username, email, password_hash))

  def get_user_by_email(self, email):
    with DatabaseConnection(self) as cur:
      cur.execute('SELECT * FROM users WHERE email = %s', (email,))
      user = cur.fetchone()
      return user

  def get_user_by_id(self, user_id):
    with DatabaseConnection(self) as cur:
      cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
      user = cur.fetchone()
      return user

  def update_user_info(self, user_id, new_username, new_email, new_tel):
    with DatabaseConnection(self) as cur:
      cur.execute('''
            UPDATE users
            SET username = %s, email = %s, tel = %s
            WHERE id = %s
        ''', (new_username, new_email, new_tel, user_id))

  def update_user_avatar(self, user_id, new_avatar):
    with DatabaseConnection(self) as cur:
      cur.execute('''
            UPDATE users
            SET avatar = %s
            WHERE id = %s
        ''', (new_avatar, user_id))

      cur.execute('''
              SELECT avatar FROM users WHERE id = %s
          ''', (user_id,))

      avatar = cur.fetchone()[0]

      return avatar

  def get_posts(self, ):
    with DatabaseConnection(self) as cur:
      cur.execute("""
          SELECT p.*, 
                 u.username, 
                 u.avatar, 
                 COALESCE(ARRAY_AGG(t.name), '{}') AS tags
          FROM posts p
          JOIN users u ON p.author_id = u.id
          LEFT JOIN post_tags pt ON p.id = pt.post_id
          LEFT JOIN tags t ON pt.tag_id = t.id
          GROUP BY p.id, p.created_at, u.id
          ORDER BY p.created_at DESC
      """)

      posts = cur.fetchall()

      posts_list = [
        self.post_to_dict(post)
        for post in posts
      ]

      return posts_list

  def get_post_by_id(self, post_id):
    with DatabaseConnection(self) as cur:
      cur.execute('''
          SELECT p.*, 
                 COALESCE(ARRAY_AGG(t.name), '{}') AS tags
          FROM posts p
          LEFT JOIN post_tags pt ON p.id = pt.post_id
          LEFT JOIN tags t ON pt.tag_id = t.id
          WHERE p.id = %s
          GROUP BY p.id
      ''', (post_id,))

      post = cur.fetchone()
      post_dict = None

      if post:
          post_dict = self.post_to_dict(post)

      return post_dict

  def create_post(self, user_id, title, content, tags, image_url=None,):
    with DatabaseConnection(self) as cur:
      cur.execute('''
          INSERT INTO posts (id, title, content, author_id, created_at, updated_at, status, views, likes, image_url)
          VALUES (gen_random_uuid(), %s, %s, %s, NOW(), NOW(), 'published', 0, 0, %s)
          RETURNING id;
      ''', (title, content, user_id, image_url))

      post_id = cur.fetchone()[0]

      self.update_tags(cur, tags, post_id)

      return post_id

  def update_post(self, post_id, title, content, image_url, tags):
    with DatabaseConnection(self) as cur:
      # 1. Обновляем сам пост
      cur.execute('''
          UPDATE posts SET title = %s, content = %s, updated_at = NOW(), image_url = %s WHERE id = %s
      ''', (title, content, image_url, post_id))

      # 2. Удаляем все старые связи поста с тегами
      cur.execute('DELETE FROM post_tags WHERE post_id = %s', (post_id,))

      # 3. Добавляем новые теги (если их нет)
      self.update_tags(cur, tags, post_id)

  def delete_post(self, post_id):
    with DatabaseConnection(self) as cur:
      cur.execute("DELETE FROM posts WHERE id = %s", (post_id,))

  def get_post_tags(self, post_id):
    with DatabaseConnection(self) as cur:
      cur.execute('''
        SELECT t.id, t.name
        FROM tags t
        JOIN post_tags pt ON t.id = pt.tag_id
        WHERE pt.post_id = %s;
      ''', (post_id,))

      post_tags = cur.fetchall()

      return post_tags

  def search_posts_by_tag(self, tag_name):
    with DatabaseConnection(self) as cur:
      cur.execute('''
          SELECT 
              p.*,
              u.username AS author_name, u.avatar AS author_avatar,
              COALESCE(ARRAY_AGG(t.name) FILTER (WHERE t.id IS NOT NULL), '{}') AS tags
          FROM posts p
          JOIN users u ON p.author_id = u.id
          JOIN post_tags pt ON p.id = pt.post_id
          JOIN tags t ON pt.tag_id = t.id
          WHERE t.name = %s
          GROUP BY p.id, u.id
      ''', (tag_name,))

      posts = cur.fetchall()

      return [
        self.post_to_dict(post)
        for post in posts
      ]





