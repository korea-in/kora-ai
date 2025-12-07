"""
인증 관련 라우트
- 회원가입
- 로그인
- 로그아웃
- 비밀번호 재설정
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from app.services.firebase import (
    create_user, 
    verify_user_password,
    get_user_by_email,
    get_user_by_uid,
    get_firebase_user_by_email,
    verify_user_by_email_and_name,
    reset_user_password,
    verify_id_token,
    update_last_login,
    is_firebase_initialized
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """회원가입 API"""
    if not is_firebase_initialized():
        return jsonify({'success': False, 'error': 'Firebase not available'}), 503
    
    # JSON 또는 Form 데이터 처리
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', '')
    
    if not email or not password:
        if request.is_json:
            return jsonify({'success': False, 'error': '이메일과 비밀번호를 입력하세요'}), 400
        return redirect(url_for('main.auth', error='missing_fields'))
    
    # 비밀번호 길이 체크
    if len(password) < 6:
        if request.is_json:
            return jsonify({'success': False, 'error': '비밀번호는 6자 이상이어야 합니다'}), 400
        return redirect(url_for('main.auth', error='password_too_short'))
    
    # 사용자 생성 (Firebase Auth + Firestore)
    user, error = create_user(email, password, name)
    
    if error:
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 400
        return redirect(url_for('main.auth', error='signup_failed'))
    
    # 세션에 사용자 정보 저장
    session['user_id'] = user.uid
    session['user_email'] = user.email
    session['user_name'] = user.display_name
    
    if request.is_json:
        return jsonify({
            'success': True, 
            'user': {
                'uid': user.uid,
                'email': user.email,
                'name': user.display_name,
                'subscription_tier': user.subscription_tier,
                'daily_analysis_limit': user.daily_analysis_limit
            }
        })
    
    return redirect(url_for('main.main_page'))


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    로그인 API
    
    지원 방식:
    1. ID 토큰 방식 (클라이언트에서 Firebase Auth 사용 시)
    2. 이메일/비밀번호 방식 (서버 사이드 - 데모용)
    """
    if not is_firebase_initialized():
        return jsonify({'success': False, 'error': 'Firebase not available'}), 503
    
    # JSON 또는 Form 데이터 처리
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    # 방식 1: ID 토큰 방식 (클라이언트에서 Firebase Auth 사용 시)
    id_token = data.get('idToken')
    
    if id_token:
        decoded_token, error = verify_id_token(id_token)
        
        if error:
            return jsonify({'success': False, 'error': error}), 401
        
        # Firestore에서 사용자 정보 조회
        user = get_user_by_uid(decoded_token['uid'])
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found in database'}), 404
        
        # 마지막 로그인 시간 업데이트
        update_last_login(user.uid)
        
        # 세션에 사용자 정보 저장
        session['user_id'] = user.uid
        session['user_email'] = user.email
        session['user_name'] = user.display_name
        
        return jsonify({
            'success': True,
            'user': {
                'uid': user.uid,
                'email': user.email,
                'name': user.display_name,
                'subscription_tier': user.subscription_tier,
                'analysis_count': user.analysis_count,
                'daily_analysis_limit': user.daily_analysis_limit,
                'daily_analysis_used': user.daily_analysis_used
            }
        })
    
    # 방식 2: 이메일/비밀번호 방식 (bcrypt 해시 검증)
    email = data.get('email')
    password = data.get('password')
    
    print(f"[DEBUG] Login attempt - email: {email}")  # 디버그
    
    if not email or not password:
        if request.is_json:
            return jsonify({'success': False, 'error': '이메일과 비밀번호를 입력하세요'}), 400
        return redirect(url_for('main.auth', error='missing_fields'))
    
    # 비밀번호 검증 (bcrypt 해시)
    user, error = verify_user_password(email, password)
    
    print(f"[DEBUG] verify_user_password result - user: {user}, error: {error}")  # 디버그
    
    if error:
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 401
        return redirect(url_for('main.auth', error='login_failed'))
    
    # 계정 활성 상태 체크
    if not user.is_active:
        if request.is_json:
            return jsonify({'success': False, 'error': '비활성화된 계정입니다'}), 403
        return redirect(url_for('main.auth', error='account_disabled'))
    
    # 마지막 로그인 시간 업데이트
    update_last_login(user.uid)
    
    # 세션에 사용자 정보 저장
    session['user_id'] = user.uid
    session['user_email'] = user.email
    session['user_name'] = user.display_name
    session['user_credits'] = user.credits
    session['investment_type'] = getattr(user, 'investment_type', '') or ''
    session['investment_score'] = getattr(user, 'investment_score', 0) or 0
    
    if request.is_json:
        return jsonify({
            'success': True,
            'user': {
                'uid': user.uid,
                'email': user.email,
                'name': user.display_name,
                'subscription_tier': user.subscription_tier,
                'analysis_count': user.analysis_count,
                'credits': user.credits
            }
        })
    
    return redirect(url_for('main.main_page'))


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """로그아웃"""
    session.clear()
    
    if request.is_json:
        return jsonify({'success': True})
    
    return redirect(url_for('main.auth'))


@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """로그인 상태 확인 API"""
    if 'user_id' not in session:
        return jsonify({'authenticated': False})
    
    # Firestore에서 최신 사용자 정보 조회
    user = get_user_by_uid(session.get('user_id'))
    
    if not user:
        session.clear()
        return jsonify({'authenticated': False})
    
    return jsonify({
        'authenticated': True,
        'user': {
            'uid': user.uid,
            'email': user.email,
            'name': user.display_name,
            'subscription_tier': user.subscription_tier,
            'analysis_count': user.analysis_count,
            'daily_analysis_limit': user.daily_analysis_limit,
            'daily_analysis_used': user.daily_analysis_used,
            'favorite_companies': user.favorite_companies
        }
    })


@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """사용자 프로필 조회"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = get_user_by_uid(session.get('user_id'))
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'uid': user.uid,
        'email': user.email,
        'display_name': user.display_name,
        'photo_url': user.photo_url,
        'subscription_tier': user.subscription_tier,
        'analysis_count': user.analysis_count,
        'daily_analysis_limit': user.daily_analysis_limit,
        'daily_analysis_used': user.daily_analysis_used,
        'favorite_companies': user.favorite_companies,
        'email_notifications': user.email_notifications,
        'push_notifications': user.push_notifications,
        'is_verified': user.is_verified
    })


@auth_bp.route('/verify-user', methods=['POST'])
def verify_user():
    """
    사용자 본인 확인 (비밀번호 재설정 1단계)
    이메일과 이름으로 사용자 확인
    """
    if not is_firebase_initialized():
        return jsonify({'success': False, 'error': 'Firebase not available'}), 503
    
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    
    if not email or not name:
        return jsonify({'success': False, 'error': '이메일과 이름을 입력해주세요'}), 400
    
    user, error = verify_user_by_email_and_name(email, name)
    
    if error:
        return jsonify({'success': False, 'error': error}), 400
    
    return jsonify({
        'success': True,
        'message': '본인 확인 완료',
        'user_email': user.email
    })


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    비밀번호 재설정 (2단계)
    이메일, 이름 재확인 후 새 비밀번호 설정
    """
    if not is_firebase_initialized():
        return jsonify({'success': False, 'error': 'Firebase not available'}), 503
    
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    new_password = data.get('new_password')
    
    if not email or not name or not new_password:
        return jsonify({'success': False, 'error': '모든 필드를 입력해주세요'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': '비밀번호는 6자 이상이어야 합니다'}), 400
    
    success, error = reset_user_password(email, name, new_password)
    
    if not success:
        return jsonify({'success': False, 'error': error}), 400
    
    return jsonify({
        'success': True,
        'message': '비밀번호가 성공적으로 변경되었습니다'
    })
