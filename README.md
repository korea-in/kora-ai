# KORA AI  
**KO**SPI · **KO**SDAQ · **R**esearch · **A**nalyze

실시간 공시·뉴스·RAG 기반 기업 분석 보고서를 자동 생성하는 AI 웹 서비스

---

## 1. 프로젝트 개요
**프로젝트명**  
KORA AI

**결과물 형태**  
PC 웹앱 + AI 기업 분석 에이전트

**한 줄 요약**  
실시간 공시·뉴스·주가 데이터를 LLM이 분석해 핵심 기업 보고서를 자동 생성하는 서비스

---

## 2. 프로젝트 목적
많은 개인 투자자들이 차트나 기술적 분석에 의존해 투자 결정을 내리기 쉽다.  
하지만 기본적 분석(Fundamental Analysis)을 수행하기 위해서는  
공시·뉴스·재무 데이터·시장 이슈를 여러 플랫폼에서 직접 검색해야 하고,  
이 과정은 시간 소모가 크고 정보 격차도 발생한다.

KORA AI는 이러한 문제를 해결하기 위해  
**DART 공시, 최신 뉴스, 주가 데이터, GPT 분석을 하나로 통합한 실시간 기업 분석 자동화 시스템**을 만든다.  
사용자는 기업을 검색하기만 하면 주요 리스크·사업 인사이트·뉴스 흐름 등을 한 번에 확인할 수 있다.

---

## 3. 주요 기능

### 🔍 기업 검색
- 코스피·코스닥 시장 선택 및 자동 추천 검색
- 실시간 인기 기업 목록

### 📊 주가 분석
- 현재 주가 조회
- 1년간 주가 변동 추이
- 이동평균선 (5일, 20일, 60일, 120일)
- 거래량 추이 및 급증 감지

### 📈 밸류에이션 지표
- PER (주가수익비율)
- PBR (주가순자산비율)
- EPS (주당순이익)
- BPS (주당순자산)
- 배당수익률 / 주당배당금

### 🔬 기술적 지표
- RSI (상대강도지수) - 과매수/과매도 판단
- MFI (자금흐름지수) - 자금 유입/유출 분석

### 📰 뉴스 분석
- 네이버 뉴스 API 기반 최신 기사 수집
- 기업별 뉴스 감정 분석

### 📋 공시 분석
- DART API 실시간 공시 조회
- 정기 공시 목록
- 기업 개황 정보
- 배당에 관한 사항
- 주요 계정 지표
- 전체 재무제표

### 🤖 AI 보고서
- GPT API 기반 기업 분석 보고서 자동 생성
- 재무 건전성, 투자 리스크, 성장 가능성 분석

---

## 4. 사용 기술

### Backend
| 기술 | 용도 |
|------|------|
| Python Flask | 웹 프레임워크 |
| Firebase Admin SDK | 인증 및 데이터베이스 |

### Data APIs
| API | 용도 | 인증 |
|-----|------|------|
| **pykrx** | 한국거래소 주가 데이터 | 불필요 |
| **Naver Search API** | 뉴스 검색 | Client ID/Secret |
| **DART OpenAPI** | 전자공시 | API Key |

### AI / Analysis
| 기술 | 용도 |
|------|------|
| GPT API | 기업 분석 보고서 생성 |
| Chroma | RAG 기반 문서 탐색 |

### Frontend
| 기술 | 용도 |
|------|------|
| HTML/CSS/JS | 웹 UI |
| Noto Sans KR | 폰트 |
| Font Awesome | 아이콘 |

### Database
| 기술 | 용도 |
|------|------|
| Firebase Firestore | 사용자, 분석 기록, 인기 기업 |

---

## 5. 프로젝트 구조

```
kora-ai/
├── app/
│   ├── __init__.py           # Flask 앱 팩토리
│   ├── models/               # 데이터 모델
│   │   ├── user.py           # 사용자 모델
│   │   ├── analysis.py       # 분석 기록 모델
│   │   └── company.py        # 기업 모델
│   ├── routes/               # API 라우트
│   │   ├── main.py           # 메인 페이지
│   │   ├── auth.py           # 인증
│   │   └── company.py        # 기업 API
│   ├── services/             # 비즈니스 로직
│   │   ├── firebase/         # Firebase 서비스
│   │   │   ├── auth_service.py
│   │   │   └── firestore_service.py
│   │   ├── naver/            # 네이버 API
│   │   │   └── news_service.py
│   │   ├── dart/             # DART API
│   │   │   ├── get_company.py
│   │   │   ├── get_financials.py
│   │   │   └── ...
│   │   └── krx/              # 한국거래소 주가
│   │       └── stock_service.py
│   ├── static/               # 정적 파일
│   │   ├── css/
│   │   └── js/
│   └── templates/            # HTML 템플릿
├── data/                     # 기업 목록 데이터
├── config/                   # 설정 파일
├── .env                      # 환경 변수
├── requirements.txt          # 의존성
└── run.py                    # 실행 파일
```

---

## 6. 설치 및 실행

### 요구사항
- Python 3.10+
- Firebase 프로젝트
- Naver 개발자 계정
- DART OpenAPI 키

### 설치
```bash
# 저장소 클론
git clone https://github.com/your-repo/kora-ai.git
cd kora-ai

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 환경 변수 설정
```bash
# .env 파일 생성
cp config/env.sample .env

# .env 파일 편집
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
DART_API_KEY=your_dart_api_key
```

### 실행
```bash
python run.py
```
http://localhost:80 접속

---

## 7. API 사용 예시

### 주가 조회 (pykrx)
```python
from app.services.krx import get_stock_summary, get_moving_averages, get_valuation, get_technical_indicators

# 신한금융지주 종합 정보
summary = get_stock_summary("055550")
print(f"{summary.name}: {summary.current_price:,}원 ({summary.change_rate:+.2f}%)")

# 이동평균선
ma = get_moving_averages("055550")
print(f"추세: {ma['trend']}")
print(f"5일선: {ma['current']['ma5']:,}원")

# 밸류에이션 지표
val = get_valuation("055550")
print(f"PER: {val['per']}, PBR: {val['pbr']}, 배당수익률: {val['div_yield']}%")

# 기술적 지표 (RSI, MFI)
indicators = get_technical_indicators("055550")
print(f"RSI: {indicators['rsi']['value']} ({indicators['rsi']['signal']})")
print(f"MFI: {indicators['mfi']['value']} ({indicators['mfi']['signal']})")
```

### 뉴스 검색 (Naver API)
```python
from app.services.naver import search_company_news

# 신한금융지주 뉴스
result = search_company_news("신한금융지주", display=5)
for item in result.items:
    print(f"- {item.clean_title}")
```

### 기업 정보 (DART API)
```python
from app.services.dart.get_company import get_company_info

# 신한금융지주 기업 개황
info = get_company_info("00382199")
print(f"회사명: {info['corp_name']}")
print(f"대표자: {info['ceo_nm']}")
```

---

## 8. 사용자 흐름 (User Flow)
1. 사용자가 웹앱 접속  
2. 회원가입 / 로그인
3. 코스피 / 코스닥 시장 선택  
4. 기업명 검색 (자동 추천 기능 제공)  
5. 기업 선택 후 분석 요청  
6. AI 파이프라인 수행  
   - 실시간 주가 조회  
   - 공시 데이터 조회  
   - 뉴스 기사 수집  
   - GPT 분석·요약 생성  
7. 결과 화면에서 요약 보고서 제공  
8. 필요 시 추가 분석 요청

---

## License
This project is for internal development and research purposes.  
All rights reserved.

---
