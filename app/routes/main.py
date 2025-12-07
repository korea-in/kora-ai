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
    import os
    
    # 이미 로그인된 경우 메인으로 이동
    if 'user_id' in session:
        return redirect(url_for('main.main_page'))
    
    error = request.args.get('error')
    
    # Firebase 설정 (구글 로그인용)
    firebase_config = {
        'api_key': os.getenv('FIREBASE_API_KEY', ''),
        'auth_domain': os.getenv('FIREBASE_AUTH_DOMAIN', ''),
        'project_id': os.getenv('FIREBASE_PROJECT_ID', ''),
    }
    
    print(f"[Auth] Firebase config: api_key={'set' if firebase_config['api_key'] else 'empty'}")
    
    return render_template('auth.html', error=error, firebase_config=firebase_config)


@main_bp.route('/main')
def main_page():
    """메인 검색 페이지"""
    # 로그인 체크
    if 'user_id' not in session:
        return redirect(url_for('main.auth'))
    
    user_name = session.get('user_name', '사용자')
    user_credits = session.get('user_credits', 500)
    return render_template('main.html', user_name=user_name, user_credits=user_credits)


@main_bp.route('/logout')
def logout():
    """로그아웃 처리"""
    session.clear()
    return redirect(url_for('main.auth'))


@main_bp.route('/about')
def about():
    """서비스 소개 페이지"""
    return render_template('about.html')


@main_bp.route('/reports')
def reports():
    """보고서함 페이지"""
    # 로그인 체크
    if 'user_id' not in session:
        return redirect(url_for('main.auth'))
    
    user_id = session.get('user_id', '')
    user_name = session.get('user_name', '사용자')
    user_credits = session.get('user_credits', 500)
    return render_template('reports.html', 
                         user_id=user_id,
                         user_name=user_name,
                         user_credits=user_credits)


@main_bp.route('/credits')
def credits():
    """크레딧 충전 페이지"""
    # 로그인 체크
    if 'user_id' not in session:
        return redirect(url_for('main.auth'))
    
    user_id = session.get('user_id')
    user_credits = session.get('user_credits', 500)
    total_used = 0
    total_purchased = 0
    
    # DB에서 최신 정보 조회
    if user_id:
        try:
            from app.services.firebase import get_db
            db = get_db()
            if db:
                doc = db.collection('users').document(user_id).get()
                if doc.exists:
                    data = doc.to_dict()
                    user_credits = data.get('credits', 500)
                    total_used = data.get('total_credits_used', 0)
                    total_purchased = data.get('total_credits_purchased', 0)
                    # 세션 동기화
                    session['user_credits'] = user_credits
        except Exception as e:
            print(f"Error fetching credits: {e}")
    
    return render_template('credits.html',
                         user_credits=user_credits,
                         total_used=total_used,
                         total_purchased=total_purchased)


@main_bp.route('/profile')
def profile():
    """개인정보 페이지"""
    # 로그인 체크
    if 'user_id' not in session:
        return redirect(url_for('main.auth'))
    
    user_name = session.get('user_name', '사용자')
    user_email = session.get('user_email', '')
    user_credits = session.get('user_credits', 500)
    phone_number = session.get('phone_number', '')
    preferred_market = session.get('preferred_market', 'kospi')
    email_notifications = session.get('email_notifications', True)
    subscription_tier = session.get('subscription_tier', 'Free')
    investment_type = session.get('investment_type', '')
    analysis_count = session.get('analysis_count', 0)
    
    return render_template('profile.html',
                         user_name=user_name,
                         user_email=user_email,
                         user_credits=user_credits,
                         phone_number=phone_number,
                         preferred_market=preferred_market,
                         email_notifications=email_notifications,
                         subscription_tier=subscription_tier,
                         investment_type=investment_type,
                         analysis_count=analysis_count,
                         member_days=1)


@main_bp.route('/investment-type')
def investment_type():
    """투자성향분석 페이지"""
    # 로그인 체크
    if 'user_id' not in session:
        return redirect(url_for('main.auth'))
    
    return render_template('investment_type.html')


@main_bp.route('/api/profile/investment-type', methods=['GET', 'POST'])
def investment_type_api():
    """투자성향 조회 및 저장 API"""
    from flask import jsonify
    
    user_id = session.get('user_id')
    
    if request.method == 'GET':
        # 저장된 투자성향 조회
        if not user_id:
            return jsonify({"success": False, "error": "로그인이 필요합니다."})
        
        try:
            from app.services.firebase import get_db
            db = get_db()
            
            if db:
                doc = db.collection('users').document(user_id).get()
                if doc.exists:
                    data = doc.to_dict()
                    investment_type = data.get('investment_type')
                    investment_score = data.get('investment_score')
                    analysis_date = data.get('investment_analysis_date')
                    
                    if investment_type:
                        return jsonify({
                            "success": True,
                            "investment_type": investment_type,
                            "investment_score": investment_score,
                            "analysis_date": analysis_date.strftime('%Y-%m-%d') if analysis_date else None
                        })
            
            return jsonify({"success": True, "investment_type": None})
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    
    else:  # POST
        # 투자성향 저장
        if not user_id:
            return jsonify({"success": False, "error": "로그인이 필요합니다."})
        
        try:
            data = request.get_json()
            inv_type = data.get('investment_type')
            inv_score = data.get('investment_score')
            
            from app.services.firebase import get_db
            from firebase_admin import firestore
            
            db = get_db()
            
            if db:
                db.collection('users').document(user_id).update({
                    'investment_type': inv_type,
                    'investment_score': inv_score,
                    'investment_analysis_date': firestore.SERVER_TIMESTAMP,
                    'updated_at': firestore.SERVER_TIMESTAMP
                })
                
                # 세션도 업데이트
                session['investment_type'] = inv_type
                
                return jsonify({"success": True})
            
            return jsonify({"success": False, "error": "DB 연결 실패"})
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})


@main_bp.route('/portfolio')
def portfolio():
    """포트폴리오 페이지"""
    # 로그인 체크
    if 'user_id' not in session:
        return redirect(url_for('main.auth'))
    
    user_name = session.get('user_name', '사용자')
    investment_type = session.get('investment_type', '')
    
    # 투자 성향 라벨 변환
    type_labels = {
        'conservative': '안정형',
        'moderately_conservative': '안정추구형',
        'moderate': '위험중립형',
        'moderately_aggressive': '적극투자형',
        'aggressive': '공격투자형'
    }
    investment_type_label = type_labels.get(investment_type, investment_type)
    
    # 투자 성향 점수 가져오기
    investment_score = 30  # 기본값
    user_id = session.get('user_id')
    if user_id:
        try:
            from app.services.firebase import get_db
            db = get_db()
            if db:
                doc = db.collection('users').document(user_id).get()
                if doc.exists:
                    investment_score = doc.to_dict().get('investment_score', 30)
        except:
            pass
    
    # 투자 성향 분석 여부 확인
    has_investment_type = bool(investment_type)
    user_credits = session.get('user_credits', 500)
    
    return render_template('portfolio.html',
                         user_name=user_name,
                         user_credits=user_credits,
                         investment_type=investment_type,
                         investment_type_label=investment_type_label,
                         investment_score=investment_score,
                         has_investment_type=has_investment_type)


# ============================================
# 크레딧 API
# ============================================

@main_bp.route('/api/credits/check')
def check_credits():
    """크레딧 확인 API"""
    from flask import jsonify
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "credits": 0, "error": "로그인 필요"})
    
    try:
        from app.services.firebase import get_user_credits
        credits = get_user_credits(user_id)
        return jsonify({"success": True, "credits": credits})
    except Exception as e:
        return jsonify({"success": False, "credits": 0, "error": str(e)})


# ============================================
# 포트폴리오 API
# ============================================

@main_bp.route('/api/portfolio/analyze', methods=['POST'])
def analyze_portfolio():
    """AI 포트폴리오 분석 API"""
    from flask import jsonify
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "로그인이 필요합니다."}), 401
    
    try:
        data = request.get_json()
        companies = data.get('companies', [])
        total_amount = data.get('total_amount', 10000000)
        investment_type = data.get('investment_type', 'moderate')
        investment_score = data.get('investment_score', 30)
        
        if len(companies) < 2:
            return jsonify({"success": False, "error": "최소 2개 이상의 기업이 필요합니다."}), 400
        
        # 크레딧 확인 및 차감 (200 크레딧)
        PORTFOLIO_COST = 200
        from app.services.firebase import get_user_credits, use_user_credits
        
        current_credits = get_user_credits(user_id)
        if current_credits < PORTFOLIO_COST:
            return jsonify({
                "success": False, 
                "error": f"크레딧이 부족합니다. (필요: {PORTFOLIO_COST}, 보유: {current_credits})"
            }), 400
        
        # AI 분석 요청
        from app.services.openai.analysis_service import chat_completion_json
        
        # 투자 성향에 따른 리스크 성향 설정
        risk_profiles = {
            'conservative': {'risk_tolerance': '낮음', 'stock_ratio': '20-40%', 'focus': '안정적 배당주, 대형주'},
            'moderately_conservative': {'risk_tolerance': '낮음-중간', 'stock_ratio': '30-50%', 'focus': '우량 배당주, 성장주 일부'},
            'moderate': {'risk_tolerance': '중간', 'stock_ratio': '40-60%', 'focus': '성장주와 가치주 균형'},
            'moderately_aggressive': {'risk_tolerance': '중간-높음', 'stock_ratio': '60-80%', 'focus': '성장주 중심, 테마주'},
            'aggressive': {'risk_tolerance': '높음', 'stock_ratio': '70-90%', 'focus': '고성장주, 소형주, 테마주'}
        }
        
        risk_profile = risk_profiles.get(investment_type, risk_profiles['moderate'])
        
        company_list = "\n".join([f"- {c['name']} ({c['code']}, {c['market']})" for c in companies])
        
        system_prompt = f"""당신은 KORA AI의 포트폴리오 전문가입니다.
사용자의 투자 성향과 선택한 기업들을 분석하여 최적의 포트폴리오 배분을 제안해주세요.

## 사용자 투자 성향
- 유형: {investment_type}
- 점수: {investment_score}/50
- 리스크 성향: {risk_profile['risk_tolerance']}
- 권장 주식 비중: {risk_profile['stock_ratio']}
- 투자 초점: {risk_profile['focus']}

## 선택한 기업
{company_list}

## 총 투자 금액
{total_amount:,}원

반드시 아래 JSON 형식으로만 응답하세요:
{{
    "allocations": [
        {{
            "code": "종목코드",
            "name": "기업명",
            "percentage": 비중(숫자, 합이 100),
            "opinion": "매수/보유/매도",
            "opinion_class": "buy/hold/sell",
            "reason": "배분 이유 (1문장)"
        }}
    ],
    "risk_score": 리스크점수(0-100),
    "risk_level": "낮음/중간/높음",
    "expected_return_min": 최소예상수익률(숫자),
    "expected_return_max": 최대예상수익률(숫자),
    "advice": "투자 성향을 고려한 종합 조언 (3-5문장, 구체적인 조언과 주의사항 포함)"
}}

## 배분 원칙
1. 사용자의 리스크 성향을 반드시 고려
2. 분산 투자 원칙 적용 (단일 종목 최대 40%)
3. 같은 업종 편중 방지
4. 보수적 투자 성향일수록 대형주, 우량주 비중 확대
5. 적극적 투자 성향일수록 성장주, 테마주 비중 가능"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "위 기업들로 포트폴리오를 구성해주세요."}
        ]
        
        analysis = chat_completion_json(messages, temperature=0.5, max_tokens=2000)
        
        if analysis:
            # 크레딧 차감
            use_user_credits(user_id, PORTFOLIO_COST, "포트폴리오 분석")
            session['user_credits'] = current_credits - PORTFOLIO_COST
            
            return jsonify({
                "success": True,
                "analysis": analysis,
                "credits_used": PORTFOLIO_COST
            })
        else:
            return jsonify({"success": False, "error": "AI 분석에 실패했습니다."}), 500
        
    except Exception as e:
        print(f"Portfolio analysis error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@main_bp.route('/api/portfolio/save', methods=['POST'])
def save_portfolio():
    """포트폴리오 저장 API"""
    from flask import jsonify
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "로그인이 필요합니다."}), 401
    
    try:
        data = request.get_json()
        companies = data.get('companies', [])
        name = data.get('name', '내 포트폴리오')
        
        from app.services.firebase import get_db
        from firebase_admin import firestore
        
        db = get_db()
        if not db:
            return jsonify({"success": False, "error": "DB 연결 실패"}), 500
        
        # 포트폴리오 저장
        portfolio_data = {
            'user_id': user_id,
            'name': name,
            'companies': companies,
            'created_at': firestore.SERVER_TIMESTAMP
        }
        
        doc_ref = db.collection('portfolios').add(portfolio_data)
        
        return jsonify({
            "success": True,
            "portfolio_id": doc_ref[1].id
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@main_bp.route('/api/credits/purchase', methods=['POST'])
def purchase_credits():
    """크레딧 충전 API"""
    from flask import jsonify
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"success": False, "error": "로그인이 필요합니다."}), 401
    
    try:
        data = request.get_json()
        credits_to_add = data.get('credits', 0)
        price = data.get('price', 0)
        method = data.get('method', 'card')
        
        if credits_to_add <= 0:
            return jsonify({"success": False, "error": "유효하지 않은 크레딧 양"}), 400
        
        from app.services.firebase import get_db
        from firebase_admin import firestore
        
        db = get_db()
        if not db:
            return jsonify({"success": False, "error": "DB 연결 실패"}), 500
        
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return jsonify({"success": False, "error": "사용자를 찾을 수 없습니다."}), 404
        
        user_data = user_doc.to_dict()
        current_credits = user_data.get('credits', 0)
        new_credits = current_credits + credits_to_add
        
        # 크레딧 업데이트
        user_ref.update({
            'credits': new_credits,
            'total_credits_purchased': firestore.Increment(credits_to_add),
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        
        # 충전 기록 저장
        db.collection('credit_history').add({
            'user_id': user_id,
            'amount': credits_to_add,
            'price': price,
            'method': method,
            'type': 'purchase',
            'reason': f'{credits_to_add} 크레딧 충전',
            'created_at': firestore.SERVER_TIMESTAMP
        })
        
        # 세션 업데이트
        session['user_credits'] = new_credits
        
        return jsonify({
            "success": True,
            "credits_added": credits_to_add,
            "credits_total": new_credits
        })
        
    except Exception as e:
        print(f"Error purchasing credits: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
