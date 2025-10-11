import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO

# Page configuration
st.set_page_config(
    page_title="Fantasy Basketball Draft Assistant",
    page_icon="🏀",
    layout="wide"
)

# ESPN Default Scoring Weights
SCORING_WEIGHTS = {
    'PTS': 1.0,
    'REB': 1.2,
    'AST': 1.5,
    'STL': 3.0,
    'BLK': 3.0,
    'TO': -1.0
}

def calculate_fantasy_points(row):
    """Calculate fantasy points per game using ESPN scoring system"""
    fppg = 0
    for stat, weight in SCORING_WEIGHTS.items():
        if stat in row and pd.notna(row[stat]):
            fppg += row[stat] * weight
    return fppg

def calculate_total_fantasy_points(row):
    """Calculate total fantasy points if GP (Games Played) exists"""
    if 'GP' in row and pd.notna(row['GP']) and row['GP'] > 0:
        return row['FPPG'] * row['GP']
    return None

def load_and_process_data(uploaded_file):
    """Load CSV and calculate fantasy points"""
    try:
        # Read CSV
        df = pd.read_csv(uploaded_file)
        
        # Calculate FPPG
        df['FPPG'] = df.apply(calculate_fantasy_points, axis=1)
        
        # Calculate Total if GP exists
        df['Total'] = df.apply(calculate_total_fantasy_points, axis=1)
        
        return df
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None

def filter_players(df, drafted_players, position_filter, name_filter):
    """Filter players based on drafted status, position, and name"""
    # Remove drafted players
    if drafted_players:
        df = df[~df['Player'].isin(drafted_players)]
    
    # Filter by position
    if position_filter != "All":
        df = df[df['Pos'] == position_filter]
    
    # Filter by name
    if name_filter:
        df = df[df['Player'].str.contains(name_filter, case=False, na=False)]
    
    return df

def main():
    st.title("🏀 Fantasy Basketball Draft Assistant")
    st.markdown("**ESPN Default Scoring System** - PTS×1, REB×1.2, AST×1.5, STL×3, BLK×3, TO×-1")
    
    # Initialize session state
    if 'drafted_players' not in st.session_state:
        st.session_state.drafted_players = []
    if 'df' not in st.session_state:
        st.session_state.df = None
    
    # Sidebar for controls
    with st.sidebar:
        st.header("📊 Controls")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload Player Projections CSV",
            type=['csv'],
            help="Upload a CSV with columns: Player, Pos, PTS, REB, AST, STL, BLK, TO, GP (optional)"
        )
        
        if uploaded_file is not None:
            if st.session_state.df is None or st.button("🔄 Reload Data"):
                st.session_state.df = load_and_process_data(uploaded_file)
        
        # Drafted players management
        st.subheader("👥 Drafted Players")
        
        # Add drafted player
        new_drafted = st.text_input("Add drafted player:", placeholder="Enter player name")
        if st.button("Add to Drafted") and new_drafted:
            if new_drafted not in st.session_state.drafted_players:
                st.session_state.drafted_players.append(new_drafted)
                st.success(f"Added {new_drafted} to drafted list")
            else:
                st.warning(f"{new_drafted} is already in drafted list")
        
        # Show drafted players
        if st.session_state.drafted_players:
            st.write("**Currently Drafted:**")
            for i, player in enumerate(st.session_state.drafted_players):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{i+1}. {player}")
                with col2:
                    if st.button("❌", key=f"remove_{i}"):
                        st.session_state.drafted_players.remove(player)
                        st.rerun()
        
        # Clear all drafted
        if st.button("🗑️ Clear All Drafted"):
            st.session_state.drafted_players = []
            st.rerun()
    
    # Main content area
    if st.session_state.df is not None:
        df = st.session_state.df.copy()
        
        # Filters
        st.header("🔍 Filters & Sorting")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Position filter
            positions = ["All"] + sorted(df['Pos'].unique().tolist())
            position_filter = st.selectbox("Filter by Position:", positions)
        
        with col2:
            # Name filter
            name_filter = st.text_input("Filter by Player Name:", placeholder="Search players...")
        
        with col3:
            # Sort options
            sort_by = st.selectbox("Sort by:", ["FPPG", "Total"])
            sort_ascending = st.checkbox("Ascending", value=False)
        
        # Apply filters
        filtered_df = filter_players(df, st.session_state.drafted_players, position_filter, name_filter)
        
        # Sort data
        if sort_by == "FPPG":
            filtered_df = filtered_df.sort_values('FPPG', ascending=sort_ascending)
        else:
            # For Total, handle NaN values by putting them at the end
            filtered_df = filtered_df.sort_values('Total', ascending=sort_ascending, na_position='last')
        
        # Display rankings
        st.header("📈 Player Rankings")
        
        # Show summary stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Available Players", len(filtered_df))
        with col2:
            st.metric("Drafted Players", len(st.session_state.drafted_players))
        with col3:
            if len(filtered_df) > 0:
                st.metric("Top FPPG", f"{filtered_df.iloc[0]['FPPG']:.1f}")
        with col4:
            if len(filtered_df) > 0 and pd.notna(filtered_df.iloc[0]['Total']):
                st.metric("Top Total", f"{filtered_df.iloc[0]['Total']:.1f}")
        
        # Display table
        if len(filtered_df) > 0:
            # Select columns to display
            display_columns = ['Player', 'Pos', 'FPPG', 'Total']
            
            # Add stat columns if they exist
            stat_columns = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'TO']
            for col in stat_columns:
                if col in filtered_df.columns:
                    display_columns.append(col)
            
            # Add GP if it exists
            if 'GP' in filtered_df.columns:
                display_columns.append('GP')
            
            # Create display dataframe
            display_df = filtered_df[display_columns].copy()
            
            # Format numbers
            if 'FPPG' in display_df.columns:
                display_df['FPPG'] = display_df['FPPG'].round(1)
            if 'Total' in display_df.columns:
                display_df['Total'] = display_df['Total'].round(1)
            
            # Add ranking
            display_df.insert(0, 'Rank', range(1, len(display_df) + 1))
            
            # Display table
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Export button
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Rankings as CSV",
                data=csv,
                file_name=f"fantasy_rankings_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No players match the current filters.")
    
    else:
        st.info("👆 Please upload a CSV file with player projections to get started.")
        
        # Show expected format
        st.subheader("Expected CSV Format:")
        st.code("""
Player,Pos,PTS,REB,AST,STL,BLK,TO,GP
LeBron James,SF,25.0,7.5,7.0,1.2,0.8,3.5,70
Stephen Curry,PG,30.0,5.0,6.0,1.5,0.3,3.0,75
...
        """, language="csv")

if __name__ == "__main__":
    main()
