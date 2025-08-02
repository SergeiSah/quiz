from src.models import db
from app import app  # или from main import app

with app.app_context():
    db.create_all()
    print("✅ База данных инициализирована.")