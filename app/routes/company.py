# app/routes/company.py
# 기업 관련 API 라우트

from flask import Blueprint, jsonify, request

company_bp = Blueprint("company", __name__)

@company_bp.route("/search", methods=["GET"])
def search_company():
    # 기업 검색 API
    # TODO: 실제 검색 로직 구현
    query = request.args.get("q", "")
    market = request.args.get("market", "all")  # kospi, kosdaq, all
    
    return jsonify({
        "success": True,
        "query": query,
        "market": market,
        "results": []
    })

@company_bp.route("/<corp_code>", methods=["GET"])
def get_company_info(corp_code):
    # 기업 정보 조회 API
    # TODO: DART 서비스 연동
    return jsonify({
        "success": True,
        "corp_code": corp_code,
        "data": {}
    })

