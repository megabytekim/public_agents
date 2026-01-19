"""pytest fixtures for utils tests"""
import sys
from pathlib import Path

# Add the parent directory to sys.path for utils module discovery
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock


@pytest.fixture
def sample_ohlcv_df():
    """샘플 OHLCV DataFrame 생성"""
    dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
    np.random.seed(42)

    base_price = 70000
    prices = base_price + np.cumsum(np.random.randn(60) * 1000)

    df = pd.DataFrame({
        '시가': (prices * 0.99).astype(int),
        '고가': (prices * 1.02).astype(int),
        '저가': (prices * 0.98).astype(int),
        '종가': prices.astype(int),
        '거래량': np.random.randint(1000000, 5000000, 60),
        '거래대금': np.random.randint(10000000000, 50000000000, 60),
        '등락률': np.random.randn(60) * 2,
    }, index=dates)

    return df


@pytest.fixture
def sample_close_series(sample_ohlcv_df):
    """종가 Series"""
    return sample_ohlcv_df['종가']


@pytest.fixture
def sample_high_series(sample_ohlcv_df):
    """고가 Series"""
    return sample_ohlcv_df['고가']


@pytest.fixture
def sample_low_series(sample_ohlcv_df):
    """저가 Series"""
    return sample_ohlcv_df['저가']


@pytest.fixture
def mock_pykrx_stock(mocker):
    """pykrx.stock 모듈 mock"""
    mock_stock = MagicMock()
    mocker.patch('utils.data_fetcher.stock', mock_stock)
    return mock_stock


@pytest.fixture
def sample_fundamental_df():
    """샘플 펀더멘털 DataFrame"""
    dates = pd.date_range(end=datetime.now(), periods=1, freq='D')
    return pd.DataFrame({
        'BPS': [50000],
        'PER': [15.5],
        'PBR': [1.4],
        'EPS': [4500],
        'DIV': [2.1],
        'DPS': [1500],
    }, index=dates)


@pytest.fixture
def sample_market_cap_df():
    """샘플 시가총액 DataFrame"""
    dates = pd.date_range(end=datetime.now(), periods=1, freq='D')
    return pd.DataFrame({
        '시가총액': [500000000000000],
        '거래량': [10000000],
        '거래대금': [700000000000],
        '상장주식수': [5969782550],
        '외국인보유주식수': [3000000000],
    }, index=dates)
