from pair_selector import cointegration_test_EG, KF_calc, get_prices, calc_spread, process_pair_KF
from symbols import get_stocks
from trading_signal import calc_z_score, signal_generator
from datetime import datetime, date, timedelta
import json
from calc import calc_pnl, calc_sharpe, calc_total_returns, max_drawdown, win_rate
import pandas as pd
import time
import numpy as np

def get_date_range(start_date, end_date):
    dates = pd.bdate_range(start_date, end_date)
    return dates


def main():

    #choose how much you want to allocate per trade
    capital_per_trade = int(5000)

    #at the start of a backtst, clear previous trade logs
    with open('kf_trade_log.json', 'w') as f:
        json.dump([], f)

    with open('eg_trade_log.json', 'w') as f:
        json.dump([], f)


    #initialise lists for usage in trade log and equity curve
    eg_trade_log = []
    kf_trade_log = []
    kf_active_positions = []
    eg_active_positions = []
    equity_curve_eg = []
    equity_curve_kf = []

    #choose dates and prices list
    start = datetime.strptime('2024-01-01', '%Y-%m-%d').date()
    end = datetime.strptime('2024-12-31', '%Y-%m-%d').date()
    tickers_list = get_stocks()
    prices = get_prices(tickers_list, end)
    business_dates = get_date_range(start, end)
    dates = business_dates.intersection(prices.index)

    #set starting equity for portfolio
    equity_eg = 100000
    equity_curve_eg.append(equity_eg)
    equity_kf = 100000
    equity_curve_kf.append(equity_kf)

    #start backtest loop
    for date in dates:
        #sanity check to see how far along backtest is
        print(date)


        #check all active positions if they should be closed in engle granger only pairs
        for pos in eg_active_positions:
            pair = pos['pair']
            p1 = prices[pair[0]].loc[:date]
            p2 = prices[pair[1]].loc[:date]
            beta = pos['beta']
            alpha = pos['alpha']
            mean = pos['mean']
            std = pos['std']
            spread = calc_spread(p1, p2, beta, alpha)
            signal = signal_generator(spread, mean, std)
            trade_entry = next(d for d in eg_active_positions if d['pair'] == pair)
            pos_type = trade_entry['direction']
            no_shares1 = trade_entry['size'][0] 
            no_shares2 = trade_entry['size'][1] 
            p1_entry = trade_entry['prices'][0] 
            p2_entry = trade_entry['prices'][1]
            prev_idx = prices.index.get_loc(date) - 1
            prev_date = prices.index[prev_idx]
            change_in_equity = calc_pnl(no_shares1, no_shares2, p1_entry, p2_entry, p1.loc[date], p2.loc[date], pos_type) -  calc_pnl(no_shares1, no_shares2, p1_entry, p2_entry, p1.loc[prev_date], p2.loc[prev_date], pos_type)
            equity_eg += change_in_equity
            if signal == 'exit':
                PnL = calc_pnl(no_shares1, no_shares2, p1_entry, p2_entry, p1.loc[date], p2.loc[date], pos_type)
                print(f'eg: {PnL}')
                for log_entry in eg_trade_log:
                    if log_entry['pair'] == pair and log_entry['entry_date'] == trade_entry['entry_date']:
                        log_entry['exit_date'] = date.isoformat()
                        log_entry['pnl'] = PnL
                        
                eg_active_positions = [d for d in eg_active_positions if not (d['pair'] == pair and d['entry_date'] == trade_entry['entry_date'])]

        #repeat for kalman filtered pairs
        for pos in kf_active_positions:
            pair = pos['pair']
            p1 = prices[pair[0]].loc[:date]
            p2 = prices[pair[1]].loc[:date]
            beta = pos['beta']
            alpha = pos['alpha']
            mean = pos['mean']
            std = pos['std']
            spread = calc_spread(p1, p2, beta, alpha)
            signal = signal_generator(spread, mean, std)
            trade_entry = next(d for d in kf_active_positions if d['pair'] == pair)
            pos_type = trade_entry['direction']
            no_shares1 = trade_entry['size'][0] 
            no_shares2 = trade_entry['size'][1] 
            p1_entry = trade_entry['prices'][0] 
            p2_entry = trade_entry['prices'][1]
            prev_idx = prices.index.get_loc(date) - 1
            prev_date = prices.index[prev_idx]
            change_in_equity = calc_pnl(no_shares1, no_shares2, p1_entry, p2_entry, p1.loc[date], p2.loc[date], pos_type) -  calc_pnl(no_shares1, no_shares2, p1_entry, p2_entry, p1.loc[prev_date], p2.loc[prev_date], pos_type)
            equity_kf += change_in_equity
            if signal == 'exit':
                PnL = calc_pnl(no_shares1, no_shares2, p1_entry, p2_entry, p1.loc[date], p2.loc[date], pos_type)
                print(f'kf: {PnL}')
                for log_entry in kf_trade_log:
                    if log_entry['pair'] == pair and log_entry['entry_date'] == trade_entry['entry_date']:
                        log_entry['exit_date'] = date.isoformat()
                        log_entry['pnl'] = PnL
                        
                kf_active_positions = [d for d in kf_active_positions if not (d['pair'] == pair and d['entry_date'] == trade_entry['entry_date'])]

        #create list of engle granger pairs and also same list but after kalman filter
        EG_Data, cointegrated_pairs = cointegration_test_EG(tickers_list, prices, date)
        KF_Data = KF_calc(cointegrated_pairs, prices, date)

        for stock in EG_Data:
            pair = stock[0]
            #check if stock isnt already an active position
            if not any(d['pair'] == pair for d in eg_active_positions):
                spread = stock[3]
                pair = stock[0]
                beta = stock[1]
                alpha = stock[2]
                mean = stock[4]
                std = stock[5]
                signal = signal_generator(spread, mean, std)
                price1 = prices[pair[0]].loc[date]
                price2 = prices[pair[1]].loc[date]
                shares1 = capital_per_trade/price1
                shares2 = (capital_per_trade*abs(beta))/price2
                #check signal and go long/short, and append all needed values to the trade log + active positions 
                if signal == 'long':
                    equity_eg = equity_eg - shares1*price1 + shares2*price2
                    eg_active_positions.append({'pair': pair, 'direction': 'long', 'entry_date': date.isoformat(), 'size': [shares1, shares2], 'prices': [price1, price2], 'beta': beta, 'alpha': alpha, 'mean': mean, 'std': std})
                    eg_trade_log.append({'pair': pair, 'direction': 'long', 'entry_date': date.isoformat(), 'size': [shares1, shares2], 'prices': [price1, price2]})
                
                elif signal == 'short':
                    equity_eg = equity_eg - shares2*price2 + shares1*price1
                    eg_active_positions.append({'pair': pair, 'direction': 'short', 'entry_date': date.isoformat(), 'size': [shares1, shares2], 'prices': [price1, price2], 'beta': beta, 'alpha': alpha, 'mean': mean, 'std': std})
                    eg_trade_log.append({'pair': pair, 'direction': 'short', 'entry_date': date.isoformat(), 'size': [shares1, shares2], 'prices': [price1, price2]})


        #repeat for kalman filtered pairs
        for stock in KF_Data:
            pair = stock[0]
            #check if stock isnt already an active position
            if not any(d['pair'] == pair for d in kf_active_positions):
                spread_series = stock[2] 
                beta = stock[1]
                alpha = stock[5]
                mean = stock[3]
                std = stock[4]
                signal = signal_generator(spread_series, mean, std)
                price1 = prices[pair[0]].loc[date]
                price2 = prices[pair[1]].loc[date]
                shares1 = capital_per_trade/price1
                shares2 = (capital_per_trade*abs(beta))/price2
                #check signal and go long/short, and append all needed values to the trade log + active positions 
                if signal == 'long':
                    equity_kf = equity_kf - shares1*price1 + shares2*price2
                    kf_active_positions.append({'pair': pair, 'direction': 'long', 'entry_date': date.isoformat(), 'size': [shares1, shares2], 'prices': [price1, price2], 'beta': beta, 'alpha': alpha, 'mean': mean, 'std': std})
                    kf_trade_log.append({'pair': pair, 'direction': 'long', 'entry_date': date.isoformat(), 'size': [shares1, shares2], 'prices': [price1, price2]})
                elif signal == 'short':
                    equity_kf = equity_kf - shares2*price2 + shares1*price1
                    kf_active_positions.append({'pair': pair, 'direction': 'short', 'entry_date': date.isoformat(), 'size': [shares1, shares2], 'prices': [price1, price2], 'beta': beta, 'alpha': alpha, 'mean': mean, 'std': std})
                    kf_trade_log.append({'pair': pair, 'direction': 'short', 'entry_date': date.isoformat(), 'size': [shares1, shares2], 'prices': [price1, price2]})
        
        equity_curve_eg.append(equity_eg)
        equity_curve_kf.append(equity_kf)

        #end of backtest loop

   
   #dump final trade logs into file so i can read it
    with open('eg_trade_log.json', 'w') as file:
        json.dump(eg_trade_log, file, indent=4)
    with open('kf_trade_log.json', 'w') as file:
        json.dump(kf_trade_log, file, indent=4) 
    
    
    #create equity curves for ease of sharpe, max drawdown calculations
    
    #print final results
    print(f"Engle Granger: PnL on exited trades = {calc_total_returns('eg_trade_log.json')}, Sharpe Ratio = {calc_sharpe(equity_curve_eg)}, Max Drawdown = {max_drawdown(equity_curve_eg)}, Win Rate = {win_rate('eg_trade_log.json')}, Final Equity = {equity_curve_eg[-1]}")
    print(f"Kalman Filter: PnL on exited trades = {calc_total_returns('kf_trade_log.json')}, Sharpe Ratio = {calc_sharpe(equity_curve_kf)}, Max Drawdown = {max_drawdown(equity_curve_kf)}, Win Rate = {win_rate('kf_trade_log.json')}, Final Equity = {equity_curve_kf[-1]}")

if __name__ == '__main__':
   main()

    #14/15/16 aug: 
    # hashtag the (code every part of it) with notes for readability
      #      2. backtest with loads of different data sets and write report!



#for the 'issues' section of report: doesnt take into account handling partial fills/retries/order time
# also little bit of lookahead bias because im trading at closing price of a day that I have data for
#trading costs
# no stop losses, positions sizing
