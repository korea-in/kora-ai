from flask import Flask
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Secret key 설정
    app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
    
    # Firebase 초기화
    from app.services.firebase import init_firebase
    init_firebase(app)
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.company import company_bp
    from app.routes.auth import auth_bp
    from app.routes.report import report_bp
    from app.routes.oauth import oauth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(company_bp, url_prefix='/api')
    app.register_blueprint(auth_bp)  # /login, /signup 등 직접 접근
    app.register_blueprint(report_bp)
    app.register_blueprint(oauth_bp)  # 소셜 로그인
    
    return app
