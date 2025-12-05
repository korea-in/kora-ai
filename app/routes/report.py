"""
보고서 관련 라우트
- 보고서 페이지
- 보고서 생성 API
- AI 채팅 API
"""

from flask import Blueprint, render_template, request, jsonify, session
import json
import numpy as np

report_bp = Blueprint('report', __name__)


def convert_to_serializable(obj):
    """numpy/pandas 타입을 JSON 직렬화 가능한 타입으로 변환"""
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif hasattr(obj, 'to_dict'):
        return convert_to_serializable(obj.to_dict())
    elif obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    else:
        return str(obj)


@report_bp.route('/report')
def report_page():
    """보고서 페이지"""
    company_name = request.args.get('company', '')
    ticker = request.args.get('ticker', '')
    corp_code = request.args.get('corp_code', '')
    market = request.args.get('market', 'KOSPI')
    
    # 디버그 로그
    print(f"[DEBUG] Report page - company: {company_name}, ticker: {ticker}, corp_code: {corp_code}")
    
    # 필수 파라미터 체크 - 없으면 메인으로 리다이렉트
    if not company_name or not ticker:
        from flask import redirect, url_for
        print("[DEBUG] Missing company_name or ticker, redirecting to main")
        return redirect(url_for('main.main_page'))
    
    return render_template('report.html',
                         company_name=company_name,
                         ticker=ticker,
                         corp_code=corp_code,
                         market=market)


@report_bp.route('/api/report/generate', methods=['POST'])
def generate_report():
    """보고서 생성 API"""
    try:
        data = request.get_json()
        company_name = data.get('company_name')
        ticker = data.get('ticker')
        corp_code = data.get('corp_code', '')  # corp_code는 선택적
        
        if not all([company_name, ticker]):
            return jsonify({
                "success": False,
                "error": "기업명과 종목코드가 필요합니다."
            }), 400
        
        # 보고서 생성
        from app.services.report_service import generate_full_report
        report = generate_full_report(company_name, ticker, corp_code)
        
        if report:
            # 세션에 보고서 저장 (채팅용)
            session['current_report'] = json.dumps(report, ensure_ascii=False, default=str)
            
            return jsonify({
                "success": True,
                "report": report
            })
        else:
            return jsonify({
                "success": False,
                "error": "보고서 생성에 실패했습니다."
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/api/report/data', methods=['POST'])
def collect_data_only():
    """데이터 수집만 (AI 분석 제외) - 빠른 로딩용"""
    try:
        data = request.get_json()
        company_name = data.get('company_name')
        ticker = data.get('ticker')
        corp_code = data.get('corp_code', '')  # corp_code는 선택적
        
        if not all([company_name, ticker]):
            return jsonify({
                "success": False,
                "error": "기업명과 종목코드가 필요합니다."
            }), 400
        
        from app.services.report_service import collect_all_data
        all_data = collect_all_data(company_name, ticker, corp_code)
        
        # numpy/pandas 타입 변환
        serializable_data = convert_to_serializable(all_data)
        
        return jsonify({
            "success": True,
            "data": serializable_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/api/report/analyze', methods=['POST'])
def analyze_data():
    """수집된 데이터로 AI 분석 요청"""
    try:
        data = request.get_json()
        all_data = data.get('all_data')
        
        if not all_data:
            return jsonify({
                "success": False,
                "error": "분석할 데이터가 없습니다."
            }), 400
        
        from app.services.report_service import request_ai_analysis
        analysis = request_ai_analysis(all_data)
        
        if analysis:
            return jsonify({
                "success": True,
                "analysis": analysis
            })
        else:
            return jsonify({
                "success": False,
                "error": "AI 분석에 실패했습니다."
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/api/report/chat', methods=['POST'])
def chat_with_report():
    """보고서 기반 AI 채팅"""
    try:
        data = request.get_json()
        user_message = data.get('message')
        report_context = data.get('report_context')
        
        if not user_message:
            return jsonify({
                "success": False,
                "error": "메시지가 없습니다."
            }), 400
        
        # 세션에서 보고서 컨텍스트 가져오기
        if not report_context and 'current_report' in session:
            report_context = session['current_report']
        
        from app.services.openai.analysis_service import chat_completion
        
        system_prompt = f"""당신은 KORA AI 투자 상담사입니다.
사용자가 기업 분석 보고서에 대해 질문하면 친절하게 답변해주세요.
답변은 간결하고 명확하게 해주세요.

현재 분석 중인 보고서 정보:
{report_context[:3000] if report_context else '보고서 정보 없음'}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        response = chat_completion(messages, temperature=0.7, max_tokens=500)
        
        if response:
            return jsonify({
                "success": True,
                "response": response
            })
        else:
            return jsonify({
                "success": False,
                "error": "응답 생성에 실패했습니다."
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/api/report/price-history/<ticker>')
def get_price_history(ticker):
    """차트용 가격 히스토리 API"""
    try:
        days = request.args.get('days', 365, type=int)
        
        from app.services.krx.stock_service import get_price_history as fetch_price_history
        history = fetch_price_history(ticker, days=days)
        
        if history:
            data = [
                {
                    "date": h.date,
                    "open": h.open,
                    "high": h.high,
                    "low": h.low,
                    "close": h.close,
                    "volume": h.volume
                }
                for h in history
            ]
            return jsonify({"success": True, "data": data})
        else:
            return jsonify({"success": False, "error": "데이터 없음"}), 404
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

