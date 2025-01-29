import psycopg2

DB_CONFIG = {
  'dbname': 'Flask_app',
  'user': 'postgres',
  'password': 'qweasdFGzxc34215',
  'host': 'localhost'
}


class Database:
  def __init__(self,):
    conn = self.get_db_connection()
    cur = conn.cursor()
    cur.execute('''
          CREATE TABLE IF NOT EXISTS users (
              id SERIAL PRIMARY KEY,
              username VARCHAR(50) NOT NULL,
              email VARCHAR(100) NOT NULL,
              password_hash VARCHAR(256) NOT NULL
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
