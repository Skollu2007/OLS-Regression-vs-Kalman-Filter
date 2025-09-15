import numpy as np
from datetime import date
import json
import pandas as pd

def calc_pnl(shares1, shares2, p1N, p2N, p1X, p2X, pos_type):
    if pos_type == 'long':
        PnL = (p1X - p1N)*shares1 + (p2N - p2X)*shares2
    elif pos_type == 'short':
        PnL = (p1N - p1X)*shares1 + (p2X - p2N)*shares2

    return PnL



def calc_total_returns(trade_log_file):
    with open(trade_log_file, 'r') as f:
        trades = json.load(f)
    
    returns = 0
    for trade in trades:
        if 'pnl' in trade:
            returns += trade['pnl']
    
    return returns



def calc_sharpe(equity_curve, risk_free_rate=0.05):
    equity_curve = pd.Series(equity_curve)
    returns = equity_curve.pct_change().dropna()
    daily_risk_free = (1 + risk_free_rate) ** (1 / 252) - 1
    excess_returns = returns - daily_risk_free
    if excess_returns.std() == 0:
        return np.nan
    sharpe = np.sqrt(252) * (excess_returns.mean() / excess_returns.std())
    return sharpe


def max_drawdown(equity_curve):
    equity_curve = pd.Series(equity_curve)
    rolling_max = equity_curve.cummax()
    drawdown = equity_curve - rolling_max
    return abs(drawdown.min())

def win_rate(trade_log_file):
    with open(trade_log_file, 'r') as file:
        trades = json.load(file)
        

    trades_made = 0
    wins = 0

    for trade in trades:
        if 'pnl' in trade:
            if float(trade['pnl']) > 0:
                wins += 1
                trades_made += 1
            else:
                trades_made += 1

    return wins/trades_made

