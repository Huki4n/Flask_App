import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
  'dbname': os.getenv('DATABASE_NAME'),
  'user': os.getenv('DATABASE_USER'),
  'password': os.getenv('DATABASE_PASSWORD'),
  'host': 'localhost'
}


class Database:
  def __init__(self, ):
    conn = self.get_db_connection()
    cur = conn.cursor()
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
    conn.commit()
    cur.close()
    conn.close()

  @staticmethod
  def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

  # Добавление пользователя
  def add_user(self, username, email, password_hash):
    conn = self.get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)',
                (username, email, password_hash))
    conn.commit()
    cur.close()
    conn.close()

  # Получение пользователя по email
  def get_user_by_email(self, email):
    conn = self.get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

  def get_user_by_id(self, user_id):
    conn = self.get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

  def update_user_info(self, user_id, new_username, new_email, new_tel):
    conn = self.get_db_connection()
    cur = conn.cursor()
    cur.execute('''
          UPDATE users
          SET username = %s, email = %s, tel = %s
          WHERE id = %s
      ''', (new_username, new_email, new_tel, user_id))
    conn.commit()
    cur.close()
    conn.close()

  def update_user_avatar(self, user_id, new_avatar):
    conn = self.get_db_connection()
    cur = conn.cursor()
    cur.execute('''
          UPDATE users
          SET avatar = %s
          WHERE id = %s
      ''', (new_avatar, user_id))
    conn.commit()

    cur.execute('''
            SELECT avatar FROM users WHERE id = %s
        ''', (user_id,))

    avatar = cur.fetchone()[0]
    cur.close()
    conn.close()
    return avatar
