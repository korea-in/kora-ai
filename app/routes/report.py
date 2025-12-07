"""
보고서 관련 라우트
- 보고서 페이지
- 보고서 생성 API
- AI 채팅 API
- 크레딧 차감 API
- 보고서 저장/조회 API
"""

from flask import Blueprint, render_template, request, jsonify, session
import json
import numpy as np

report_bp = Blueprint('report', __name__)

# 크레딧 비용 상수
CREDIT_COST_GENERATE_REPORT = 300  # 보고서 생성 비용
CREDIT_COST_VIEW_PUBLIC_REPORT = 100  # 공개 보고서 열람 비용


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
    """보고서 페이지 (새 보고서 생성)"""
    from flask import redirect, url_for
    
    # 로그인 체크
    if 'user_id' not in session:
        return redirect(url_for('main.auth'))
    
    company_name = request.args.get('company', '')
    ticker = request.args.get('ticker', '')
    corp_code = request.args.get('corp_code', '')
    market = request.args.get('market', 'KOSPI')
    request_text = request.args.get('request', '')  # 사용자 요청사항
    
    # 디버그 로그
    print(f"[DEBUG] Report page - company: {company_name}, ticker: {ticker}, corp_code: {corp_code}, request: {request_text}")
    
    # 필수 파라미터 체크 - 없으면 메인으로 리다이렉트
    if not company_name or not ticker:
        from flask import redirect, url_for
        print("[DEBUG] Missing company_name or ticker, redirecting to main")
        return redirect(url_for('main.main_page'))
    
    return render_template('report.html',
                         company_name=company_name,
                         ticker=ticker,
                         corp_code=corp_code,
                         market=market,
                         request_text=request_text)


@report_bp.route('/report/view/<report_id>')
def view_saved_report(report_id):
    """저장된 보고서 조회 페이지"""
    from flask import redirect, url_for
    
    # 로그인 체크
    if 'user_id' not in session:
        return redirect(url_for('main.auth'))
    
    user_id = session.get('user_id')
    
    from app.services.firebase import get_report_by_id, use_user_credits, get_user_credits
    
    report = get_report_by_id(report_id, user_id)
    
    if not report:
        return redirect(url_for('main.reports'))
    
    # 본인 보고서가 아닌 경우 크레딧 차감
    is_owner = report.get('is_owner', False)
    
    if not is_owner:
        current_credits = get_user_credits(user_id)
        
        if current_credits < CREDIT_COST_VIEW_PUBLIC_REPORT:
            # 크레딧 부족 - 크레딧 충전 페이지로 이동
            from flask import flash
            return redirect(url_for('main.credits'))
        
        # 크레딧 차감
        use_user_credits(
            user_id,
            CREDIT_COST_VIEW_PUBLIC_REPORT,
            f"공개 보고서 열람: {report.get('company_name')}"
        )
        
        # 세션 업데이트
        session['user_credits'] = current_credits - CREDIT_COST_VIEW_PUBLIC_REPORT
        print(f"[view_saved_report] 크레딧 차감: {user_id}, -{CREDIT_COST_VIEW_PUBLIC_REPORT}")
    
    return render_template('report_view.html',
                         report=report,
                         report_id=report_id,
                         is_owner=is_owner)


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
        print("[analyze_data] Starting AI analysis...")
        data = request.get_json()
        all_data = data.get('all_data')
        
        if not all_data:
            print("[analyze_data] No data to analyze")
            return jsonify({
                "success": False,
                "error": "분석할 데이터가 없습니다."
            }), 400
        
        print(f"[analyze_data] Company: {all_data.get('company_name')}, Ticker: {all_data.get('ticker')}")
        
        from app.services.report_service import request_ai_analysis
        analysis = request_ai_analysis(all_data)
        
        if analysis:
            print(f"[analyze_data] Analysis successful, score: {analysis.get('investment_score')}")
            return jsonify({
                "success": True,
                "analysis": analysis
            })
        else:
            print("[analyze_data] Analysis returned None")
            return jsonify({
                "success": False,
                "error": "AI 분석에 실패했습니다. OpenAI API를 확인하세요."
            }), 500
            
    except Exception as e:
        print(f"[analyze_data] Exception: {e}")
        import traceback
        traceback.print_exc()
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


@report_bp.route('/api/report/request-answer', methods=['POST'])
def answer_request():
    """사용자 요청사항에 대한 AI 답변"""
    try:
        data = request.get_json()
        company_name = data.get('company_name')
        request_text = data.get('request_text')
        report_context = data.get('report_context', '')
        
        if not request_text:
            return jsonify({
                "success": False,
                "error": "요청사항이 없습니다."
            }), 400
        
        from app.services.openai.analysis_service import chat_completion
        
        system_prompt = f"""당신은 KORA AI의 수석 증권 애널리스트입니다.
사용자가 {company_name}에 대해 질문했습니다.
제공된 분석 데이터를 기반으로 정확하고 상세하게 답변해주세요.

답변 형식:
- 질문에 대한 직접적인 답변을 먼저 제시
- 근거가 되는 데이터나 수치를 함께 설명
- 투자자 관점에서 유용한 인사이트 제공
- 3~5문장으로 간결하면서도 충실하게 답변

분석 데이터:
{report_context[:4000] if report_context else '데이터 없음'}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"질문: {request_text}"}
        ]
        
        answer = chat_completion(messages, temperature=0.5, max_tokens=800)
        
        if answer:
            return jsonify({
                "success": True,
                "answer": answer
            })
        else:
            return jsonify({
                "success": False,
                "error": "답변 생성 실패"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================
# 크레딧 및 보고서 저장 API
# ============================================

@report_bp.route('/api/report/save', methods=['POST'])
def save_report_api():
    """보고서 저장 및 크레딧 차감"""
    try:
        user_id = session.get('user_id')
        print(f"[save_report_api] user_id: {user_id}")
        
        if not user_id:
            print("[save_report_api] No user_id in session")
            return jsonify({
                "success": False,
                "error": "로그인이 필요합니다."
            }), 401
        
        data = request.get_json()
        company_name = data.get('company_name')
        ticker = data.get('ticker')
        market = data.get('market')
        analysis = data.get('analysis')
        raw_data = data.get('raw_data')
        
        print(f"[save_report_api] company: {company_name}, ticker: {ticker}, market: {market}")
        print(f"[save_report_api] analysis exists: {bool(analysis)}, raw_data exists: {bool(raw_data)}")
        
        if not all([company_name, ticker]):
            return jsonify({
                "success": False,
                "error": "필수 정보가 없습니다."
            }), 400
        
        from app.services.firebase import (
            use_user_credits, 
            save_report, 
            get_user_credits
        )
        
        # 크레딧 확인
        current_credits = get_user_credits(user_id)
        print(f"[save_report_api] current_credits: {current_credits}, required: {CREDIT_COST_GENERATE_REPORT}")
        
        if current_credits < CREDIT_COST_GENERATE_REPORT:
            return jsonify({
                "success": False,
                "error": f"크레딧이 부족합니다. (필요: {CREDIT_COST_GENERATE_REPORT}, 보유: {current_credits})"
            }), 400
        
        # 크레딧 차감
        credit_used = use_user_credits(
            user_id, 
            CREDIT_COST_GENERATE_REPORT,
            f"보고서 생성: {company_name}"
        )
        print(f"[save_report_api] credit_used result: {credit_used}")
        
        if not credit_used:
            return jsonify({
                "success": False,
                "error": "크레딧 차감에 실패했습니다."
            }), 500
        
        # 보고서 저장
        report_data = {
            'company_name': company_name,
            'ticker': ticker,
            'market': market,
            'analysis': analysis,
            'raw_data': raw_data
        }
        
        report_id = save_report(user_id, report_data)
        print(f"[save_report_api] save_report result: {report_id}")
        
        if report_id:
            # 세션 크레딧 업데이트
            new_credits = current_credits - CREDIT_COST_GENERATE_REPORT
            session['user_credits'] = new_credits
            print(f"[save_report_api] Session credits updated to: {new_credits}")
            
            return jsonify({
                "success": True,
                "report_id": report_id,
                "credits_used": CREDIT_COST_GENERATE_REPORT,
                "credits_remaining": new_credits
            })
        else:
            print("[save_report_api] save_report returned None")
            return jsonify({
                "success": False,
                "error": "보고서 저장에 실패했습니다."
            }), 500
            
    except Exception as e:
        print(f"[save_report_api] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/api/reports/my')
def get_my_reports():
    """내 보고서 목록 조회"""
    try:
        user_id = session.get('user_id')
        print(f"[get_my_reports] Session: {dict(session)}")
        print(f"[get_my_reports] user_id: {user_id}")
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "로그인이 필요합니다."
            }), 401
        
        from app.services.firebase import get_user_reports
        
        reports = get_user_reports(user_id)
        
        # 날짜 형식 변환
        for report in reports:
            if report.get('created_at'):
                try:
                    report['created_at'] = report['created_at'].strftime('%Y-%m-%d %H:%M')
                except:
                    pass
        
        print(f"[get_my_reports] Found {len(reports)} reports")
        
        return jsonify({
            "success": True,
            "reports": reports,
            "count": len(reports)
        })
        
    except Exception as e:
        print(f"[get_my_reports] Error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/api/reports/public')
def get_public_reports_api():
    """공개 보고서 목록 조회"""
    try:
        market = request.args.get('market', 'all')
        search = request.args.get('search', '')
        
        # 현재 로그인한 사용자의 보고서는 제외
        current_user_id = session.get('user_id')
        
        from app.services.firebase import get_public_reports
        
        reports = get_public_reports(
            limit=100, 
            market=market, 
            search=search,
            exclude_user_id=current_user_id  # 내 보고서 제외
        )
        
        return jsonify({
            "success": True,
            "reports": reports,
            "count": len(reports)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/api/reports/<report_id>')
def get_report_detail(report_id):
    """보고서 상세 조회 (공개 보고서 열람 시 크레딧 차감)"""
    try:
        user_id = session.get('user_id')
        
        from app.services.firebase import (
            get_report_by_id, 
            use_user_credits, 
            get_user_credits
        )
        
        report = get_report_by_id(report_id, user_id)
        
        if not report:
            return jsonify({
                "success": False,
                "error": "보고서를 찾을 수 없습니다."
            }), 404
        
        # 본인 보고서가 아닌 경우 크레딧 차감
        if not report.get('is_owner') and user_id:
            current_credits = get_user_credits(user_id)
            
            if current_credits < CREDIT_COST_VIEW_PUBLIC_REPORT:
                return jsonify({
                    "success": False,
                    "error": f"크레딧이 부족합니다. (필요: {CREDIT_COST_VIEW_PUBLIC_REPORT}, 보유: {current_credits})"
                }), 400
            
            # 크레딧 차감
            use_user_credits(
                user_id,
                CREDIT_COST_VIEW_PUBLIC_REPORT,
                f"보고서 열람: {report.get('company_name')}"
            )
            
            session['user_credits'] = current_credits - CREDIT_COST_VIEW_PUBLIC_REPORT
            report['credits_used'] = CREDIT_COST_VIEW_PUBLIC_REPORT
        
        return jsonify({
            "success": True,
            "report": report
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

