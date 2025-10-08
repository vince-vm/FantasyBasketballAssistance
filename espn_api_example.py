#!/usr/bin/env python3
"""
ESPN API Example Script
Demonstrates how to use the community-discovered ESPN API endpoints
based on the Public-ESPN-API repository documentation.
"""

import requests
import json
from typing import Dict, List, Optional

class ESPNAPIClient:
    """Simple ESPN API client using community-discovered endpoints."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        })
    
    def get_nba_players(self, season: int = 2024) -> List[Dict]:
        """
        Get NBA players using the Sports Core API endpoint.
        
        Based on: https://github.com/pseudo-r/Public-ESPN-API
        Endpoint: /v2/sports/basketball/leagues/nba/seasons/{season}/athletes
        """
        url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/seasons/{season}/athletes"
        
        params = {
            'limit': 1000
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('items', [])
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching NBA players: {e}")
            return []
    
    def get_nba_players_with_stats(self, season: int = 2024) -> List[Dict]:
        """
        Get NBA players with statistics.
        
        Based on: https://github.com/pseudo-r/Public-ESPN-API
        Endpoint: /v2/sports/basketball/leagues/nba/seasons/{season}/athletes?statistics=true
        """
        url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/seasons/{season}/athletes"
        
        params = {
            'limit': 1000,
            'statistics': 'true'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('items', [])
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching NBA players with stats: {e}")
            return []
    
    def get_fantasy_players(self, season: int = 2024) -> List[Dict]:
        """
        Get fantasy basketball players.
        
        Based on: https://github.com/pseudo-r/Public-ESPN-API
        Endpoint: /apis/v3/games/fba/seasons/{season}/segments/0/leagues/standard
        """
        url = f"https://fantasy.espn.com/apis/v3/games/fba/seasons/{season}/segments/0/leagues/standard"
        
        params = {
            'view': 'kona_player_info',
            'scoringPeriodId': 0
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('players', [])
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching fantasy players: {e}")
            return []
    
    def get_team_info(self, team_id: int) -> Optional[Dict]:
        """
        Get team information.
        
        Based on: https://github.com/pseudo-r/Public-ESPN-API
        Endpoint: /v2/sports/basketball/leagues/nba/teams/{team_id}
        """
        url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/teams/{team_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching team {team_id}: {e}")
            return None
    
    def get_player_stats(self, player_id: int, season: int = 2024) -> Optional[Dict]:
        """
        Get player statistics.
        
        Based on: https://github.com/pseudo-r/Public-ESPN-API
        Endpoint: /v2/sports/basketball/leagues/nba/athletes/{player_id}/statisticslog
        """
        url = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/athletes/{player_id}/statisticslog"
        
        params = {
            'season': season
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching player {player_id} stats: {e}")
            return None

def main():
    """Example usage of ESPN API endpoints."""
    print("🏀 ESPN API Example Script")
    print("=" * 50)
    print("Based on: https://github.com/pseudo-r/Public-ESPN-API")
    print()
    
    client = ESPNAPIClient()
    
    # Example 1: Get NBA players
    print("1. Fetching NBA players...")
    players = client.get_nba_players(2024)
    print(f"   Found {len(players)} players")
    
    if players:
        # Show first 5 players
        print("   First 5 players:")
        for i, player in enumerate(players[:5]):
            name = player.get('displayName', 'Unknown')
            team = player.get('team', {}).get('abbreviation', 'UNK')
            position = player.get('position', {}).get('abbreviation', 'UNK')
            print(f"   {i+1}. {name} ({team}, {position})")
    
    print()
    
    # Example 2: Get players with stats
    print("2. Fetching NBA players with statistics...")
    players_with_stats = client.get_nba_players_with_stats(2024)
    print(f"   Found {len(players_with_stats)} players with stats")
    
    if players_with_stats:
        # Show first player with stats
        player = players_with_stats[0]
        name = player.get('displayName', 'Unknown')
        stats = player.get('statistics', {})
        print(f"   Example: {name}")
        print(f"   Has statistics: {'Yes' if stats else 'No'}")
    
    print()
    
    # Example 3: Get fantasy players
    print("3. Fetching fantasy basketball players...")
    fantasy_players = client.get_fantasy_players(2024)
    print(f"   Found {len(fantasy_players)} fantasy players")
    
    print()
    
    # Example 4: Get team info
    print("4. Fetching team information...")
    team_info = client.get_team_info(1)  # Team ID 1
    if team_info:
        team_name = team_info.get('displayName', 'Unknown')
        print(f"   Team 1: {team_name}")
    
    print()
    print("✅ ESPN API examples completed!")
    print()
    print("📚 For more information, visit:")
    print("   https://github.com/pseudo-r/Public-ESPN-API")
    print()
    print("⚠️  Remember: These are unofficial APIs that may change without notice!")

if __name__ == "__main__":
    main()
