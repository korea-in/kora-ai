"""
KRX 주식 데이터 서비스
pykrx 라이브러리를 사용한 한국거래소 공식 데이터 조회

기능:
- 현재 주가 조회
- 1년간 주가 변동 추이
- 이동평균선 계산
- 거래량 추이 조회
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from pykrx import stock


# ============================================
# 데이터 클래스
# ============================================

@dataclass
class StockPrice:
    """
    주식 가격 데이터
    """
    date: str                    # 날짜 (YYYY-MM-DD)
    open: int                    # 시가
    high: int                    # 고가
    low: int                     # 저가
    close: int                   # 종가
    volume: int                  # 거래량
    change_rate: float = 0.0    # 등락률 (%)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'date': self.date,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'change_rate': self.change_rate
        }


@dataclass
class StockSummary:
    """
    주식 요약 정보
    """
    ticker: str                  # 종목코드
    name: str                    # 종목명
    market: str                  # 시장 (KOSPI/KOSDAQ)
    
    # 현재가 정보
    current_price: int = 0       # 현재가 (최근 종가)
    change: int = 0              # 전일 대비
    change_rate: float = 0.0     # 등락률 (%)
    
    # 당일 정보
    open: int = 0                # 시가
    high: int = 0                # 고가
    low: int = 0                 # 저가
    volume: int = 0              # 거래량
    
    # 52주 정보
    high_52w: int = 0            # 52주 최고가
    low_52w: int = 0             # 52주 최저가
    
    # 이동평균
    ma5: int = 0                 # 5일 이동평균
    ma20: int = 0                # 20일 이동평균
    ma60: int = 0                # 60일 이동평균
    ma120: int = 0               # 120일 이동평균
    
    # 메타
    last_updated: str = ""       # 마지막 업데이트 날짜
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'ticker': self.ticker,
            'name': self.name,
            'market': self.market,
            'current_price': self.current_price,
            'change': self.change,
            'change_rate': self.change_rate,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'volume': self.volume,
            'high_52w': self.high_52w,
            'low_52w': self.low_52w,
            'ma5': self.ma5,
            'ma20': self.ma20,
            'ma60': self.ma60,
            'ma120': self.ma120,
            'last_updated': self.last_updated
        }


# ============================================
# 유틸리티 함수
# ============================================

def _get_date_str(date: datetime = None) -> str:
    """날짜를 YYYYMMDD 형식 문자열로 변환"""
    if date is None:
        date = datetime.now()
    return date.strftime("%Y%m%d")


def _get_latest_trading_date() -> str:
    """가장 최근 거래일 조회"""
    today = datetime.now()
    # 최근 7일 내 거래일 찾기
    for i in range(7):
        date = today - timedelta(days=i)
        date_str = _get_date_str(date)
        try:
            df = stock.get_market_ohlcv(date_str, date_str, "005930")  # 삼성전자로 테스트
            if not df.empty:
                return date_str
        except:
            continue
    return _get_date_str(today)


def _get_stock_name(ticker: str) -> str:
    """종목코드로 종목명 조회"""
    try:
        return stock.get_market_ticker_name(ticker)
    except:
        return ""


def _get_market_type(ticker: str) -> str:
    """종목코드로 시장 구분 조회"""
    try:
        kospi_tickers = stock.get_market_ticker_list(market="KOSPI")
        if ticker in kospi_tickers:
            return "KOSPI"
        return "KOSDAQ"
    except:
        return "KOSPI"


# ============================================
# 주가 조회 함수
# ============================================

def get_current_price(ticker: str) -> Optional[StockPrice]:
    """
    현재 주가 조회 (최근 거래일 종가)
    
    Args:
        ticker: 종목코드 (예: "055550")
        
    Returns:
        StockPrice 객체 또는 None
        
    Example:
        >>> price = get_current_price("055550")  # 신한금융지주
        >>> print(f"현재가: {price.close:,}원")
    """
    try:
        end_date = _get_latest_trading_date()
        start_date = (datetime.strptime(end_date, "%Y%m%d") - timedelta(days=7)).strftime("%Y%m%d")
        
        df = stock.get_market_ohlcv(start_date, end_date, ticker)
        
        if df.empty:
            return None
        
        # 가장 최근 데이터
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        change_rate = ((latest['종가'] - prev['종가']) / prev['종가'] * 100) if prev['종가'] > 0 else 0
        
        return StockPrice(
            date=df.index[-1].strftime("%Y-%m-%d"),
            open=int(latest['시가']),
            high=int(latest['고가']),
            low=int(latest['저가']),
            close=int(latest['종가']),
            volume=int(latest['거래량']),
            change_rate=round(change_rate, 2)
        )
        
    except Exception as e:
        print(f"Error fetching current price: {e}")
        return None


def get_price_history(
    ticker: str,
    days: int = 30
) -> List[StockPrice]:
    """
    일별 주가 이력 조회
    
    Args:
        ticker: 종목코드
        days: 조회 기간 (일)
        
    Returns:
        StockPrice 객체 리스트
        
    Example:
        >>> history = get_price_history("055550", days=30)
        >>> for price in history[-5:]:
        ...     print(f"{price.date}: {price.close:,}원")
    """
    try:
        end_date = _get_latest_trading_date()
        start_date = (datetime.strptime(end_date, "%Y%m%d") - timedelta(days=days + 10)).strftime("%Y%m%d")
        
        df = stock.get_market_ohlcv(start_date, end_date, ticker)
        
        if df.empty:
            return []
        
        # 등락률 계산
        df['change_rate'] = df['종가'].pct_change() * 100
        
        result = []
        for idx, row in df.iterrows():
            result.append(StockPrice(
                date=idx.strftime("%Y-%m-%d"),
                open=int(row['시가']),
                high=int(row['고가']),
                low=int(row['저가']),
                close=int(row['종가']),
                volume=int(row['거래량']),
                change_rate=round(row['change_rate'], 2) if pd.notna(row['change_rate']) else 0.0
            ))
        
        return result[-days:] if len(result) > days else result
        
    except Exception as e:
        print(f"Error fetching price history: {e}")
        return []


def get_yearly_trend(ticker: str) -> Dict[str, Any]:
    """
    최근 1년간 주가 변동 추이
    
    Args:
        ticker: 종목코드
        
    Returns:
        연간 추이 데이터 딕셔너리
        
    Example:
        >>> trend = get_yearly_trend("055550")
        >>> print(f"1년 수익률: {trend['return_rate']}%")
    """
    try:
        end_date = _get_latest_trading_date()
        start_date = (datetime.strptime(end_date, "%Y%m%d") - timedelta(days=365)).strftime("%Y%m%d")
        
        df = stock.get_market_ohlcv(start_date, end_date, ticker)
        
        if df.empty:
            return {}
        
        # 기본 통계
        first_price = int(df.iloc[0]['종가'])
        last_price = int(df.iloc[-1]['종가'])
        high_price = int(df['고가'].max())
        low_price = int(df['저가'].min())
        avg_volume = int(df['거래량'].mean())
        
        # 수익률
        return_rate = round((last_price - first_price) / first_price * 100, 2)
        
        # 월별 데이터 (차트용)
        df['month'] = df.index.to_period('M')
        monthly = df.groupby('month').agg({
            '시가': 'first',
            '고가': 'max',
            '저가': 'min',
            '종가': 'last',
            '거래량': 'sum'
        })
        
        monthly_data = []
        for idx, row in monthly.iterrows():
            monthly_data.append({
                'month': str(idx),
                'open': int(row['시가']),
                'high': int(row['고가']),
                'low': int(row['저가']),
                'close': int(row['종가']),
                'volume': int(row['거래량'])
            })
        
        return {
            'ticker': ticker,
            'period': f"{start_date[:4]}-{start_date[4:6]} ~ {end_date[:4]}-{end_date[4:6]}",
            'first_price': first_price,
            'last_price': last_price,
            'high_price': high_price,
            'low_price': low_price,
            'return_rate': return_rate,
            'avg_volume': avg_volume,
            'trading_days': len(df),
            'monthly_data': monthly_data
        }
        
    except Exception as e:
        print(f"Error fetching yearly trend: {e}")
        return {}


def get_moving_averages(
    ticker: str,
    periods: List[int] = [5, 20, 60, 120]
) -> Dict[str, Any]:
    """
    이동평균선 계산
    
    Args:
        ticker: 종목코드
        periods: 이동평균 기간 리스트 (기본: 5, 20, 60, 120일)
        
    Returns:
        이동평균선 데이터 딕셔너리
        
    Example:
        >>> ma = get_moving_averages("055550")
        >>> print(f"20일선: {ma['current']['ma20']:,}원")
    """
    try:
        # 가장 긴 기간 + 여유분
        max_period = max(periods) + 30
        end_date = _get_latest_trading_date()
        start_date = (datetime.strptime(end_date, "%Y%m%d") - timedelta(days=max_period * 2)).strftime("%Y%m%d")
        
        df = stock.get_market_ohlcv(start_date, end_date, ticker)
        
        if df.empty:
            return {}
        
        # 이동평균 계산
        for period in periods:
            df[f'ma{period}'] = df['종가'].rolling(window=period).mean()
        
        # 현재 이동평균값
        latest = df.iloc[-1]
        current_ma = {}
        for period in periods:
            ma_val = latest[f'ma{period}']
            current_ma[f'ma{period}'] = int(ma_val) if pd.notna(ma_val) else 0
        
        # 골든크로스/데드크로스 체크
        signals = []
        if len(df) > 1:
            prev = df.iloc[-2]
            # 5일선과 20일선
            if pd.notna(latest['ma5']) and pd.notna(latest['ma20']):
                if prev['ma5'] < prev['ma20'] and latest['ma5'] > latest['ma20']:
                    signals.append("골든크로스 (5일선 > 20일선)")
                elif prev['ma5'] > prev['ma20'] and latest['ma5'] < latest['ma20']:
                    signals.append("데드크로스 (5일선 < 20일선)")
        
        # 추세 판단
        current_price = int(latest['종가'])
        trend = "중립"
        if current_ma.get('ma20', 0) > 0:
            if current_price > current_ma['ma20'] and current_ma['ma5'] > current_ma['ma20']:
                trend = "상승 추세"
            elif current_price < current_ma['ma20'] and current_ma['ma5'] < current_ma['ma20']:
                trend = "하락 추세"
        
        # 최근 30일 이동평균 데이터 (차트용)
        recent_df = df.tail(30)
        ma_history = []
        for idx, row in recent_df.iterrows():
            data = {'date': idx.strftime("%Y-%m-%d"), 'close': int(row['종가'])}
            for period in periods:
                ma_val = row[f'ma{period}']
                data[f'ma{period}'] = int(ma_val) if pd.notna(ma_val) else None
            ma_history.append(data)
        
        return {
            'ticker': ticker,
            'current_price': current_price,
            'current': current_ma,
            'trend': trend,
            'signals': signals,
            'history': ma_history
        }
        
    except Exception as e:
        print(f"Error calculating moving averages: {e}")
        return {}


def get_volume_trend(ticker: str, days: int = 30) -> Dict[str, Any]:
    """
    거래량 추이 조회
    
    Args:
        ticker: 종목코드
        days: 조회 기간 (일)
        
    Returns:
        거래량 추이 데이터 딕셔너리
        
    Example:
        >>> volume = get_volume_trend("055550")
        >>> print(f"평균 거래량: {volume['avg_volume']:,}주")
    """
    try:
        end_date = _get_latest_trading_date()
        start_date = (datetime.strptime(end_date, "%Y%m%d") - timedelta(days=days + 10)).strftime("%Y%m%d")
        
        df = stock.get_market_ohlcv(start_date, end_date, ticker)
        
        if df.empty:
            return {}
        
        df = df.tail(days)
        
        # 거래량 통계
        avg_volume = int(df['거래량'].mean())
        max_volume = int(df['거래량'].max())
        min_volume = int(df['거래량'].min())
        latest_volume = int(df.iloc[-1]['거래량'])
        
        # 거래량 이동평균
        df['vol_ma5'] = df['거래량'].rolling(window=5).mean()
        df['vol_ma20'] = df['거래량'].rolling(window=20).mean()
        
        # 거래량 급증 체크 (20일 평균 대비 2배 이상)
        vol_ma20 = df['vol_ma20'].iloc[-1]
        volume_surge = latest_volume > vol_ma20 * 2 if pd.notna(vol_ma20) and vol_ma20 > 0 else False
        
        # 일별 거래량 데이터
        volume_history = []
        for idx, row in df.iterrows():
            volume_history.append({
                'date': idx.strftime("%Y-%m-%d"),
                'volume': int(row['거래량']),
                'close': int(row['종가']),
                'vol_ma5': int(row['vol_ma5']) if pd.notna(row['vol_ma5']) else None,
                'vol_ma20': int(row['vol_ma20']) if pd.notna(row['vol_ma20']) else None
            })
        
        return {
            'ticker': ticker,
            'period_days': days,
            'avg_volume': avg_volume,
            'max_volume': max_volume,
            'min_volume': min_volume,
            'latest_volume': latest_volume,
            'volume_surge': volume_surge,
            'history': volume_history
        }
        
    except Exception as e:
        print(f"Error fetching volume trend: {e}")
        return {}


def get_stock_summary(ticker: str) -> Optional[StockSummary]:
    """
    주식 종합 요약 정보 조회
    
    Args:
        ticker: 종목코드
        
    Returns:
        StockSummary 객체 또는 None
        
    Example:
        >>> summary = get_stock_summary("055550")  # 신한금융지주
        >>> print(f"{summary.name}: {summary.current_price:,}원 ({summary.change_rate:+.2f}%)")
    """
    try:
        # 기본 정보
        name = _get_stock_name(ticker)
        market = _get_market_type(ticker)
        
        # 현재가 조회
        current = get_current_price(ticker)
        if not current:
            return None
        
        # 이동평균
        ma_data = get_moving_averages(ticker)
        
        # 52주 최고/최저
        yearly = get_yearly_trend(ticker)
        
        # 전일 대비
        history = get_price_history(ticker, days=2)
        change = 0
        if len(history) >= 2:
            change = history[-1].close - history[-2].close
        
        return StockSummary(
            ticker=ticker,
            name=name,
            market=market,
            current_price=current.close,
            change=change,
            change_rate=current.change_rate,
            open=current.open,
            high=current.high,
            low=current.low,
            volume=current.volume,
            high_52w=yearly.get('high_price', 0),
            low_52w=yearly.get('low_price', 0),
            ma5=ma_data.get('current', {}).get('ma5', 0),
            ma20=ma_data.get('current', {}).get('ma20', 0),
            ma60=ma_data.get('current', {}).get('ma60', 0),
            ma120=ma_data.get('current', {}).get('ma120', 0),
            last_updated=current.date
        )
        
    except Exception as e:
        print(f"Error fetching stock summary: {e}")
        return None


# ============================================
# 밸류에이션 지표 (PER, PBR, 배당수익률)
# ============================================

def get_valuation(ticker: str) -> Dict[str, Any]:
    """
    밸류에이션 지표 조회 (PER, PBR, 배당수익률)
    
    Args:
        ticker: 종목코드
        
    Returns:
        밸류에이션 지표 딕셔너리
        
    Example:
        >>> val = get_valuation("055550")  # 신한금융지주
        >>> print(f"PER: {val['per']}, PBR: {val['pbr']}")
    """
    try:
        date = _get_latest_trading_date()
        
        # 개별 종목 기본 지표
        df = stock.get_market_fundamental(date, date, ticker)
        
        if df.empty:
            return {}
        
        row = df.iloc[0]
        
        return {
            'ticker': ticker,
            'date': date[:4] + '-' + date[4:6] + '-' + date[6:],
            'per': round(float(row['PER']), 2) if pd.notna(row['PER']) else None,
            'pbr': round(float(row['PBR']), 2) if pd.notna(row['PBR']) else None,
            'eps': int(row['EPS']) if pd.notna(row['EPS']) else None,
            'bps': int(row['BPS']) if pd.notna(row['BPS']) else None,
            'div_yield': round(float(row['DIV']), 2) if pd.notna(row['DIV']) else None,  # 배당수익률
            'dps': int(row['DPS']) if pd.notna(row['DPS']) else None,  # 주당배당금
        }
        
    except Exception as e:
        print(f"Error fetching valuation: {e}")
        return {}


# ============================================
# 기술적 지표 (RSI, MFI)
# ============================================

def calculate_rsi(ticker: str, period: int = 14) -> Dict[str, Any]:
    """
    RSI (Relative Strength Index) 계산
    
    - RSI > 70: 과매수 구간 (매도 신호)
    - RSI < 30: 과매도 구간 (매수 신호)
    
    Args:
        ticker: 종목코드
        period: RSI 기간 (기본 14일)
        
    Returns:
        RSI 데이터 딕셔너리
        
    Example:
        >>> rsi = calculate_rsi("055550")
        >>> print(f"RSI(14): {rsi['value']}")
    """
    try:
        # RSI 계산을 위해 충분한 데이터 필요
        days_needed = period * 3
        end_date = _get_latest_trading_date()
        start_date = (datetime.strptime(end_date, "%Y%m%d") - timedelta(days=days_needed)).strftime("%Y%m%d")
        
        df = stock.get_market_ohlcv(start_date, end_date, ticker)
        
        if df.empty or len(df) < period + 1:
            return {}
        
        # 가격 변화
        delta = df['종가'].diff()
        
        # 상승/하락 분리
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        # 평균 계산 (Wilder's smoothing)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # RS 및 RSI 계산
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = round(float(rsi.iloc[-1]), 2) if pd.notna(rsi.iloc[-1]) else None
        
        # 신호 판단
        signal = "중립"
        if current_rsi is not None:
            if current_rsi >= 70:
                signal = "과매수"
            elif current_rsi <= 30:
                signal = "과매도"
            elif current_rsi >= 50:
                signal = "강세"
            else:
                signal = "약세"
        
        # 최근 5일 RSI 히스토리
        rsi_history = []
        for i in range(-5, 0):
            if pd.notna(rsi.iloc[i]):
                rsi_history.append({
                    'date': df.index[i].strftime("%Y-%m-%d"),
                    'rsi': round(float(rsi.iloc[i]), 2)
                })
        
        return {
            'ticker': ticker,
            'period': period,
            'value': current_rsi,
            'signal': signal,
            'overbought': current_rsi >= 70 if current_rsi else False,
            'oversold': current_rsi <= 30 if current_rsi else False,
            'history': rsi_history
        }
        
    except Exception as e:
        print(f"Error calculating RSI: {e}")
        return {}


def calculate_mfi(ticker: str, period: int = 14) -> Dict[str, Any]:
    """
    MFI (Money Flow Index) 계산
    
    - RSI의 거래량 가중 버전
    - MFI > 80: 과매수 구간
    - MFI < 20: 과매도 구간
    
    Args:
        ticker: 종목코드
        period: MFI 기간 (기본 14일)
        
    Returns:
        MFI 데이터 딕셔너리
        
    Example:
        >>> mfi = calculate_mfi("055550")
        >>> print(f"MFI(14): {mfi['value']}")
    """
    try:
        # MFI 계산을 위해 충분한 데이터 필요
        days_needed = period * 3
        end_date = _get_latest_trading_date()
        start_date = (datetime.strptime(end_date, "%Y%m%d") - timedelta(days=days_needed)).strftime("%Y%m%d")
        
        df = stock.get_market_ohlcv(start_date, end_date, ticker)
        
        if df.empty or len(df) < period + 1:
            return {}
        
        # Typical Price (고가 + 저가 + 종가) / 3
        typical_price = (df['고가'] + df['저가'] + df['종가']) / 3
        
        # Raw Money Flow = Typical Price × Volume
        raw_money_flow = typical_price * df['거래량']
        
        # Money Flow 방향 결정
        tp_diff = typical_price.diff()
        
        positive_flow = raw_money_flow.where(tp_diff > 0, 0)
        negative_flow = raw_money_flow.where(tp_diff < 0, 0)
        
        # 기간 합계
        positive_sum = positive_flow.rolling(window=period).sum()
        negative_sum = negative_flow.rolling(window=period).sum()
        
        # Money Flow Ratio
        mfr = positive_sum / negative_sum
        
        # MFI 계산
        mfi = 100 - (100 / (1 + mfr))
        
        current_mfi = round(float(mfi.iloc[-1]), 2) if pd.notna(mfi.iloc[-1]) else None
        
        # 신호 판단
        signal = "중립"
        if current_mfi is not None:
            if current_mfi >= 80:
                signal = "과매수"
            elif current_mfi <= 20:
                signal = "과매도"
            elif current_mfi >= 50:
                signal = "자금 유입"
            else:
                signal = "자금 유출"
        
        # 최근 5일 MFI 히스토리
        mfi_history = []
        for i in range(-5, 0):
            if pd.notna(mfi.iloc[i]):
                mfi_history.append({
                    'date': df.index[i].strftime("%Y-%m-%d"),
                    'mfi': round(float(mfi.iloc[i]), 2)
                })
        
        return {
            'ticker': ticker,
            'period': period,
            'value': current_mfi,
            'signal': signal,
            'overbought': current_mfi >= 80 if current_mfi else False,
            'oversold': current_mfi <= 20 if current_mfi else False,
            'history': mfi_history
        }
        
    except Exception as e:
        print(f"Error calculating MFI: {e}")
        return {}


def get_technical_indicators(ticker: str) -> Dict[str, Any]:
    """
    주요 기술적 지표 종합 조회
    
    Args:
        ticker: 종목코드
        
    Returns:
        기술적 지표 종합 딕셔너리
        
    Example:
        >>> indicators = get_technical_indicators("055550")
        >>> print(f"RSI: {indicators['rsi']['value']}, MFI: {indicators['mfi']['value']}")
    """
    rsi = calculate_rsi(ticker)
    mfi = calculate_mfi(ticker)
    valuation = get_valuation(ticker)
    
    # 종합 신호 판단
    signals = []
    
    if rsi.get('overbought'):
        signals.append("RSI 과매수")
    elif rsi.get('oversold'):
        signals.append("RSI 과매도")
    
    if mfi.get('overbought'):
        signals.append("MFI 과매수")
    elif mfi.get('oversold'):
        signals.append("MFI 과매도")
    
    return {
        'ticker': ticker,
        'rsi': rsi,
        'mfi': mfi,
        'valuation': valuation,
        'signals': signals
    }


# ============================================
# 테스트
# ============================================

if __name__ == "__main__":
    # 신한금융지주 테스트
    ticker = "055550"
    
    print("=" * 60)
    print("신한금융지주 주식 데이터 조회")
    print("=" * 60)
    
    # 1. 현재가
    print("\n[현재가]")
    price = get_current_price(ticker)
    if price:
        print(f"날짜: {price.date}")
        print(f"종가: {price.close:,}원")
        print(f"등락률: {price.change_rate:+.2f}%")
    
    # 2. 종합 요약
    print("\n[종합 요약]")
    summary = get_stock_summary(ticker)
    if summary:
        print(f"종목: {summary.name} ({summary.ticker})")
        print(f"현재가: {summary.current_price:,}원 ({summary.change_rate:+.2f}%)")
        print(f"52주 최고/최저: {summary.high_52w:,} / {summary.low_52w:,}")
        print(f"이동평균: 5일 {summary.ma5:,} | 20일 {summary.ma20:,} | 60일 {summary.ma60:,}")
    
    # 3. 이동평균선
    print("\n[이동평균선]")
    ma = get_moving_averages(ticker)
    if ma:
        print(f"추세: {ma.get('trend')}")
        print(f"시그널: {ma.get('signals')}")
    
    # 4. 거래량
    print("\n[거래량]")
    volume = get_volume_trend(ticker, days=20)
    if volume:
        print(f"평균 거래량: {volume['avg_volume']:,}")
        print(f"최근 거래량: {volume['latest_volume']:,}")
        print(f"거래량 급증: {'예' if volume['volume_surge'] else '아니오'}")
    
    # 5. 밸류에이션 지표
    print("\n[밸류에이션]")
    val = get_valuation(ticker)
    if val:
        print(f"PER: {val.get('per')}")
        print(f"PBR: {val.get('pbr')}")
        print(f"배당수익률: {val.get('div_yield')}%")
        print(f"EPS: {val.get('eps'):,}원" if val.get('eps') else "EPS: N/A")
        print(f"BPS: {val.get('bps'):,}원" if val.get('bps') else "BPS: N/A")
    
    # 6. RSI
    print("\n[RSI]")
    rsi = calculate_rsi(ticker)
    if rsi:
        print(f"RSI(14): {rsi.get('value')}")
        print(f"신호: {rsi.get('signal')}")
    
    # 7. MFI
    print("\n[MFI]")
    mfi = calculate_mfi(ticker)
    if mfi:
        print(f"MFI(14): {mfi.get('value')}")
        print(f"신호: {mfi.get('signal')}")
    
    # 8. 기술적 지표 종합
    print("\n[기술적 지표 종합]")
    indicators = get_technical_indicators(ticker)
    if indicators.get('signals'):
        print(f"주의 신호: {', '.join(indicators['signals'])}")
    else:
        print("특별한 신호 없음")

