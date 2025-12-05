from flask import Blueprint, render_template, redirect, url_for, session, request

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """메인 페이지로 리다이렉트 (로그인 상태에 따라)"""
    if 'user_id' in session:
        return redirect(url_for('main.main_page'))
    return redirect(url_for('main.auth'))


@main_bp.route('/auth')
def auth():
    """로그인/회원가입 페이지"""
    # 이미 로그인된 경우 메인으로 이동
    if 'user_id' in session:
        return redirect(url_for('main.main_page'))
    
    error = request.args.get('error')
    return render_template('auth.html', error=error)


@main_bp.route('/main')
def main_page():
    """메인 검색 페이지"""
    # 로그인 체크 (선택적 - 비로그인도 허용하려면 주석 처리)
    # if 'user_id' not in session:
    #     return redirect(url_for('main.auth'))
    
    user_name = session.get('user_name', '사용자')
    return render_template('main.html', user_name=user_name)


@main_bp.route('/logout')
def logout():
    """로그아웃 처리"""
    session.clear()
    return redirect(url_for('main.auth'))
