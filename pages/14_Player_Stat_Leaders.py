import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

st.title('MLB Player Stat Leaders')

@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    data['game_date'] = pd.to_datetime(data['game_date'])
    data['month'] = data['game_date'].dt.month
    return data

def generate_date_list(start, end):
    delta = end - start
    return [start + timedelta(days=i) for i in range(delta.days + 1)]

@st.cache_data
def process_data(df, position_selection, filter_str, date_range=None):
    if filter_str == 'Home':
        df = df[df['Team'] == df['home_name']]
    elif filter_str == 'Away':
        df = df[df['Team'] == df['away_name']]
    elif filter_str == 'Current Month':
        df = df[df['month'] == datetime.now().month]
    elif filter_str == 'Specific Date Range' and date_range:
        date_list = generate_date_list(date_range[0], date_range[1])
        df = df[df['game_date'].isin(date_list)]

    if position_selection == 'Hitters':
        grouped_df = df.groupby('personId').agg({
            'Name': 'first', 'personId': 'size', 'ab': 'sum', 'r': 'sum', 'h': 'sum', 'k': 'sum',
            'hr': 'sum', 'rbi': 'sum', 'sb': 'sum', 'bb': 'sum', 'TB': 'sum', 'doubles': 'sum',
            'triples': 'sum', 'isStarter': 'sum'
        }).rename(columns={
            'personId': 'Games Played in', 'isStarter': 'Games Started', 'doubles': 'Doubles',
            'triples': 'Triples', 'ab': 'At Bats', 'r': 'Runs Scored', 'h': 'Hits',
            'k': 'Batter Strikeouts', 'hr': 'Home Runs', 'rbi': 'Runs Batted In',
            'sb': 'Stolen Bases', 'bb': 'Batter Walks', 'TB': 'Total Bases'
        })
    else:
        grouped_df = df.groupby('personId').agg({
            'Name': 'first', 'personId': 'size', 'ip': 'sum', 'h': 'sum', 'r': 'sum',
            'er': 'sum', 'bb': 'sum', 'k': 'sum', 'hr': 'sum', 'p': 'sum', 's': 'sum'
        }).rename(columns={'personId': 'Games Started'})

        grouped_df['Earned Run Average'] = round((grouped_df['er'] / grouped_df['ip']) * 9, 3)
        grouped_df['Walks/Hits Allowed Per Inning'] = round((grouped_df['bb'] + grouped_df['h']) / grouped_df['ip'], 3)
        grouped_df = grouped_df.rename(columns={
            'ip': 'Innings Pitched', 'h': 'Hits Allowed', 'r': 'Runs Allowed',
            'er': 'Earned Runs Allowed', 'bb': 'Walks Allowed', 'k': 'Pitcher Strikeouts',
            'hr': 'Home Runs Allowed', 'p': 'Pitches Thrown', 's': 'Strikes Thrown'
        })

    return grouped_df

def create_chart(data, stat, num_players):
    chart = alt.Chart(data).mark_bar().encode(
        y=alt.Y('Name:N', sort='-x'),
        x=alt.X(f'{stat}:Q'),
        color=alt.Color(f'{stat}:Q', scale=alt.Scale(scheme='viridis')),
        tooltip=['Name', stat]
    ).properties(
        width=500,
        height=300,
        title=f'Top {num_players} in {stat}'
    )
    text = chart.mark_text(
        align='left',
        baseline='middle',
        dx=3  # Nudges text to right so it doesn't appear on top of the bar
    ).encode(
        text=alt.Text(f'{stat}:Q', format='.2f')
    )
    return (chart + text).interactive()

pitcher_boxscores = load_data('datasets/complex_pitchers.csv')
batter_boxscores = load_data('datasets/complex_batters.csv')

pitcher_boxscores = pitcher_boxscores[pitcher_boxscores['seasonNumber'] == 2024]
batter_boxscores = batter_boxscores[batter_boxscores['seasonNumber'] == 2024]

position_selection = st.selectbox('Select if you would like Hitter or Pitcher Stats:', ['Hitters', 'Pitchers'])

stat_df = batter_boxscores if position_selection == 'Hitters' else pitcher_boxscores[pitcher_boxscores['isStarter']]

tabs_filters = {
    'Overall': None,
    'Home': 'Home',
    'Away': 'Away',
    'Current Month': 'Current Month',
    'Specific Date Range': 'Specific Date Range'
}

num_of_players = st.select_slider('Select The Number of Players to Include:', options=range(1, 21))

tabs = st.tabs(list(tabs_filters.keys()))

for tab, filter_str in zip(tabs, tabs_filters.values()):
    with tab:
        date_range = None
        if filter_str == 'Specific Date Range':
            min_date = stat_df['game_date'].min()
            max_date = stat_df['game_date'].max()
            date_range = st.date_input('Select a date range:', value=(min_date, max_date),
                                       min_value=min_date, max_value=max_date)

        grouped_display_df = process_data(stat_df, position_selection, filter_str, date_range)

        container_headers = list(grouped_display_df.columns)
        container_headers.remove('Name')

        for i in range(0, len(container_headers), 2):
            col1, col2 = st.columns(2)
            with col1:
                if i < len(container_headers):
                    chart = create_chart(grouped_display_df, container_headers[i], num_of_players)
                    st.altair_chart(chart,use_container_width=True)
            with col2:
                if i+1 < len(container_headers):
                    chart = create_chart(grouped_display_df, container_headers[i+1], num_of_players)
                    st.altair_chart(chart,use_container_width=True)


