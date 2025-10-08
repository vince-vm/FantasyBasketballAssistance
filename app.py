"""
Fantasy Basketball Draft Assistant
A Streamlit web app for NBA fantasy basketball draft preparation.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import io
import time
from api_utils import fetch_nba_data
from public_espn_api import fetch_nba_data_public_api

# Page configuration
st.set_page_config(
    page_title="Fantasy Basketball Draft Assistant",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern StatsMuse-Inspired CSS Design System
st.markdown("""
<style>
    /* Import Google Fonts for modern typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Root Variables for Design System */
    :root {
        --primary-color: #2563eb;
        --primary-dark: #1d4ed8;
        --primary-light: #3b82f6;
        --secondary-color: #64748b;
        --accent-color: #f59e0b;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --background-primary: #ffffff;
        --background-secondary: #f8fafc;
        --background-tertiary: #f1f5f9;
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-muted: #94a3b8;
        --border-color: #e2e8f0;
        --border-radius: 12px;
        --border-radius-lg: 16px;
        --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
        --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
    }
    
    /* Global Typography */
    .main-header {
        font-family: 'Inter', sans-serif;
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 3rem;
        background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }
    
    /* Modern Card System */
    .stats-card {
        background: var(--background-primary);
        border-radius: var(--border-radius-lg);
        padding: 2rem;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        margin-bottom: 1.5rem;
    }
    
    .stats-card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
    }
    
    .metric-card {
        background: linear-gradient(135deg, var(--background-primary), var(--background-secondary));
        border-radius: var(--border-radius);
        padding: 1.5rem;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border-color);
        margin: 0.75rem 0;
        transition: all 0.2s ease;
    }
    
    .metric-card:hover {
        box-shadow: var(--shadow-md);
        border-color: var(--primary-color);
    }
    
    /* Player Card Design */
    .player-card {
        background: var(--background-primary);
        border-radius: var(--border-radius);
        padding: 1.25rem;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border-color);
        margin: 0.75rem 0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .player-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, var(--primary-color), var(--accent-color));
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .player-card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
        border-color: var(--primary-color);
    }
    
    .player-card:hover::before {
        opacity: 1;
    }
    
    .player-name {
        font-family: 'Inter', sans-serif;
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }
    
    .player-stats {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        margin-top: 0.75rem;
    }
    
    .stat-item {
        background: var(--background-tertiary);
        padding: 0.5rem 0.75rem;
        border-radius: 8px;
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-secondary);
    }
    
    .stat-value {
        font-weight: 700;
        color: var(--primary-color);
    }
    
    /* Draft Tracker */
    .draft-tracker {
        background: linear-gradient(135deg, #fef3c7, #fde68a);
        border-radius: var(--border-radius-lg);
        padding: 1.5rem;
        box-shadow: var(--shadow-md);
        border: 1px solid #f59e0b;
        margin: 1.5rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .draft-tracker::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, var(--accent-color), #fbbf24);
    }
    
    /* Modern Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
        color: white;
        border-radius: var(--border-radius);
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        font-size: 0.875rem;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
        text-transform: none;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--primary-dark), var(--primary-color));
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }
    
    .draft-button {
        background: linear-gradient(135deg, var(--success-color), #059669) !important;
        font-size: 0.75rem !important;
        padding: 0.5rem 1rem !important;
    }
    
    .draft-button:hover {
        background: linear-gradient(135deg, #059669, var(--success-color)) !important;
    }
    
    /* Data Table Styling */
    .stDataFrame {
        border-radius: var(--border-radius-lg);
        overflow: hidden;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-color);
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: var(--background-secondary);
        border-right: 1px solid var(--border-color);
    }
    
    /* Section Headers */
    .section-header {
        font-family: 'Inter', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--border-color);
    }
    
    /* Loading Spinner */
    .loading-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 300px;
        flex-direction: column;
        background: var(--background-secondary);
        border-radius: var(--border-radius-lg);
        margin: 2rem 0;
    }
    
    .spinner {
        width: 80px;
        height: 80px;
        border: 4px solid var(--border-color);
        border-top: 4px solid var(--primary-color);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 1.5rem;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .loading-text {
        font-family: 'Inter', sans-serif;
        font-size: 1.125rem;
        color: var(--text-secondary);
        font-weight: 500;
        text-align: center;
    }
    
    /* Maintenance Message */
    .maintenance-message {
        background: linear-gradient(135deg, #fef3c7, #fde68a);
        border: 1px solid var(--accent-color);
        border-radius: var(--border-radius-lg);
        padding: 3rem;
        text-align: center;
        margin: 3rem 0;
        box-shadow: var(--shadow-lg);
    }
    
    .maintenance-title {
        font-family: 'Inter', sans-serif;
        font-size: 2rem;
        color: #92400e;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    .maintenance-text {
        font-family: 'Inter', sans-serif;
        font-size: 1.125rem;
        color: #92400e;
        font-weight: 400;
    }
    
    /* Quick Draft Section */
    .quick-draft-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .quick-draft-item {
        background: var(--background-primary);
        border-radius: var(--border-radius);
        padding: 1rem;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border-color);
        text-align: center;
        transition: all 0.2s ease;
    }
    
    .quick-draft-item:hover {
        box-shadow: var(--shadow-md);
        border-color: var(--primary-color);
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2.5rem;
        }
        
        .player-stats {
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .quick-draft-grid {
            grid-template-columns: 1fr;
        }
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--background-tertiary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'players_data' not in st.session_state:
        st.session_state.players_data = pd.DataFrame()
    
    if 'drafted_players' not in st.session_state:
        st.session_state.drafted_players = set()
    
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = None
    
    if 'filtered_data' not in st.session_state:
        st.session_state.filtered_data = pd.DataFrame()
    
    if 'data_loading' not in st.session_state:
        st.session_state.data_loading = False
    
    if 'api_error' not in st.session_state:
        st.session_state.api_error = False

def load_player_data():
    """Load player data from ESPN API with caching."""
    st.session_state.data_loading = True
    st.session_state.api_error = False
    
    try:
        # Use a faster timeout and concurrent requests
        data = fetch_nba_data_public_api()
        
        if not data.empty and len(data) > 100:  # Ensure we got real data (not sample)
            st.session_state.players_data = data
            st.session_state.last_refresh = datetime.now()
            st.session_state.data_loading = False
            return True
        else:
            st.session_state.api_error = True
            st.session_state.data_loading = False
            return False
            
    except Exception as e:
        st.session_state.api_error = True
        st.session_state.data_loading = False
        return False

def should_refresh_data():
    """Check if data should be refreshed based on cache timing."""
    if st.session_state.last_refresh is None:
        return True
    
    # Refresh every 30 minutes to get injury updates
    cache_duration = timedelta(minutes=30)
    return datetime.now() - st.session_state.last_refresh > cache_duration

def show_loading_spinner():
    """Show fancy loading spinner."""
    st.markdown("""
    <div class="loading-container">
        <div class="spinner"></div>
        <div class="loading-text">Loading player data...</div>
    </div>
    """, unsafe_allow_html=True)

def show_maintenance_message():
    """Show maintenance message when API fails."""
    st.markdown("""
    <div class="maintenance-message">
        <div class="maintenance-title">🔧 Website Under Maintenance</div>
        <div class="maintenance-text">
            We're currently updating our player data. Please try again in a few minutes.
            <br><br>
            If this issue persists, please contact support.
        </div>
    </div>
    """, unsafe_allow_html=True)

def filter_players(data, position_filter, name_search):
    """Filter players based on position and name search."""
    filtered = data.copy()
    
    # Filter by position
    if position_filter != "All Positions":
        filtered = filtered[filtered['Position'] == position_filter]
    
    # Filter by name search
    if name_search:
        filtered = filtered[
            filtered['Player'].str.contains(name_search, case=False, na=False)
        ]
    
    # Remove drafted players
    if st.session_state.drafted_players:
        filtered = filtered[~filtered['Player'].isin(st.session_state.drafted_players)]
    
    return filtered

def export_data(data, format_type):
    """Export data in specified format."""
    if format_type == "CSV":
        csv = data.to_csv(index=False)
        return csv.encode('utf-8'), "text/csv", "players_data.csv"
    elif format_type == "JSON":
        json_str = data.to_json(orient='records', indent=2)
        return json_str.encode('utf-8'), "application/json", "players_data.json"

def main():
    """Main application function."""
    initialize_session_state()
    
    # Auto-load data if needed
    if should_refresh_data() and not st.session_state.data_loading:
        load_player_data()
    
    # Show loading spinner if data is loading
    if st.session_state.data_loading:
        show_loading_spinner()
        st.stop()
    
    # Show maintenance message if API failed
    if st.session_state.api_error:
        show_maintenance_message()
        st.stop()
    
    # Header
    st.markdown('<h1 class="main-header">🏀 Fantasy Basketball Draft Assistant</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Controls")
        
        # Data refresh section
        st.subheader("📊 Data Status")
        
        if st.session_state.last_refresh:
            st.caption(f"Last updated: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.caption("Data not loaded yet")
        
        # Filters
        st.subheader("🔍 Filters")
        
        # Position filter
        if not st.session_state.players_data.empty:
            positions = ["All Positions"] + sorted(st.session_state.players_data['Position'].unique().tolist())
            position_filter = st.selectbox("Position", positions)
        else:
            position_filter = "All Positions"
        
        # Name search
        name_search = st.text_input("Search Player Name", placeholder="Enter player name...")
        
        # Draft tracker
        st.subheader("📝 Draft Tracker")
        st.markdown('<div class="draft-tracker">', unsafe_allow_html=True)
        
        if st.session_state.drafted_players:
            st.write(f"**Drafted Players ({len(st.session_state.drafted_players)}):**")
            for player in sorted(st.session_state.drafted_players):
                if st.button(f"❌ {player}", key=f"remove_{player}"):
                    st.session_state.drafted_players.remove(player)
                    st.rerun()
        else:
            st.write("No players drafted yet")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Export options
        st.subheader("📤 Export Data")
        export_format = st.selectbox("Export Format", ["CSV", "JSON"])
        
        if not st.session_state.filtered_data.empty:
            if st.button("📥 Download Data"):
                data_bytes, mime_type, filename = export_data(st.session_state.filtered_data, export_format)
                st.download_button(
                    label=f"Download {export_format}",
                    data=data_bytes,
                    file_name=filename,
                    mime=mime_type
                )
    
    # Main content area
    if st.session_state.players_data.empty:
        st.info("📊 Player data is automatically loaded and refreshed every 30 minutes.")
        
        # Show ESPN scoring explanation
        st.subheader("📋 ESPN Points Scoring System")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **Positive Categories:**
            - Points: × 1.0
            - Rebounds: × 1.2
            - Assists: × 1.5
            """)
        
        with col2:
            st.markdown("""
            **Defensive Categories:**
            - Steals: × 3.0
            - Blocks: × 3.0
            """)
        
        with col3:
            st.markdown("""
            **Negative Category:**
            - Turnovers: × -1.0
            """)
        
        st.markdown("**FPPG = (PTS × 1) + (REB × 1.2) + (AST × 1.5) + (STL × 3) + (BLK × 3) + (TO × -1)**")
        
    else:
        # Filter data
        st.session_state.filtered_data = filter_players(
            st.session_state.players_data, 
            position_filter, 
            name_search
        )
        
        # Modern Summary Cards
        st.markdown('<h2 class="section-header">📊 Dashboard Overview</h2>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'''
            <div class="metric-card">
                <div style="font-size: 2rem; font-weight: 700; color: var(--primary-color); margin-bottom: 0.5rem;">
                    {len(st.session_state.filtered_data)}
                </div>
                <div style="font-size: 0.875rem; color: var(--text-secondary); font-weight: 500;">
                    Available Players
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            if not st.session_state.filtered_data.empty:
                avg_fppg = st.session_state.filtered_data['FPPG'].mean()
                st.markdown(f'''
                <div class="metric-card">
                    <div style="font-size: 2rem; font-weight: 700; color: var(--success-color); margin-bottom: 0.5rem;">
                        {avg_fppg:.1f}
                    </div>
                    <div style="font-size: 0.875rem; color: var(--text-secondary); font-weight: 500;">
                        Average FPPG
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown('''
                <div class="metric-card">
                    <div style="font-size: 2rem; font-weight: 700; color: var(--text-muted); margin-bottom: 0.5rem;">
                        N/A
                    </div>
                    <div style="font-size: 0.875rem; color: var(--text-secondary); font-weight: 500;">
                        Average FPPG
                    </div>
                </div>
                ''', unsafe_allow_html=True)
        
        with col3:
            if not st.session_state.filtered_data.empty:
                top_player = st.session_state.filtered_data.iloc[0]['Player']
                top_fppg = st.session_state.filtered_data.iloc[0]['FPPG']
                st.markdown(f'''
                <div class="metric-card">
                    <div style="font-size: 1.25rem; font-weight: 700; color: var(--accent-color); margin-bottom: 0.5rem;">
                        {top_player}
                    </div>
                    <div style="font-size: 0.875rem; color: var(--text-secondary); font-weight: 500;">
                        Top Player ({top_fppg:.1f} FPPG)
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown('''
                <div class="metric-card">
                    <div style="font-size: 2rem; font-weight: 700; color: var(--text-muted); margin-bottom: 0.5rem;">
                        N/A
                    </div>
                    <div style="font-size: 0.875rem; color: var(--text-secondary); font-weight: 500;">
                        Top Player
                    </div>
                </div>
                ''', unsafe_allow_html=True)
        
        with col4:
            st.markdown(f'''
            <div class="metric-card">
                <div style="font-size: 2rem; font-weight: 700; color: var(--warning-color); margin-bottom: 0.5rem;">
                    {len(st.session_state.drafted_players)}
                </div>
                <div style="font-size: 0.875rem; color: var(--text-secondary); font-weight: 500;">
                    Players Drafted
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        # Modern Player Rankings with Card Design
        st.markdown('<h2 class="section-header">🏆 Player Rankings</h2>', unsafe_allow_html=True)
        
        if not st.session_state.filtered_data.empty:
            # Display columns selection
            display_cols = st.multiselect(
                "Select columns to display:",
                options=['Player', 'Team', 'Position', 'GP', 'PTS_PG', 'REB_PG', 
                        'AST_PG', 'STL_PG', 'BLK_PG', 'TO_PG', 'FPPG', 'Total'],
                default=['Player', 'Team', 'Position', 'GP', 'PTS_PG', 'REB_PG', 
                        'AST_PG', 'STL_PG', 'BLK_PG', 'TO_PG', 'FPPG']
            )
            
            if display_cols:
                display_data = st.session_state.filtered_data[display_cols].copy()
                
                # Modern Player Cards
                if 'Player' in display_cols:
                    for idx, row in display_data.iterrows():
                        player_name = row['Player']
                        if player_name not in st.session_state.drafted_players:
                            # Create modern player card with safe column access
                            team = row.get('Team', 'UNK')
                            position = row.get('Position', 'UNK')
                            fppg = row.get('FPPG', 0)
                            
                            st.markdown(f'''
                            <div class="player-card">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                                    <div>
                                        <div class="player-name">{player_name}</div>
                                        <div style="font-size: 0.875rem; color: var(--text-secondary);">
                                            {team} • {position}
                                        </div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary-color);">
                                            {fppg:.1f}
                                        </div>
                                        <div style="font-size: 0.75rem; color: var(--text-muted);">
                                            FPPG
                                        </div>
                                    </div>
                                </div>
                            </div>
                            ''', unsafe_allow_html=True)
                            
                            # Stats row
                            stats_html = '<div class="player-stats">'
                            for col in display_cols:
                                if col not in ['Player', 'Team', 'Position', 'FPPG'] and col in row.index:
                                    try:
                                        stats_html += f'''
                                        <div class="stat-item">
                                            {col}: <span class="stat-value">{row[col]:.1f}</span>
                                        </div>
                                        '''
                                    except (ValueError, TypeError):
                                        # Handle non-numeric values
                                        stats_html += f'''
                                        <div class="stat-item">
                                            {col}: <span class="stat-value">{row[col]}</span>
                                        </div>
                                        '''
                            stats_html += '</div>'
                            st.markdown(stats_html, unsafe_allow_html=True)
                            
                            # Draft button
                            col1, col2, col3 = st.columns([1, 1, 1])
                            with col2:
                                if st.button("🎯 Draft Player", key=f"draft_{player_name}", help=f"Draft {player_name}"):
                                    st.session_state.drafted_players.add(player_name)
                                    st.rerun()
                            
                            st.markdown('<br>', unsafe_allow_html=True)
                
                # Alternative: Show as dataframe with draft functionality
                st.subheader("📊 Full Rankings Table")
                
                # Add a column for draft status
                display_data_with_draft = display_data.copy()
                if not display_data_with_draft.empty and 'Player' in display_data_with_draft.columns:
                    display_data_with_draft['Draft Status'] = display_data_with_draft['Player'].apply(
                        lambda x: "✅ Drafted" if x in st.session_state.drafted_players else "⭕ Available"
                    )
                
                # Filter out drafted players from the table if desired
                show_drafted = st.checkbox("Show drafted players in table", value=False)
                if not show_drafted and not display_data_with_draft.empty and 'Player' in display_data_with_draft.columns:
                    display_data_with_draft = display_data_with_draft[
                        ~display_data_with_draft['Player'].isin(st.session_state.drafted_players)
                    ]
                
                st.dataframe(
                    display_data_with_draft,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Modern Quick Draft Grid
                st.markdown('<h2 class="section-header">⚡ Quick Draft</h2>', unsafe_allow_html=True)
                if not display_data_with_draft.empty and 'Player' in display_data_with_draft.columns:
                    top_available = display_data_with_draft.head(10)
                    
                    # Create modern grid layout
                    st.markdown('<div class="quick-draft-grid">', unsafe_allow_html=True)
                    
                    cols = st.columns(5)
                    for i, (_, player) in enumerate(top_available.iterrows()):
                        if i < 10 and player['Player'] not in st.session_state.drafted_players:
                            with cols[i % 5]:
                                # Safely get values with fallbacks
                                team = player.get('Team', 'UNK')
                                position = player.get('Position', 'UNK')
                                fppg = player.get('FPPG', 0)
                                
                                st.markdown(f'''
                                <div class="quick-draft-item">
                                    <div style="font-weight: 600; margin-bottom: 0.5rem;">{player['Player']}</div>
                                    <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.75rem;">
                                        {team} • {position}
                                    </div>
                                    <div style="font-size: 1.25rem; font-weight: 700; color: var(--primary-color); margin-bottom: 0.75rem;">
                                        {fppg:.1f} FPPG
                                    </div>
                                </div>
                                ''', unsafe_allow_html=True)
                                
                                if st.button("🎯 Draft", key=f"quick_draft_{player['Player']}", help=f"Draft {player['Player']}"):
                                    st.session_state.drafted_players.add(player['Player'])
                                    st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
        
        else:
            st.warning("No players match your current filters.")
        
        # Modern Analytics Charts
        if not st.session_state.filtered_data.empty and len(st.session_state.filtered_data) > 1:
            st.markdown('<h2 class="section-header">📊 Analytics Dashboard</h2>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="stats-card">', unsafe_allow_html=True)
                st.markdown('<h3 style="font-family: Inter, sans-serif; font-weight: 600; margin-bottom: 1rem;">Position Distribution</h3>', unsafe_allow_html=True)
                
                position_counts = st.session_state.filtered_data['Position'].value_counts()
                
                fig = px.pie(
                    values=position_counts.values,
                    names=position_counts.index,
                    color_discrete_sequence=['#2563eb', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6']
                )
                fig.update_layout(
                    font_family="Inter",
                    font_size=12,
                    showlegend=True,
                    legend=dict(
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.01
                    )
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="stats-card">', unsafe_allow_html=True)
                st.markdown('<h3 style="font-family: Inter, sans-serif; font-weight: 600; margin-bottom: 1rem;">FPPG by Position</h3>', unsafe_allow_html=True)
                
                fig_box = px.box(
                    st.session_state.filtered_data,
                    x='Position',
                    y='FPPG',
                    color='Position',
                    color_discrete_sequence=['#2563eb', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6']
                )
                fig_box.update_layout(
                    font_family="Inter",
                    font_size=12,
                    showlegend=False,
                    xaxis_title="Position",
                    yaxis_title="Fantasy Points Per Game"
                )
                st.plotly_chart(fig_box, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
