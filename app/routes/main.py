# app/routes/main.py
# 메인 라우트 - 로그인, 메인 페이지 등

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    # 루트 경로 접속 시 로그인 페이지 렌더링
    return render_template("login.html")

@main_bp.route("/login")
def login():
    # 로그인 페이지
    return render_template("login.html")

