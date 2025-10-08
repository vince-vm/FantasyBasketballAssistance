"""
API utilities for fetching NBA player data from ESPN API.
Handles data fetching, normalization, and ESPN fantasy scoring calculations.
"""

import pandas as pd
import requests
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ESPNFantasyAPI:
    """ESPN Fantasy Basketball API client using community-discovered endpoints."""
    
    def __init__(self):
        # Using the community-discovered ESPN API endpoints
        self.fantasy_base_url = "https://fantasy.espn.com/apis/v3/games/fba"
        self.sports_base_url = "https://sports.core.api.espn.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        })
    
    def get_current_season(self) -> int:
        """Get the current NBA season year."""
        current_year = datetime.now().year
        # NBA season typically starts in October, so if we're before October, use previous year
        if datetime.now().month < 10:
            return current_year - 1
        return current_year
    
    def fetch_player_stats(self, season: Optional[int] = None) -> pd.DataFrame:
        """
        Fetch NBA player statistics from ESPN API using community-discovered endpoints.
        
        Args:
            season: NBA season year (defaults to current season)
            
        Returns:
            DataFrame with player stats and fantasy points
        """
        if season is None:
            season = self.get_current_season()
        
        # Try multiple approaches based on the Public-ESPN-API documentation
        approaches = [
            self._try_fantasy_api,
            self._try_sports_core_api,
            self._try_athletes_endpoint
        ]
        
        for approach in approaches:
            try:
                df = approach(season)
                if not df.empty:
                    return df
            except Exception as e:
                logger.warning(f"Approach {approach.__name__} failed: {e}")
                continue
        
        # If all approaches fail, return sample data for demonstration
        logger.warning("All API approaches failed, returning sample data")
        return self._create_sample_data()
    
    def _try_fantasy_api(self, season: int) -> pd.DataFrame:
        """Try the Fantasy API endpoint."""
        url = f"{self.fantasy_base_url}/seasons/{season}/segments/0/leagues/standard"
        
        params = {
            'view': 'kona_player_info',
            'scoringPeriodId': 0
        }
        
        logger.info(f"Trying Fantasy API: {url}")
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if 'players' in data and data['players']:
            return self._process_fantasy_players(data['players'])
        
        return pd.DataFrame()
    
    def _try_sports_core_api(self, season: int) -> pd.DataFrame:
        """Try the Sports Core API for NBA players."""
        # NBA league ID is typically 1
        url = f"{self.sports_base_url}/v2/sports/basketball/leagues/nba/seasons/{season}/athletes"
        
        params = {
            'limit': 1000
        }
        
        logger.info(f"Trying Sports Core API: {url}")
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if 'items' in data and data['items']:
            return self._process_sports_core_players(data['items'])
        
        return pd.DataFrame()
    
    def _try_athletes_endpoint(self, season: int) -> pd.DataFrame:
        """Try the athletes endpoint with statistics."""
        url = f"{self.sports_base_url}/v2/sports/basketball/leagues/nba/seasons/{season}/athletes"
        
        params = {
            'limit': 1000,
            'statistics': 'true'
        }
        
        logger.info(f"Trying Athletes endpoint: {url}")
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if 'items' in data and data['items']:
            return self._process_athletes_with_stats(data['items'])
        
        return pd.DataFrame()
    
    def _process_fantasy_players(self, players: List[Dict]) -> pd.DataFrame:
        """Process players from Fantasy API response."""
        players_data = []
        for player in players:
            try:
                player_info = self._extract_player_info(player)
                if player_info:
                    players_data.append(player_info)
            except Exception as e:
                logger.warning(f"Error processing fantasy player {player.get('id', 'unknown')}: {e}")
                continue
        
        if players_data:
            df = pd.DataFrame(players_data)
            df = self._calculate_fantasy_points(df)
            df = df.sort_values('FPPG', ascending=False).reset_index(drop=True)
            logger.info(f"Successfully processed {len(df)} players from Fantasy API")
            return df
        
        return pd.DataFrame()
    
    def _process_sports_core_players(self, players: List[Dict]) -> pd.DataFrame:
        """Process players from Sports Core API response."""
        players_data = []
        for player in players:
            try:
                player_info = self._extract_sports_core_player_info(player)
                if player_info:
                    players_data.append(player_info)
            except Exception as e:
                logger.warning(f"Error processing sports core player {player.get('id', 'unknown')}: {e}")
                continue
        
        if players_data:
            df = pd.DataFrame(players_data)
            df = self._calculate_fantasy_points(df)
            df = df.sort_values('FPPG', ascending=False).reset_index(drop=True)
            logger.info(f"Successfully processed {len(df)} players from Sports Core API")
            return df
        
        return pd.DataFrame()
    
    def _process_athletes_with_stats(self, players: List[Dict]) -> pd.DataFrame:
        """Process players from Athletes endpoint with statistics."""
        players_data = []
        for player in players:
            try:
                player_info = self._extract_athlete_stats_info(player)
                if player_info:
                    players_data.append(player_info)
            except Exception as e:
                logger.warning(f"Error processing athlete {player.get('id', 'unknown')}: {e}")
                continue
        
        if players_data:
            df = pd.DataFrame(players_data)
            df = self._calculate_fantasy_points(df)
            df = df.sort_values('FPPG', ascending=False).reset_index(drop=True)
            logger.info(f"Successfully processed {len(df)} players from Athletes API")
            return df
        
        return pd.DataFrame()
    
    def _extract_player_info(self, player: Dict) -> Optional[Dict]:
        """Extract relevant player information from API response."""
        try:
            # Basic player info
            player_id = player.get('id')
            if not player_id:
                return None
            
            # Player details
            player_details = player.get('player', {})
            name = player_details.get('fullName', 'Unknown')
            team = player_details.get('proTeamId', 0)
            position = player_details.get('defaultPositionId', 0)
            
            # Convert team ID to team abbreviation
            team_abbr = self._get_team_abbreviation(team)
            
            # Convert position ID to position name
            pos_name = self._get_position_name(position)
            
            # Stats
            stats = player.get('stats', [])
            season_stats = None
            
            # Find season totals (usually the first stat entry)
            for stat in stats:
                if stat.get('statSourceId') == 0:  # Season totals
                    season_stats = stat.get('stats', {})
                    break
            
            if not season_stats:
                return None
            
            # Extract relevant stats
            games_played = season_stats.get('0', 0)  # Games played
            if games_played == 0:
                return None  # Skip players with no games
            
            points = season_stats.get('1', 0)  # Points
            rebounds = season_stats.get('2', 0)  # Rebounds
            assists = season_stats.get('3', 0)  # Assists
            steals = season_stats.get('4', 0)  # Steals
            blocks = season_stats.get('5', 0)  # Blocks
            turnovers = season_stats.get('6', 0)  # Turnovers
            
            return {
                'Player': name,
                'Team': team_abbr,
                'Position': pos_name,
                'GP': games_played,
                'PTS': points,
                'REB': rebounds,
                'AST': assists,
                'STL': steals,
                'BLK': blocks,
                'TO': turnovers
            }
            
        except Exception as e:
            logger.warning(f"Error extracting player info: {e}")
            return None
    
    def _extract_sports_core_player_info(self, player: Dict) -> Optional[Dict]:
        """Extract player info from Sports Core API response."""
        try:
            # Basic player info
            player_id = player.get('id')
            if not player_id:
                return None
            
            display_name = player.get('displayName', 'Unknown')
            team_id = player.get('team', {}).get('id', 0)
            position_id = player.get('position', {}).get('id', 0)
            
            # Convert team ID to team abbreviation
            team_abbr = self._get_team_abbreviation(team_id)
            
            # Convert position ID to position name
            pos_name = self._get_position_name(position_id)
            
            # For Sports Core API, we might not have detailed stats
            # Return basic info with placeholder stats
            return {
                'Player': display_name,
                'Team': team_abbr,
                'Position': pos_name,
                'GP': 1,  # Placeholder
                'PTS': 0,
                'REB': 0,
                'AST': 0,
                'STL': 0,
                'BLK': 0,
                'TO': 0
            }
            
        except Exception as e:
            logger.warning(f"Error extracting sports core player info: {e}")
            return None
    
    def _extract_athlete_stats_info(self, player: Dict) -> Optional[Dict]:
        """Extract player info from Athletes API with statistics."""
        try:
            # Basic player info
            player_id = player.get('id')
            if not player_id:
                return None
            
            display_name = player.get('displayName', 'Unknown')
            team_id = player.get('team', {}).get('id', 0)
            position_id = player.get('position', {}).get('id', 0)
            
            # Convert team ID to team abbreviation
            team_abbr = self._get_team_abbreviation(team_id)
            
            # Convert position ID to position name
            pos_name = self._get_position_name(position_id)
            
            # Try to extract statistics if available
            stats = player.get('statistics', {})
            if stats:
                # Extract season stats if available
                season_stats = stats.get('seasons', [])
                if season_stats:
                    latest_season = season_stats[-1]  # Get most recent season
                    stats_data = latest_season.get('stats', {})
                    
                    games_played = stats_data.get('gamesPlayed', 1)
                    if games_played == 0:
                        games_played = 1
                    
                    return {
                        'Player': display_name,
                        'Team': team_abbr,
                        'Position': pos_name,
                        'GP': games_played,
                        'PTS': stats_data.get('points', 0),
                        'REB': stats_data.get('rebounds', 0),
                        'AST': stats_data.get('assists', 0),
                        'STL': stats_data.get('steals', 0),
                        'BLK': stats_data.get('blocks', 0),
                        'TO': stats_data.get('turnovers', 0)
                    }
            
            # If no detailed stats, return basic info
            return {
                'Player': display_name,
                'Team': team_abbr,
                'Position': pos_name,
                'GP': 1,
                'PTS': 0,
                'REB': 0,
                'AST': 0,
                'STL': 0,
                'BLK': 0,
                'TO': 0
            }
            
        except Exception as e:
            logger.warning(f"Error extracting athlete stats info: {e}")
            return None
    
    def _get_team_abbreviation(self, team_id: int) -> str:
        """Convert ESPN team ID to team abbreviation."""
        team_map = {
            1: 'ATL', 2: 'BOS', 3: 'BKN', 4: 'CHA', 5: 'CHI',
            6: 'CLE', 7: 'DAL', 8: 'DEN', 9: 'DET', 10: 'GSW',
            11: 'HOU', 12: 'IND', 13: 'LAC', 14: 'LAL', 15: 'MEM',
            16: 'MIA', 17: 'MIL', 18: 'MIN', 19: 'NO', 20: 'NY',
            21: 'OKC', 22: 'ORL', 23: 'PHI', 24: 'PHX', 25: 'POR',
            26: 'SAC', 27: 'SA', 28: 'TOR', 29: 'UTA', 30: 'WSH'
        }
        return team_map.get(team_id, 'UNK')
    
    def _get_position_name(self, position_id: int) -> str:
        """Convert ESPN position ID to position name."""
        position_map = {
            1: 'PG', 2: 'SG', 3: 'SF', 4: 'PF', 5: 'C'
        }
        return position_map.get(position_id, 'UNK')
    
    def _calculate_fantasy_points(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate ESPN fantasy points per game.
        
        ESPN Points scoring:
        - PTS × 1
        - REB × 1.2
        - AST × 1.5
        - STL × 3
        - BLK × 3
        - TO × –1
        """
        df = df.copy()
        
        # Calculate per-game averages
        df['PTS_PG'] = df['PTS'] / df['GP']
        df['REB_PG'] = df['REB'] / df['GP']
        df['AST_PG'] = df['AST'] / df['GP']
        df['STL_PG'] = df['STL'] / df['GP']
        df['BLK_PG'] = df['BLK'] / df['GP']
        df['TO_PG'] = df['TO'] / df['GP']
        
        # Calculate fantasy points per game
        df['FPPG'] = (
            df['PTS_PG'] * 1.0 +
            df['REB_PG'] * 1.2 +
            df['AST_PG'] * 1.5 +
            df['STL_PG'] * 3.0 +
            df['BLK_PG'] * 3.0 +
            df['TO_PG'] * -1.0
        ).round(2)
        
        # Calculate total fantasy points
        df['Total'] = (df['FPPG'] * df['GP']).round(1)
        
        # Round per-game stats to 1 decimal place
        for col in ['PTS_PG', 'REB_PG', 'AST_PG', 'STL_PG', 'BLK_PG', 'TO_PG']:
            df[col] = df[col].round(1)
        
        return df
    
    def _create_empty_dataframe(self) -> pd.DataFrame:
        """Create an empty DataFrame with the expected columns."""
        return pd.DataFrame(columns=[
            'Player', 'Team', 'Position', 'GP', 'PTS', 'REB', 'AST', 
            'STL', 'BLK', 'TO', 'PTS_PG', 'REB_PG', 'AST_PG', 
            'STL_PG', 'BLK_PG', 'TO_PG', 'FPPG', 'Total'
        ])
    
    def _create_sample_data(self) -> pd.DataFrame:
        """Create sample data for demonstration when API is unavailable."""
        sample_players = [
            {'Player': 'Nikola Jokic', 'Team': 'DEN', 'Position': 'C', 'GP': 70, 'PTS': 2100, 'REB': 700, 'AST': 600, 'STL': 100, 'BLK': 50, 'TO': 200},
            {'Player': 'Luka Doncic', 'Team': 'DAL', 'Position': 'PG', 'GP': 65, 'PTS': 2200, 'REB': 600, 'AST': 700, 'STL': 120, 'BLK': 30, 'TO': 250},
            {'Player': 'Joel Embiid', 'Team': 'PHI', 'Position': 'C', 'GP': 60, 'PTS': 2000, 'REB': 800, 'AST': 300, 'STL': 80, 'BLK': 120, 'TO': 180},
            {'Player': 'Giannis Antetokounmpo', 'Team': 'MIL', 'Position': 'PF', 'GP': 68, 'PTS': 1900, 'REB': 750, 'AST': 400, 'STL': 90, 'BLK': 80, 'TO': 220},
            {'Player': 'Jayson Tatum', 'Team': 'BOS', 'Position': 'SF', 'GP': 72, 'PTS': 1800, 'REB': 500, 'AST': 350, 'STL': 100, 'BLK': 60, 'TO': 200},
            {'Player': 'Stephen Curry', 'Team': 'GSW', 'Position': 'PG', 'GP': 58, 'PTS': 1600, 'REB': 300, 'AST': 400, 'STL': 80, 'BLK': 20, 'TO': 180},
            {'Player': 'LeBron James', 'Team': 'LAL', 'Position': 'SF', 'GP': 55, 'PTS': 1400, 'REB': 400, 'AST': 450, 'STL': 70, 'BLK': 40, 'TO': 200},
            {'Player': 'Kevin Durant', 'Team': 'PHX', 'Position': 'SF', 'GP': 62, 'PTS': 1700, 'REB': 450, 'AST': 300, 'STL': 60, 'BLK': 80, 'TO': 190},
            {'Player': 'Damian Lillard', 'Team': 'MIL', 'Position': 'PG', 'GP': 60, 'PTS': 1500, 'REB': 250, 'AST': 500, 'STL': 70, 'BLK': 15, 'TO': 200},
            {'Player': 'Anthony Davis', 'Team': 'LAL', 'Position': 'PF', 'GP': 65, 'PTS': 1600, 'REB': 700, 'AST': 200, 'STL': 80, 'BLK': 150, 'TO': 180},
            {'Player': 'Jimmy Butler', 'Team': 'MIA', 'Position': 'SF', 'GP': 58, 'PTS': 1200, 'REB': 400, 'AST': 350, 'STL': 100, 'BLK': 30, 'TO': 150},
            {'Player': 'Kawhi Leonard', 'Team': 'LAC', 'Position': 'SF', 'GP': 50, 'PTS': 1100, 'REB': 350, 'AST': 250, 'STL': 80, 'BLK': 40, 'TO': 120},
            {'Player': 'Paul George', 'Team': 'LAC', 'Position': 'SF', 'GP': 55, 'PTS': 1300, 'REB': 400, 'AST': 300, 'STL': 90, 'BLK': 50, 'TO': 160},
            {'Player': 'Russell Westbrook', 'Team': 'LAC', 'Position': 'PG', 'GP': 52, 'PTS': 1000, 'REB': 400, 'AST': 500, 'STL': 80, 'BLK': 20, 'TO': 200},
            {'Player': 'Kyrie Irving', 'Team': 'DAL', 'Position': 'PG', 'GP': 48, 'PTS': 1200, 'REB': 200, 'AST': 400, 'STL': 60, 'BLK': 15, 'TO': 150},
            {'Player': 'Devin Booker', 'Team': 'PHX', 'Position': 'SG', 'GP': 65, 'PTS': 1500, 'REB': 300, 'AST': 350, 'STL': 70, 'BLK': 25, 'TO': 180},
            {'Player': 'Bradley Beal', 'Team': 'PHX', 'Position': 'SG', 'GP': 60, 'PTS': 1400, 'REB': 250, 'AST': 300, 'STL': 60, 'BLK': 20, 'TO': 170},
            {'Player': 'Donovan Mitchell', 'Team': 'CLE', 'Position': 'SG', 'GP': 68, 'PTS': 1600, 'REB': 300, 'AST': 400, 'STL': 80, 'BLK': 30, 'TO': 190},
            {'Player': 'Trae Young', 'Team': 'ATL', 'Position': 'PG', 'GP': 70, 'PTS': 1500, 'REB': 250, 'AST': 600, 'STL': 70, 'BLK': 10, 'TO': 250},
            {'Player': 'Ja Morant', 'Team': 'MEM', 'Position': 'PG', 'GP': 45, 'PTS': 1000, 'REB': 200, 'AST': 400, 'STL': 50, 'BLK': 15, 'TO': 150},
            {'Player': 'Zion Williamson', 'Team': 'NO', 'Position': 'PF', 'GP': 40, 'PTS': 900, 'REB': 300, 'AST': 200, 'STL': 40, 'BLK': 30, 'TO': 120},
            {'Player': 'Karl-Anthony Towns', 'Team': 'MIN', 'Position': 'C', 'GP': 65, 'PTS': 1500, 'REB': 600, 'AST': 300, 'STL': 60, 'BLK': 80, 'TO': 180},
            {'Player': 'Rudy Gobert', 'Team': 'MIN', 'Position': 'C', 'GP': 70, 'PTS': 800, 'REB': 800, 'AST': 100, 'STL': 50, 'BLK': 120, 'TO': 100},
            {'Player': 'Bam Adebayo', 'Team': 'MIA', 'Position': 'C', 'GP': 68, 'PTS': 1200, 'REB': 600, 'AST': 300, 'STL': 80, 'BLK': 100, 'TO': 150},
            {'Player': 'Pascal Siakam', 'Team': 'IND', 'Position': 'PF', 'GP': 70, 'PTS': 1400, 'REB': 500, 'AST': 350, 'STL': 70, 'BLK': 60, 'TO': 160}
        ]
        
        df = pd.DataFrame(sample_players)
        df = self._calculate_fantasy_points(df)
        df = df.sort_values('FPPG', ascending=False).reset_index(drop=True)
        
        logger.info(f"Created sample dataset with {len(df)} players")
        return df

def fetch_nba_data(season: Optional[int] = None) -> pd.DataFrame:
    """
    Convenience function to fetch NBA player data.
    
    Args:
        season: NBA season year (defaults to current season)
        
    Returns:
        DataFrame with player stats and fantasy points
    """
    api = ESPNFantasyAPI()
    return api.fetch_player_stats(season)

if __name__ == "__main__":
    # Test the API
    print("Testing ESPN Fantasy API...")
    df = fetch_nba_data()
    print(f"Fetched {len(df)} players")
    if not df.empty:
        print("\nTop 10 players by FPPG:")
        print(df[['Player', 'Team', 'Position', 'FPPG']].head(10))
