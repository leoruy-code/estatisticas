"""
Scraper Module
==============
Scrapers para coleta de dados de futebol.
"""

from .sofascore_scraper import SofaScoreScraper, Team, Player, PlayerStats, TeamStats

__all__ = [
    'SofaScoreScraper',
    'Team',
    'Player', 
    'PlayerStats',
    'TeamStats'
]
