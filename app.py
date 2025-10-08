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

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1f4e79, #2e7d32);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2e7d32;
        margin: 0.5rem 0;
    }
    
    .draft-tracker {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    
    .stDataFrame {
        border-radius: 0.5rem;
        overflow: hidden;
    }
    
    .stButton > button {
        background-color: #2e7d32;
        color: white;
        border-radius: 0.5rem;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background-color: #1b5e20;
        color: white;
    }
    
    /* Fancy Loading Spinner */
    .loading-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 200px;
        flex-direction: column;
    }
    
    .spinner {
        width: 60px;
        height: 60px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #2e7d32;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 20px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .loading-text {
        font-size: 18px;
        color: #2e7d32;
        font-weight: bold;
        text-align: center;
    }
    
    .maintenance-message {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 2rem;
        text-align: center;
        margin: 2rem 0;
    }
    
    .maintenance-title {
        font-size: 24px;
        color: #856404;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    .maintenance-text {
        font-size: 16px;
        color: #856404;
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
        
        # Summary metrics
        st.subheader("📈 Summary Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Players", len(st.session_state.filtered_data))
        
        with col2:
            if not st.session_state.filtered_data.empty:
                avg_fppg = st.session_state.filtered_data['FPPG'].mean()
                st.metric("Avg FPPG", f"{avg_fppg:.1f}")
            else:
                st.metric("Avg FPPG", "N/A")
        
        with col3:
            if not st.session_state.filtered_data.empty:
                top_player = st.session_state.filtered_data.iloc[0]['Player']
                top_fppg = st.session_state.filtered_data.iloc[0]['FPPG']
                st.metric("Top Player", f"{top_player} ({top_fppg:.1f})")
            else:
                st.metric("Top Player", "N/A")
        
        with col4:
            st.metric("Drafted", len(st.session_state.drafted_players))
        
        # Player rankings table
        st.subheader("🏆 Player Rankings")
        
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
                
                # Add draft buttons
                if 'Player' in display_cols:
                    player_col_idx = display_cols.index('Player')
                    
                    # Create a custom dataframe with draft buttons
                    for idx, row in display_data.iterrows():
                        player_name = row['Player']
                        if player_name not in st.session_state.drafted_players:
                            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                            
                            with col1:
                                st.write(f"**{player_name}**")
                            
                            with col2:
                                st.write(f"**{row['Team']}**")
                            
                            with col3:
                                st.write(f"**{row['Position']}**")
                            
                            with col4:
                                st.write(f"**{row['FPPG']:.1f}**")
                            
                            with col5:
                                if st.button("Draft", key=f"draft_{player_name}"):
                                    st.session_state.drafted_players.add(player_name)
                                    st.rerun()
                            
                            # Show other stats in a compact format
                            if len(display_cols) > 4:
                                stats_text = " | ".join([f"{col}: {row[col]:.1f}" for col in display_cols[4:] if col != 'Player'])
                                st.caption(stats_text)
                            
                            st.divider()
                
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
                
                # Quick draft buttons for top players
                st.subheader("⚡ Quick Draft (Top 10 Available)")
                if not display_data_with_draft.empty and 'Player' in display_data_with_draft.columns:
                    top_available = display_data_with_draft.head(10)
                    
                    cols = st.columns(5)
                    for i, (_, player) in enumerate(top_available.iterrows()):
                        if i < 10 and player['Player'] not in st.session_state.drafted_players:
                            with cols[i % 5]:
                                if st.button(f"Draft {player['Player']}", key=f"quick_draft_{player['Player']}"):
                                    st.session_state.drafted_players.add(player['Player'])
                                    st.rerun()
        
        else:
            st.warning("No players match your current filters.")
        
        # Position distribution chart
        if not st.session_state.filtered_data.empty and len(st.session_state.filtered_data) > 1:
            st.subheader("📊 Position Distribution")
            
            position_counts = st.session_state.filtered_data['Position'].value_counts()
            
            fig = px.pie(
                values=position_counts.values,
                names=position_counts.index,
                title="Available Players by Position"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # FPPG distribution by position
            st.subheader("📈 FPPG Distribution by Position")
            
            fig_box = px.box(
                st.session_state.filtered_data,
                x='Position',
                y='FPPG',
                title="Fantasy Points Per Game by Position"
            )
            st.plotly_chart(fig_box, use_container_width=True)

if __name__ == "__main__":
    main()
