# tests/test_web_scraper.py
"""웹 스크래퍼 유틸리티 테스트"""
import pytest


def test_get_naver_stock_info_market_cap():
    """시가총액 파싱 테스트 - 숫자(억 단위)로 반환되어야 함"""
    from utils.web_scraper import get_naver_stock_info
    result = get_naver_stock_info("005930")  # 삼성전자

    assert result is not None
    assert 'market_cap' in result
    # market_cap은 숫자여야 함 (억 단위)
    assert isinstance(result['market_cap'], (int, float))
    assert result['market_cap'] > 0  # 삼성전자 시가총액은 양수


def test_get_naver_stock_info_market_cap_parsing_jo_format():
    """'조' 단위 포함 시가총액 파싱 테스트"""
    from utils.web_scraper import _parse_market_cap

    # "8조 9,014" 형식 (억 생략)
    result = _parse_market_cap("8조 9,014")
    assert result == 89014  # 8 * 10000 + 9014

    # "1조 2,345억" 형식
    result = _parse_market_cap("1조 2,345억")
    assert result == 12345  # 1 * 10000 + 2345


def test_get_naver_stock_info_market_cap_parsing_eok_format():
    """'억' 단위만 있는 시가총액 파싱 테스트"""
    from utils.web_scraper import _parse_market_cap

    # "9,014억" 형식
    result = _parse_market_cap("9,014억")
    assert result == 9014

    # "500억" 형식
    result = _parse_market_cap("500억")
    assert result == 500


def test_get_naver_stock_info_market_cap_parsing_edge_cases():
    """시가총액 파싱 엣지 케이스 테스트"""
    from utils.web_scraper import _parse_market_cap

    # 빈 문자열
    assert _parse_market_cap("") == 0

    # None
    assert _parse_market_cap(None) == 0

    # 숫자만 있는 경우
    assert _parse_market_cap("1234") == 1234
