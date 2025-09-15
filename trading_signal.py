import pandas as pd
import statsmodels.api as sm
import numpy as np

entry_threshold = 2
exit_threshold = 0.5

def calc_z_score(spread, mean, std):
    z_score = (spread - mean) / std
    return z_score.iloc[-1]

    


def signal_generator(spread, mean, std):
    z_score = calc_z_score(spread, mean, std)

    if z_score > entry_threshold:
        return 'short'
    elif z_score < -entry_threshold:
        return 'long'
    elif abs(z_score) < exit_threshold:
        return 'exit'
    else:
        return 'hold'
    



