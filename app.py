import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash
from src.models import db, User, Progress, Result
from src.utils import load_json
from src.configs import DBConfig, CODES_INFO, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config.from_object(DBConfig)

db.init_app(app)

photo_styles = load_json('data/photo_parameters.json')
question_text = load_json('data/questions.json')
TOTAL_QUESTIONS = len(question_text)

@app.before_request
def check_user_authentication():
    path = request.path
    user_id = session.get("user_id")

    # Разрешаем доступ к статике и favicon
    if path.startswith("/static/") or path == "/favicon.ico":
        return

    if not user_id:
        # Неавторизованный пользователь может попасть только на /login
        if path != "/login":
            return redirect(url_for("login"))
    else:
        # Авторизованный пользователь пытается попасть на / или /login
        if path in ["/", "/login"]:
            for i in range(1, len(question_text) + 1):
                correct = Progress.query.filter_by(
                    user_id=user_id,
                    question_number=i,
                    is_correct=True
                ).first()
                if not correct and i == 1:
                    return redirect(url_for("intro"))
                if not correct:
                    return redirect(url_for("question", question_number=i))
            return redirect(url_for("complete"))


def has_finished_quiz(user_id: int) -> bool:
    total = len(question_text)
    for i in range(1, total + 1):
        correct = Progress.query.filter_by(
            user_id=user_id,
            question_number=i,
            is_correct=True
        ).first()
        if not correct:
            return False
    return True


@app.route("/login", methods=["GET", "POST"])
def login():
    background = 'images/login/background.jpg'

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session.permanent = True
            session["user_id"] = user.id
            return redirect(url_for("intro"))
        else:
            return render_template(
                "login.html", error="Неверный логин или пароль", background=background
            )

    return render_template("login.html", background=background)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/intro")
def intro():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("intro.html")


@app.route("/question/<int:question_number>")
def question(question_number):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    is_last_question = question_number == len(question_text)

    # Запрет на просмотр вопросов вне очереди
    if question_number > 1:
        previous_correct = db.session.query(Progress).filter_by(
            user_id=user_id,
            question_number=question_number - 1,
            is_correct=True
        ).first()
        if not previous_correct:
            return redirect(url_for("question", question_number=question_number - 1))

    # Загружаем данные вопроса
    image_dir = f"images/question{question_number}"
    full_path = os.path.join("static", image_dir)
    question_data = question_text.get(str(question_number))
    photo_params = photo_styles.get(str(question_number), [])

    # Фото
    photos = []
    if os.path.exists(full_path):
        files = sorted([f for f in os.listdir(full_path) if f.lower().startswith('img')])
        for i, filename in enumerate(files):
            if i >= len(photo_params):
                break
            photos.append({
                "src": f"{image_dir}/{filename}",
                "style": photo_params[i]
            })

    # Прогресс по этому вопросу
    answers = Progress.query.filter_by(
        user_id=user_id,
        question_number=question_number
    ).all()

    selected_answers = [a.chosen_answer for a in answers]
    correct_answer = question_data["correct"]

    background = f"{image_dir}/background.jpg"

    return render_template(
        "question.html",
        question_number=question_number,
        question_data=question_data,
        photos=photos,
        background=background,
        selected_answers=selected_answers,
        correct_answer=correct_answer,
        is_last_question=is_last_question
    )


@app.route("/complete")
def complete():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    if not has_finished_quiz(user_id):
        # Перенаправляем на первый неотвеченный вопрос
        for i in range(1, len(question_text) + 1):
            correct = Progress.query.filter_by(
                user_id=user_id,
                question_number=i,
                is_correct=True
            ).first()
            if not correct:
                return redirect(url_for("question", question_number=i))

    result = Result.query.filter_by(user_id=user_id).order_by(Result.created_at.desc()).first()

    if result is None:
        code = 0
    else:
        code = int(result.result_code)

    img_dir = 'images/complete'
    if code in CODES_INFO:
        background = f'{img_dir}/background_v1.jpg'
    else:
        background = f'{img_dir}/background_v2.jpg'

    return render_template("complete.html", result_code=code, codes_info=CODES_INFO, background=background)


@app.route("/restart", methods=["POST"])
def restart():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    Progress.query.filter_by(user_id=user_id).delete()
    Result.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return redirect(url_for("question", question_number=1))


@app.route("/answer", methods=["POST"])
def answer():
    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 403

    data = request.get_json()
    question_number = int(data.get("question_number"))
    chosen = data.get("chosen_answer")
    correct = question_text[str(question_number)]["correct"]
    is_correct = chosen == correct
    user_id = session["user_id"]

    # Сохраняем попытку
    db.session.add(Progress(
        user_id=user_id,
        question_number=question_number,
        chosen_answer=chosen,
        is_correct=is_correct
    ))
    db.session.commit()

    if is_correct and question_number == len(question_text):
        result = Result.query.filter_by(user_id=user_id).first()
        if result:
            return jsonify({
                "status": "correct",
                "completed": True,
                "code": result.result_code
            })
        else:
            return jsonify({
                "status": "correct",
                "completed": True,
                "code": 0
            })

    return jsonify({"status": "correct" if is_correct else "wrong"})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
