import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import altair as alt
st.set_page_config(layout="wide")

st.title('MLB Player Stat Leaders')

@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data

def generate_date_list(start, end):
    delta = end - start  # timedelta
    return [start + timedelta(days=i) for i in range(delta.days + 1)]

def layout_headers(headers, stat_df, num_of_players, cols_per_row=2):
    # Calculate how many rows are needed
    row_count = (len(headers) + cols_per_row - 1) // cols_per_row  # This ensures all headers are included

    # Create a grid layout
    for i in range(row_count):
        # Create a row with specified number of columns
        cols = st.columns(cols_per_row)
        # Fill each column in the current row
        for j in range(cols_per_row):
            index = i * cols_per_row + j
            if index < len(headers):
                if headers[index] in stat_df.columns:
                    temp_df = stat_df.copy()
                    temp_df = temp_df.sort_values(by=headers[index], ascending=False)
                    temp_df = temp_df[['Name', headers[index]]].head(num_of_players)

                    fig, ax = plt.subplots(figsize=(10, 6))

                    colors = plt.cm.viridis(np.linspace(0, 1, num_of_players))
                    bars = ax.barh(temp_df['Name'].to_list()[::-1], temp_df[headers[index]].to_list()[::-1], color=colors)
                    
                    for bar in bars:
                        value = bar.get_width()
                        ax.text(value, bar.get_y() + bar.get_height() / 2, f'{value:.2f}', va='center', ha='left', fontweight='bold')

                    # Customizations
                    ax.set_xlabel(headers[index], fontsize=12)
                    ax.set_ylabel('Name', fontsize=12)
                    ax.set_title(f'Top {num_of_players} in {headers[index]}', fontsize=14, fontweight='bold')
                    ax.tick_params(axis='both', which='major', labelsize=10)

                    plt.tight_layout()

                    # Show plot in Streamlit
                    cols[j].pyplot(fig)
                    plt.close(fig)  # Close the figure to free up memory

            else:
                # If no more headers, break out of the loop
                break



pitcher_boxscores = load_data('datasets/complex_pitchers.csv')
batter_boxscores = load_data('datasets/complex_batters.csv')

pitcher_boxscores = pitcher_boxscores[pitcher_boxscores['seasonNumber'] == 2024]
batter_boxscores = batter_boxscores[batter_boxscores['seasonNumber'] == 2024]

current_month = datetime.now().month

position_selection = st.selectbox(options=['Hitters', 'Pitchers'], label='Select if you would like Hitter or Pitcher Stats:')

if position_selection == 'Hitters':
    stat_df = batter_boxscores.copy()
else:
    stat_df = pitcher_boxscores[pitcher_boxscores['isStarter']].copy()


stat_df['game_date'] = pd.to_datetime(stat_df['game_date'])

stat_df['month'] = stat_df['game_date'].dt.month


tabs_filters = {
    'Overall' : None,
    'Home' : 'Home',
    'Away' : 'Away',
    'Current Month' : 'Current Month',
    'Specific Date Range' : 'Specific Date Range'

}
num_of_players = st.select_slider(label='Select The Number of Players to Include:', options=range(1,21))


tabs = st.tabs(list(tabs_filters.keys()))

for tab, filter_str in zip(tabs, tabs_filters.values()):
    with tab:
        if filter_str is None:
            display_df = stat_df.copy()
        elif filter_str == 'Home':
            display_df = stat_df[stat_df['Team'] == stat_df['home_name']].copy()
        elif filter_str == 'Away':
            display_df = stat_df[stat_df['Team'] == stat_df['away_name']].copy()
        elif filter_str == 'Current Month':
            display_df = stat_df[stat_df['month'] == current_month]
        elif filter_str == 'Specific Date Range':
            display_df = stat_df.copy()
            display_df = display_df.sort_values(by='game_date')
            min_date = display_df['game_date'].iloc[0]
            max_date = display_df['game_date'].iloc[-1]
            d = st.date_input(label='Select a date range:', value=(min_date,max_date), min_value=min_date,max_value=max_date)
            
            if d:
                date_list = generate_date_list(d[0],d[1])
            display_df = display_df[display_df['game_date'].isin(date_list)]
            

        stat_leaders = []
        player_id = sorted(display_df['personId'].unique())
        if position_selection == 'Hitters':
            grouped_display_df = display_df.groupby('personId').agg({
                'Name' : 'first', 'personId' : 'size', 'ab': 'sum','r' : 'sum', 'h' : 'sum', 'k' : 'sum', 'hr' : 'sum', 'rbi' : 'sum', 'sb' : 'sum', 'bb' : 'sum', 'TB' : 'sum', 'doubles' : 'sum', 'triples' : 'sum', 'isStarter' : 'sum'
            }).rename(columns={'personId' : 'Games Played in', 'isStarter': 'Games Started', 'doubles' : 'Doubles', 'triples': 'Triples'})

            grouped_display_df = grouped_display_df.rename(columns={'ab' : 'At Bats', 'r': 'Runs Scored', 'h' : 'Hits', 'k' : 'Batter Strikeouts', 'hr' : 'Home Runs', 'rbi' : 'Runs Batted In', 'sb' : 'Stolen Bases', 'bb' : 'Batter Walks', 'TB' : 'Total Bases'})
        else:
            grouped_display_df = display_df.groupby('personId').agg({
                'Name' : 'first', 'personId' : 'size', 'ip' : 'sum', 'h' : 'sum', 'r' : 'sum', 'er' : 'sum', 'bb' : 'sum', 'k' : 'sum', 'hr' : 'sum', 'p' : 'sum', 's': 'sum'
            }).rename(columns={'personId' : 'Games Started'})

            grouped_display_df['era'] = round((grouped_display_df['er'].astype(int) / grouped_display_df['ip'].astype(float)) * 9,3)
            grouped_display_df['whip'] = round((grouped_display_df['bb'].astype(int) + grouped_display_df['h'].astype(int)) / grouped_display_df['ip'].astype(float),3)
            grouped_display_df = grouped_display_df.rename(columns={'ip' : 'Innings Pitched', 'h': 'Hits Allowed', 'r' : 'Runs Allowed', 'er' : 'Earned Runs Allowed', 'bb' : 'Walks Allowed', 'k' : 'Pitcher Strikeouts', 'hr' : 'Home Runs Allowed', 'p' : 'Pitches Thrown', 's' : 'Strikes Thrown', 'era' : 'Earned Run Average', 'whip' : 'Walks/Hits Allowed Per Inning'})



        container_headers = list(grouped_display_df.columns)
        container_headers.remove('Name')

        layout_headers(sorted(container_headers), grouped_display_df, num_of_players)


