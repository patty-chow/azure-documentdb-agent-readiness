from typing import Dict, Any


def format_strategy_review(stats: Dict[str, Any]) -> str:
    # Deterministic LLM-ready summary
    return (
        f"Strategy {stats.get('strategy_id')} — {stats.get('trade_count',0)} trades. "
        f"Total P&L: {stats.get('total_pnl',0.0):+.2f}. "
        f"Average P&L/trade: {stats.get('avg_pnl',0.0):+.2f}. "
        f"Win rate: {stats.get('win_rate',0.0)*100:.1f}%. "
        f"Max drawdown: {stats.get('max_drawdown',0.0):.2f}."
    )
