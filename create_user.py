import argparse
from werkzeug.security import generate_password_hash
from src.models import db, User
from src.configs import DBConfig
from flask import Flask
import os

app = Flask(__name__)
app.config.from_object(DBConfig)

db.init_app(app)

def create_user_cli():
    parser = argparse.ArgumentParser(description="Создание нового пользователя")
    parser.add_argument("--name", type=str, help="Имя пользователя")
    parser.add_argument("--password", type=str, help="Пароль")
    args = parser.parse_args()

    with app.app_context():
        username = args.name or input("Введите логин: ").strip()

        if not username:
            print("Логин не может быть пустым.")
            return

        existing = User.query.filter_by(username=username).first()
        if existing:
            print("Пользователь с таким логином уже существует.")
            return

        if args.password:
            password = args.password.strip()
        else:
            password = input("Введите пароль: ").strip()

        hashed = generate_password_hash(password)
        user = User(username=username, password_hash=hashed)
        db.session.add(user)
        db.session.commit()

        print(f"✅ Пользователь '{username}' создан.")

if __name__ == "__main__":
    create_user_cli()