import argparse
from flask import Flask
from src.models import db, User, Result
from src.configs import DBConfig
from datetime import datetime

app = Flask(__name__)
app.config.from_object(DBConfig)
db.init_app(app)


def add_result_cli():
    parser = argparse.ArgumentParser(description="Добавить результат пользователю")
    parser.add_argument("--name", type=str, help="Имя пользователя")
    parser.add_argument("--code", type=str, help="Код результата")
    args = parser.parse_args()

    with app.app_context():
        username = args.name or input("Введите имя пользователя: ").strip()
        user = User.query.filter_by(username=username).first()

        if not user:
            print(f"❌ Пользователь '{username}' не найден.")
            return

        result_code = args.code or input("Введите код результата: ").strip()

        if not result_code.isdigit():
            print("❌ Код должен быть числовым.")
            return

        result = Result(user_id=user.id, result_code=result_code, created_at=datetime.now())
        db.session.add(result)
        db.session.commit()

        print(f"✅ Код '{result_code}' добавлен для пользователя '{username}'.")


if __name__ == "__main__":
    add_result_cli()