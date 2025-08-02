import os
from dotenv import load_dotenv
load_dotenv()


# ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
# QUIZ_DB_URI = f"sqlite:///{os.path.join(ROOT_DIR, 'instance', 'quiz.db')}"

CODES_INFO = {
    0: os.environ.get("CODE_0"),
    1: os.environ.get("CODE_1"),
    2: os.environ.get("CODE_2")
}

SECRET_KEY = os.environ.get("APP_KEY")

class DBConfig:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DB_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False