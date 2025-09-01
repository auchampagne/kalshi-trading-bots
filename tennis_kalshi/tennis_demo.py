from dataclasses import dataclass
from datetime import datetime

@dataclass
class TennisMatch:
    """Simple tennis match class for demo purposes."""
    home_player: str
    away_player: str
    surface: str
    tournament: str
    
@dataclass
class MarketAnalysis:
    """Analysis result for a tennis market."""
    market_id: str
    title: str
    win_probability: float
    yes_price: float
    no_price: float
    recommended_side: str
    size: int
    edge: float

def analyze_demo_market(match: TennisMatch) -> MarketAnalysis:
    """Analyze a demo tennis market."""
    # Demo values
    win_prob = 0.65  # 65% chance of home player winning
    yes_price = 60.0  # 60 cents
    no_price = 40.0   # 40 cents
    
    # Calculate edge
    edge = abs(win_prob - (yes_price / 100.0)) * 100
    
    return MarketAnalysis(
        market_id="TENNIS-DEMO-1",
        title=f"{match.home_player} vs {match.away_player} - {match.tournament}",
        win_probability=win_prob,
        yes_price=yes_price,
        no_price=no_price,
        recommended_side="yes" if win_prob > (yes_price / 100.0) else "no",
        size=10,  # Demo size
        edge=edge
    )
