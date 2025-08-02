from flask import Flask
from src.models import db
from src.configs import DBConfig

app = Flask(__name__)
app.config.from_object(DBConfig)
db.init_app(app)

with app.app_context():
    db.drop_all()
    print("🗑️ Все таблицы удалены.")