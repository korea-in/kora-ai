# run.py
# Flask 애플리케이션 실행 파일

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

