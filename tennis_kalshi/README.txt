Goal
Paper-trade a live match-winner market by computing fair prices from per-point serve strengths and current state, and output trade signals only when edge clears fees.

How to run
python3 run_paper.py

Next steps
1) Replace simulated state transitions with a live tennis feed. You need: server, point score, game score, set score, tiebreak points, who serves next.
2) Replace kalshi_api.py stubs with real book + order methods; prefer mid for valuation, cross only when edge > fees.
3) Log every tick: fair, market, action, inventory. Backtest your rules of engagement on recorded streams.
4) Tune ServePriors by tour/surface; update only at service-game boundaries to avoid overfitting single points.
5) Add guardrails: no trades during medical timeouts, rain, or after player injury flags; pause if spread collapses.