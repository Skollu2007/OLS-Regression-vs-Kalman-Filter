import pandas as pd
import warnings
from joblib import Parallel, delayed
from itertools import combinations
import numpy as np
import statsmodels.tsa.stattools as ts
import yfinance as yf
import statsmodels.api as sm
from pykalman import KalmanFilter
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

def get_prices(tickers_list, date=None):
    prices = yf.download(tickers_list, start= (date - relativedelta(years=4)), end = date, interval='1d', auto_adjust=True, progress=False, timeout=30, ignore_tz=True)['Close']
    return prices

def correlation_filter(tickers_list, prices, date=None):
    prices = prices.loc[:date]
    filtered_pairs = []
    stock_pairs = combinations(tickers_list, 2)
    for pair in stock_pairs:
        try:
            p1 = prices[pair[0]]
            p2 = prices[pair[1]]
            p1 = p1.dropna()
            p2 = p2.dropna()

            df = pd.concat([p1, p2], axis=1).dropna()
            if df.shape[0] < 2:
                continue
            corr = df.corr().iloc[0, 1]

            if 0.8 < abs(corr) < 0.99:
                filtered_pairs.append(pair)
        except Exception:
            continue

    return filtered_pairs

def calc_spread(p1, p2, beta, alpha):
    spread = p1 - beta * p2 - alpha
    return spread

def process_pair_EG(pair, prices):
    try:
        p1 = prices[pair[0]].dropna()
        p2 = prices[pair[1]].dropna()
        df = pd.concat([p1, p2], axis=1).dropna()
        if df.shape[0] < 2:
            return None

        p1 = df.iloc[:, 0]
        p2 = df.iloc[:, 1]
        if np.std(p1) < 1e-8 or np.std(p2) < 1e-8:
            return None

        pvalue = ts.coint(p1, p2)[1]
        if pvalue < 0.025:
            model = sm.OLS(p1, sm.add_constant(p2)).fit()
            if np.isclose(model.ssr, 0):
                return None 
            beta = model.params.iloc[1]
            alpha = model.params.iloc[0]
            spread = calc_spread(p1, p2, beta, alpha)
            mean = spread.rolling(252).mean().iloc[-1]
            std = spread.rolling(252).std().iloc[-1]
            return (pair, round(float(beta), 4), round(float(alpha)), spread, mean, std)
        else:
            return None
    except:
        return None

def cointegration_test_EG(tickers_list, prices, date, n_jobs=4):
    prices = prices.loc[:date]
    filtered_pairs = correlation_filter(tickers_list, prices, date)

    results = Parallel(n_jobs=n_jobs)(
        delayed(process_pair_EG)(pair, prices) for pair in filtered_pairs
    )

    EG_pairs = [r for r in results if r is not None]
    final_pairs = [r[0] for r in EG_pairs]

    return EG_pairs, final_pairs


def process_pair_KF(pair, prices, date, trans_cov):
    try:
        p1 = prices[pair[0]].loc[:date].dropna()
        p2 = prices[pair[1]].loc[:date].dropna()
        df = pd.concat([p1, p2], axis=1).dropna()
        if df.shape[0] < 2:
            return None 

        p1 = df.iloc[:, 0]
        p2 = df.iloc[:, 1]

        obs_mat = np.vstack([p2, np.ones(len(p1))]).T[:, np.newaxis, :]
        kf = KalmanFilter(
            n_dim_obs=1, n_dim_state=2,
            initial_state_mean=[0, 0],
            initial_state_covariance=np.eye(2),
            transition_matrices=np.eye(2),
            observation_matrices=obs_mat,
            observation_covariance=1,
            transition_covariance=trans_cov
        )
        means, _ = kf.filter(p1)
        beta = pd.Series(means[:, 0], index=df.index)
        alpha = pd.Series(means[:, 1], index=df.index)
        spread = p1 - beta * p2 - alpha
        mean = spread.rolling(252).mean().iloc[-1]
        std = spread.rolling(252).std().iloc[-1]
        return (pair, round(float(beta.iloc[-1]), 4), spread, mean, std, alpha.iloc[-1])
    except:
        return None

def KF_calc(cointegrated_pairs, prices, date, n_jobs=4):

    delta = 0.0001
    trans_cov = (delta / (1 - delta)) * np.eye(2)

    results = Parallel(n_jobs=n_jobs)(
        delayed(process_pair_KF)(pair, prices, date, trans_cov) for pair in cointegrated_pairs
    )

    KF_pairs = [r for r in results if r is not None]

    return KF_pairs

