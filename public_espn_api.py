"""
Basketball API client based on Public-ESPN-API repository
https://github.com/pseudo-r/Public-ESPN-API

Optimized for instant loading with concurrent requests and caching.
"""

import requests
import pandas as pd
from typing import Dict, List, Optional
import logging
from datetime import datetime
import concurrent.futures
import threading
import time

logger = logging.getLogger(__name__)

# Global cache for instant loading
_player_cache = {}
_cache_lock = threading.Lock()
_last_cache_time = None

logger = logging.getLogger(__name__)

class ESPNBasketballAPI:
    """ESPN Basketball API client optimized for instant loading."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        })
    
    def get_nba_players_from_api(self, season: int = 2024) -> pd.DataFrame:
        """Get ALL NBA players with real stats and fantasy projections."""
        global _player_cache, _last_cache_time
        
        # Check cache first - instant return if available
        with _cache_lock:
            if _player_cache and _last_cache_time:
                cache_age = datetime.now() - _last_cache_time
                if cache_age.total_seconds() < 1800:  # 30 minutes
                    logger.info(f"Returning cached data instantly ({len(_player_cache)} players)")
                    return pd.DataFrame(_player_cache)
        
        # If no cache or expired, fetch ALL players with real stats
        logger.info("Fetching ALL NBA players with real statistics...")
        start_time = time.time()
        
        # Use the most reliable endpoint for complete player data
        endpoint = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/seasons/{season}/athletes"
        
        try:
            # Get initial page to determine total pages
            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status()
            initial_data = response.json()
            
            total_pages = initial_data.get('pageCount', 1)  # Get ALL pages
            logger.info(f"Fetching ALL {total_pages} pages for complete NBA roster...")
            
            # Fetch all pages concurrently
            all_players = self._fetch_all_pages_concurrently(endpoint, total_pages)
            
            if all_players:
                # Process ALL players with real stats
                processed_players = self._process_all_players_with_real_stats(all_players)
                
                if processed_players:
                    df = pd.DataFrame(processed_players)
                    df = self._calculate_fantasy_points(df)
                    df = df.sort_values('FPPG', ascending=False).reset_index(drop=True)
                    
                    # Cache the results
                    with _cache_lock:
                        _player_cache = df.to_dict('records')
                        _last_cache_time = datetime.now()
                    
                    elapsed = time.time() - start_time
                    logger.info(f"Successfully fetched {len(df)} NBA players with real stats in {elapsed:.2f} seconds")
                    return df
            
            logger.error("No players fetched")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return pd.DataFrame()
    
    def _fetch_all_pages_concurrently(self, base_endpoint: str, total_pages: int) -> List[Dict]:
        """Fetch ALL pages concurrently to get complete NBA roster."""
        all_items = []
        
        def fetch_page(page_num):
            try:
                endpoint = f"{base_endpoint}?page={page_num}"
                response = self.session.get(endpoint, timeout=8)
                response.raise_for_status()
                data = response.json()
                return data.get('items', [])
            except Exception as e:
                logger.warning(f"Error fetching page {page_num}: {e}")
                return []
        
        # Use ThreadPoolExecutor for concurrent requests - get ALL pages
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(fetch_page, page) for page in range(1, total_pages + 1)]
            
            for future in concurrent.futures.as_completed(futures):
                items = future.result()
                all_items.extend(items)
        
        logger.info(f"Fetched {len(all_items)} player references from ALL {total_pages} pages")
        return all_items
    
    def _process_all_players_with_real_stats(self, player_refs: List[Dict]) -> List[Dict]:
        """Process ALL players with real statistics extraction."""
        processed_players = []
        
        def process_player_ref(player_ref):
            try:
                if isinstance(player_ref, dict) and '$ref' in player_ref:
                    # Follow the reference to get actual player data
                    ref_url = player_ref['$ref']
                    response = self.session.get(ref_url, timeout=5)
                    response.raise_for_status()
                    player_data = response.json()
                    
                    # Extract player info with REAL stats
                    return self._extract_player_with_real_stats(player_data)
                return None
            except Exception as e:
                logger.warning(f"Error processing player: {e}")
                return None
        
        # Process ALL players concurrently (no artificial limits)
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(process_player_ref, ref) for ref in player_refs]
            
            for future in concurrent.futures.as_completed(futures):
                player_info = future.result()
                if player_info:
                    processed_players.append(player_info)
        
        logger.info(f"Processed {len(processed_players)} players with real statistics")
        return processed_players
    
    def _extract_player_with_real_stats(self, athlete: Dict) -> Optional[Dict]:
        """Extract player info with REAL statistics from ESPN API."""
        try:
            # Extract name
            name = (athlete.get('displayName') or 
                   athlete.get('fullName') or 
                   athlete.get('name') or 
                   'Unknown')
            
            # Extract team with reference following for accuracy
            team_info = athlete.get('team', {})
            team_abbr = 'UNK'
            if isinstance(team_info, dict) and '$ref' in team_info:
                # Follow team reference for accurate team data
                try:
                    team_response = self.session.get(team_info['$ref'], timeout=3)
                    team_response.raise_for_status()
                    team_data = team_response.json()
                    team_abbr = team_data.get('abbreviation', 'UNK')
                except:
                    # Fallback to ID extraction
                    ref_url = team_info['$ref']
                    team_id = ref_url.split('/')[-1].split('?')[0]
                    team_abbr = self._get_team_abbreviation_fast(team_id)
            else:
                team_abbr = team_info.get('abbreviation', 'UNK')
            
            # Extract position
            position_info = athlete.get('position', {})
            pos_name = position_info.get('abbreviation', 'UNK')
            
            # Extract REAL statistics by following the statistics reference
            stats_ref = athlete.get('statistics', {}).get('$ref')
            if stats_ref:
                try:
                    stats_response = self.session.get(stats_ref, timeout=5)
                    stats_response.raise_for_status()
                    stats_data = stats_response.json()
                    
                    # Extract stats from the splits structure
                    splits = stats_data.get('splits', {})
                    if splits and 'categories' in splits:
                        stats_dict = {}
                        
                        # Parse all categories to find the stats we need
                        for category in splits['categories']:
                            if 'stats' in category:
                                for stat in category['stats']:
                                    stat_name = stat.get('name', '')
                                    stat_value = stat.get('value', 0)
                                    stats_dict[stat_name] = stat_value
                        
                        # Extract the stats we need for fantasy basketball
                        games_played = stats_dict.get('gamesPlayed', 0)
                        if games_played == 0:
                            games_played = 1  # Avoid division by zero
                        
                        points = stats_dict.get('points', 0)
                        rebounds = stats_dict.get('rebounds', 0)
                        assists = stats_dict.get('assists', 0)
                        steals = stats_dict.get('steals', 0)
                        blocks = stats_dict.get('blocks', 0)
                        turnovers = stats_dict.get('turnovers', 0)
                        
                        # Only return players with actual stats
                        if points > 0 or rebounds > 0 or assists > 0:
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
                    logger.warning(f"Error fetching stats for {name}: {e}")
            
            # If no stats found, skip this player
            logger.warning(f"No statistics found for {name}")
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting player info for {athlete.get('displayName', 'Unknown')}: {e}")
            return None
    
    def _get_team_abbreviation_fast(self, team_id: str) -> str:
        """Fast team abbreviation lookup."""
        team_map = {
            '1': 'ATL', '2': 'BOS', '3': 'BKN', '4': 'CHA', '5': 'CHI',
            '6': 'CLE', '7': 'DAL', '8': 'DEN', '9': 'DET', '10': 'GSW',
            '11': 'HOU', '12': 'IND', '13': 'LAC', '14': 'LAL', '15': 'MEM',
            '16': 'MIA', '17': 'MIL', '18': 'MIN', '19': 'NO', '20': 'NY',
            '21': 'OKC', '22': 'ORL', '23': 'PHI', '24': 'PHX', '25': 'POR',
            '26': 'SAC', '27': 'SA', '28': 'TOR', '29': 'UTA', '30': 'WSH'
        }
        return team_map.get(team_id, 'UNK')
    
    def _calculate_fantasy_points(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate ESPN fantasy points per game."""
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
    

def fetch_nba_data_public_api(season: Optional[int] = None) -> pd.DataFrame:
    """
    Fetch NBA player data using Public-ESPN-API repository patterns.
    
    This function uses the exact same patterns and approaches as the
    Public-ESPN-API repository, adapted for basketball.
    """
    if season is None:
        season = datetime.now().year
        if datetime.now().month < 10:
            season -= 1
    
    api = ESPNBasketballAPI()
    return api.get_nba_players_from_api(season)

if __name__ == "__main__":
    # Test the Public-ESPN-API pattern
    print("Testing Public-ESPN-API Basketball Pattern...")
    df = fetch_nba_data_public_api()
    print(f"Fetched {len(df)} players using Public-ESPN-API patterns")
    if not df.empty:
        print("\nTop 10 players by FPPG:")
        print(df[['Player', 'Team', 'Position', 'FPPG']].head(10))
