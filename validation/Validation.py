import re


class Validation:
  @staticmethod
  def validate_email(email):
    return not ('@' in email and '.' in email)

  def register(self, data):
    errors = {}
    if len(data.get('username', '')) < 3:
      errors['username'] = "Имя должно содержать не менее 3 символов."
    if self.validate_email(data.get('email', '')):
      errors['email'] = "Введите валидный адрес электронной почты"
    if len(data.get('password', '')) < 8:
      errors['password'] = "Длина пароля не может быть меньше 8 символов"
    return errors


