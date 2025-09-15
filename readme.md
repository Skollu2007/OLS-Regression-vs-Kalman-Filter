Dynamic vs Static Beta in Mean-Reversion Pairs Trading

This project compares two approaches to estimating hedge ratios for mean-reversion pairs trading strategies:

Engle–Granger OLS regression (static β)

Kalman Filter (dynamic β)

It evaluates which method performs better in terms of risk-adjusted returns, drawdowns, and overall portfolio equity growth.

Project Overview

Pairs trading relies on the assumption that the price spread between two co-integrated assets will mean-revert over time. This project investigates whether a dynamically estimated hedge ratio (via a Kalman filter) outperforms a static hedge ratio (via OLS regression) in live trading conditions.

Methods

Data Collection:
Historical price data for selected stock pairs.

Static Approach (Engle–Granger):

Run OLS regression once over a training window to estimate α and β.

Compute spread as:

spread
𝑡
=
𝑦
𝑡
−
(
𝛼
+
𝛽
𝑥
𝑡
)
spread
t
	​

=y
t
	​

−(α+βx
t
	​

)

Trade when z-score exceeds entry thresholds; exit on mean reversion.

Dynamic Approach (Kalman Filter):

Update α and β recursively at each time step using a state-space model.

Compute dynamically adjusted spread and z-scores.

Trade using the same threshold-based logic as OLS.

Evaluation:

PnL on exited trades

Sharpe ratio

Maximum drawdown

Final equity

Comparison across multiple years (2021, 2022, 2024; 2023 excluded due to anomalous results)

Key Results
Year	PnL ($)	Sharpe (%)	Max Drawdown ($)	Final Equity ($)
2021	KF: 6,719.51 / OLS: 21,147.27	KF: 1.80 / OLS: 1.15	KF: 22,394.43 / OLS: 25,554.41	KF: 204,493.03 / OLS: 153,026.02
2022	KF: 7,944.44 / OLS: 15,725.08	KF: 1.81 / OLS: 0.74	KF: 19,476.15 / OLS: 82,074.00	KF: 198,390.11 / OLS: 198,390.11
2024	KF: 2,465.95 / OLS: 16,430.41	KF: 2.41 / OLS: 1.36	KF: 16,126.85 / OLS: 19,460.88	KF: 243,111.52 / OLS: 165,331.75

Summary:

Kalman Filter → lower drawdowns, higher Sharpe ratios, smoother equity growth.

OLS → higher absolute profits but significantly higher volatility and risk.

Practical Implications

Traders looking for steady returns and capital preservation may prefer the Kalman filter for its adaptiveness and smoother signals.

Quant researchers may find OLS attractive for its simplicity and computational efficiency, particularly for screening large universes of pairs.

Future Work

Hybrid models: OLS for pair selection, KF for live trading execution.

Robustness tests under different market regimes, volatility clusters, and asset classes.

Extension to nonlinear state-space models to handle regime shifts.

How to Run

Clone the repository:

git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name


Install dependencies:

pip install -r requirements.txt

change dates in main.py

Run the backtest script:

python main.py


View results in the results/ folder (PNL plots, z-score charts, performance metrics).

License

MIT License – free to use and modify for academic or personal projects.