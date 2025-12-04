# app/__init__.py
# Flask 애플리케이션 팩토리

from flask import Flask

def create_app():
    # Flask 앱 생성
    app = Flask(__name__)
    
    # 설정 로드
    app.config["SECRET_KEY"] = "kora-ai-secret-key-change-in-production"
    
    # 블루프린트 등록
    from app.routes.main import main_bp
    from app.routes.company import company_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(company_bp, url_prefix="/api/company")
    
    return app

