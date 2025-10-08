# 🏀 Fantasy Basketball Draft Assistant

A Streamlit web application that helps you prepare for your NBA fantasy basketball draft by providing live player rankings based on ESPN's fantasy scoring system.

## ✨ Features

- **Live Data**: Fetches real-time NBA player statistics from ESPN's fantasy API
- **ESPN Scoring**: Applies ESPN's default points scoring system:
  - Points: × 1.0
  - Rebounds: × 1.2  
  - Assists: × 1.5
  - Steals: × 3.0
  - Blocks: × 3.0
  - Turnovers: × -1.0
- **Interactive Rankings**: Sortable and filterable player rankings by Fantasy Points Per Game (FPPG)
- **Draft Tracker**: Mark players as drafted to remove them from available rankings
- **Position Filtering**: Filter players by position (PG, SG, SF, PF, C)
- **Search**: Search for specific players by name
- **Export**: Download rankings as CSV or JSON for external use
- **Session Persistence**: Drafted players stay removed even after page refresh
- **Modern UI**: Clean, responsive design with wide layout

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package installer)

### Installation

1. **Clone or download this repository**
   ```bash
   cd /path/to/AIFantasyBasketball
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser**
   - The app will automatically open at `http://localhost:8501`
   - If it doesn't open automatically, manually navigate to the URL shown in your terminal

## 📚 ESPN API Integration

This app uses the community-discovered ESPN API endpoints documented in the [Public-ESPN-API repository](https://github.com/pseudo-r/Public-ESPN-API). The implementation tries multiple approaches:

1. **Fantasy API**: `https://fantasy.espn.com/apis/v3/games/fba/seasons/{season}/segments/0/leagues/standard`
2. **Sports Core API**: `https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/seasons/{season}/athletes`
3. **Athletes with Stats**: `https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/seasons/{season}/athletes?statistics=true`

### Important Notes About ESPN API

⚠️ **The ESPN API is unofficial and undocumented**. ESPN does not provide official support for these endpoints. Key considerations:

- **Instability**: Endpoints may change or be removed without notice
- **No SLA**: No service level agreements or official support
- **Terms of Service**: Usage may violate ESPN's ToS
- **Rate Limiting**: Unknown rate limits may apply

The app includes robust error handling and falls back to sample data when the API is unavailable.

### Testing ESPN API Endpoints

To test the ESPN API endpoints directly, run the example script:

```bash
python3 espn_api_example.py
```

This script demonstrates:
- Fetching NBA players from Sports Core API
- Getting players with statistics
- Accessing fantasy basketball data
- Retrieving team information
- Getting individual player statistics

## 📖 How to Use

### 1. Load Player Data
- Click "🔄 Refresh Player Data" in the sidebar to fetch live NBA statistics
- Wait for the data to load (this may take a few seconds)

### 2. View Rankings
- Players are automatically ranked by Fantasy Points Per Game (FPPG)
- Use the position filter to focus on specific positions
- Search for specific players using the name search box

### 3. Track Your Draft
- Click "Draft" next to any player to mark them as drafted
- Drafted players are removed from available rankings
- View all drafted players in the sidebar
- Remove players from drafted list if needed

### 4. Export Data
- Use the export section in the sidebar to download rankings
- Choose between CSV or JSON format
- Exported data includes all current filters and excludes drafted players

### 5. Analyze Performance
- View position distribution charts
- Compare FPPG across different positions
- Use summary statistics to understand player pools

## 🛠️ Technical Details

### Architecture
- **Frontend**: Streamlit web framework
- **Data Source**: ESPN Fantasy Basketball API
- **Data Processing**: Pandas for data manipulation and analysis
- **Visualization**: Plotly for interactive charts

### File Structure
```
AIFantasyBasketball/
├── app.py              # Main Streamlit application
├── api_utils.py        # ESPN API client and data processing
├── espn_api_example.py # Example script showing direct ESPN API usage
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### Key Components

#### `api_utils.py`
- `ESPNFantasyAPI`: Main API client class
- `fetch_nba_data()`: Convenience function to get player data
- Handles data normalization and ESPN scoring calculations

#### `app.py`
- Main Streamlit application
- Session state management for draft tracking
- Interactive UI components and data visualization

#### `espn_api_example.py`
- Standalone example script demonstrating direct ESPN API usage
- Shows how to use the community-discovered endpoints
- Useful for understanding the API structure and testing endpoints

## 🔧 Customization

### Scoring System
To modify the scoring system, edit the `_calculate_fantasy_points()` method in `api_utils.py`:

```python
df['FPPG'] = (
    df['PTS_PG'] * 1.0 +      # Points multiplier
    df['REB_PG'] * 1.2 +      # Rebounds multiplier
    df['AST_PG'] * 1.5 +      # Assists multiplier
    df['STL_PG'] * 3.0 +      # Steals multiplier
    df['BLK_PG'] * 3.0 +      # Blocks multiplier
    df['TO_PG'] * -1.0        # Turnovers multiplier
).round(2)
```

### Data Columns
Add or remove columns by modifying the `display_cols` options in `app.py`.

### Styling
Customize the appearance by modifying the CSS in the `st.markdown()` section of `app.py`.

## 🐛 Troubleshooting

### Common Issues

1. **"No player data found"**
   - The ESPN API might be temporarily unavailable
   - Try refreshing the data after a few minutes
   - Check your internet connection

2. **Slow loading**
   - The ESPN API can be slow during peak times
   - Consider running the app during off-peak hours
   - The first load is typically slower than subsequent refreshes

3. **Missing players**
   - Some players might not appear if they haven't played enough games
   - Players with 0 games played are filtered out
   - Check if the player is on a different team or injured

### Error Messages
- **API request failed**: Network or ESPN API issue
- **No valid player data extracted**: Data format changed or API unavailable
- **Unexpected error**: Check the terminal for detailed error messages

## 🔮 Future Enhancements

- **Position Scarcity**: Add Value Over Replacement Player (VORP) calculations
- **Team Fit Analysis**: Consider team needs and roster construction
- **Category Scoring**: Support for 8-category and 9-category leagues
- **Injury Risk**: Integrate injury probability data
- **Chrome Extension**: Browser overlay for ESPN draft pages
- **Mock Drafts**: Simulate draft scenarios
- **Player Comparisons**: Side-by-side player analysis

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## ⚠️ Disclaimer

This tool is for entertainment and educational purposes only. It is not affiliated with ESPN or the NBA. Use at your own discretion during your fantasy basketball draft.
