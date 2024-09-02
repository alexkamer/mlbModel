import streamlit as st
st.title('Team Per Inning Analysis')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import altair as alt
import requests
from io import StringIO
import re


def implied_probability_to_american_odds(implied_prob):
    try:
        if implied_prob < 0.5:
            return f"+{int((100 / implied_prob) - 100)}"
        elif implied_prob == 0:
            return 0
        else:
            return f"-{int((100 / implied_prob))}"
    except:
        return "Adjust game slider"

pd.set_option('display.max_columns', 500)

@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data


pitcher_boxscores = load_data('datasets/complex_pitchers.csv')
pitcher_boxscores = pitcher_boxscores[(pitcher_boxscores['isStarter']) & (pitcher_boxscores['seasonNumber'] == 2024)]
basic_gamelogs = load_data('datasets/basicGameLogs.csv')


simple_basic_gamelogs = basic_gamelogs[['game_id', 'home_name', 'away_name', 'game_date', 'home_id', 'away_id']].copy()



k_per_inning = load_data('datasets/k_per_inning.csv')
h_per_inning = load_data('datasets/h_per_inning.csv')
pitches_per_inning = load_data('datasets/pitches_per_inning.csv')
r_per_inning = load_data('datasets/r_per_inning.csv')
bb_per_inning = load_data('datasets/bb_per_inning.csv')
hr_per_inning = load_data('datasets/hr_per_inning.csv')


col1, col2 = st.columns(2)
with col1:
    team_name = st.selectbox(
        options=sorted(pitcher_boxscores['Team'].unique()),
        label='Select a Team:'
    )
    

    team_gamelog = pitcher_boxscores[pitcher_boxscores['Team'] == team_name].copy()
    team_gamelog = team_gamelog.sort_values(by='date')
    team_gamelog = team_gamelog[::-1]
    game_id_list = team_gamelog['game_id'].to_list()

with col2:
    stat_type = st.selectbox(
        options=sorted(['Strikeouts Per Inning', 'Hits Per Inning', 'Pitches Thrown Per Inning', 'Runs Per Inning', 'Home Runs Hit Per Inning', 'Walks Per Inning']),
        label='Select a stat type:'
    )


#st.write(game_id_list)


if stat_type == 'Strikeouts Per Inning':
    merged_df = k_per_inning.merge(simple_basic_gamelogs, on='game_id', how='left')
    merged_df['Team'] = np.where(merged_df['homeOrAway'] == 'home', merged_df['home_name'], merged_df['away_name'])
    merged_df['team_id'] = np.where(merged_df['homeOrAway'] == 'home', merged_df['home_id'], merged_df['away_id'])

    stat_df = merged_df.drop(['home_name', 'away_name'], axis=1)
    stat_df = stat_df[(stat_df['game_id'].isin(game_id_list)) & (stat_df['Team'] != team_name)].sort_values(by='game_date', ascending=False)
    grouped_df = stat_df.groupby('game_id').agg({
        'Team' : 'first',
        'game_date': 'first',  # Keeps the first date found for each game_id
        '1': 'sum', '2': 'sum', '3': 'sum', '4': 'sum',
        '5': 'sum', '6': 'sum', '7': 'sum', '8': 'sum', '9': 'sum'
        }).reset_index()
    grouped_df = grouped_df.sort_values(by='game_date', ascending=False)

elif stat_type == 'Pitches Thrown Per Inning':
    merged_df = pitches_per_inning.merge(simple_basic_gamelogs, on='game_id', how='left')
    merged_df['Team'] = np.where(merged_df['homeOrAway'] == 'home', merged_df['home_name'], merged_df['away_name'])
    merged_df['team_id'] = np.where(merged_df['homeOrAway'] == 'home', merged_df['home_id'], merged_df['away_id'])

    stat_df = merged_df.drop(['home_name', 'away_name'], axis=1)
    stat_df = stat_df[(stat_df['game_id'].isin(game_id_list)) & (stat_df['Team'] != team_name)].sort_values(by='game_date', ascending=False)
    grouped_df = stat_df.groupby('game_id').agg({
        'Team' : 'first',
        'game_date': 'first',  # Keeps the first date found for each game_id
        '1': 'sum', '2': 'sum', '3': 'sum', '4': 'sum',
        '5': 'sum', '6': 'sum', '7': 'sum', '8': 'sum', '9': 'sum'
        }).reset_index()
    grouped_df = grouped_df.sort_values(by='game_date', ascending=False)

elif stat_type == 'Runs Per Inning':
    merged_df = r_per_inning.merge(simple_basic_gamelogs, on='game_id', how='left')
    merged_df['Team'] = np.where(merged_df['homeOrAway'] == 'home', merged_df['home_name'], merged_df['away_name'])
    merged_df['team_id'] = np.where(merged_df['homeOrAway'] == 'home', merged_df['home_id'], merged_df['away_id'])

    stat_df = merged_df.drop(['home_name', 'away_name'], axis=1)
    stat_df = stat_df[(stat_df['game_id'].isin(game_id_list)) & (stat_df['Team'] != team_name)].sort_values(by='game_date', ascending=False)
    grouped_df = stat_df.groupby('game_id').agg({
        'Team' : 'first',
        'game_date': 'first',  # Keeps the first date found for each game_id
        '1': 'sum', '2': 'sum', '3': 'sum', '4': 'sum',
        '5': 'sum', '6': 'sum', '7': 'sum', '8': 'sum', '9': 'sum'
        }).reset_index()
    grouped_df = grouped_df.sort_values(by='game_date', ascending=False)

elif stat_type == 'Home Runs Hit Per Inning':
    merged_df = hr_per_inning.merge(simple_basic_gamelogs, on='game_id', how='left')
    merged_df['Team'] = np.where(merged_df['homeOrAway'] == 'home', merged_df['home_name'], merged_df['away_name'])
    merged_df['team_id'] = np.where(merged_df['homeOrAway'] == 'home', merged_df['home_id'], merged_df['away_id'])

    stat_df = merged_df.drop(['home_name', 'away_name'], axis=1)
    stat_df = stat_df[(stat_df['game_id'].isin(game_id_list)) & (stat_df['Team'] != team_name)].sort_values(by='game_date', ascending=False)
    grouped_df = stat_df.groupby('game_id').agg({
        'Team' : 'first',
        'game_date': 'first',  # Keeps the first date found for each game_id
        '1': 'sum', '2': 'sum', '3': 'sum', '4': 'sum',
        '5': 'sum', '6': 'sum', '7': 'sum', '8': 'sum', '9': 'sum'
        }).reset_index()
    grouped_df = grouped_df.sort_values(by='game_date', ascending=False)

elif stat_type == 'Walks Per Inning':
    merged_df = bb_per_inning.merge(simple_basic_gamelogs, on='game_id', how='left')
    merged_df['Team'] = np.where(merged_df['homeOrAway'] == 'home', merged_df['home_name'], merged_df['away_name'])
    merged_df['team_id'] = np.where(merged_df['homeOrAway'] == 'home', merged_df['home_id'], merged_df['away_id'])

    stat_df = merged_df.drop(['home_name', 'away_name'], axis=1)
    stat_df = stat_df[(stat_df['game_id'].isin(game_id_list)) & (stat_df['Team'] != team_name)].sort_values(by='game_date', ascending=False)
    grouped_df = stat_df.groupby('game_id').agg({
        'Team' : 'first',
        'game_date': 'first',  # Keeps the first date found for each game_id
        '1': 'sum', '2': 'sum', '3': 'sum', '4': 'sum',
        '5': 'sum', '6': 'sum', '7': 'sum', '8': 'sum', '9': 'sum'
        }).reset_index()
    grouped_df = grouped_df.sort_values(by='game_date', ascending=False)



elif stat_type == 'Hits Per Inning':
    merged_df = h_per_inning.merge(simple_basic_gamelogs, on='game_id', how='left')
    merged_df['Team'] = np.where(merged_df['homeOrAway'] == 'home', merged_df['home_name'], merged_df['away_name'])
    merged_df['team_id'] = np.where(merged_df['homeOrAway'] == 'home', merged_df['home_id'], merged_df['away_id'])
    stat_df = merged_df.drop(['home_name', 'away_name'], axis=1)
    stat_df = stat_df[(stat_df['game_id'].isin(game_id_list)) & (stat_df['Team'] != team_name)].sort_values(by='game_date', ascending=False)

    grouped_df = stat_df.groupby('game_id').agg({
        'Team' : 'first',
        'game_date': 'first',  # Keeps the first date found for each game_id
        '1': 'sum', '2': 'sum', '3': 'sum', '4': 'sum',
        '5': 'sum', '6': 'sum', '7': 'sum', '8': 'sum', '9': 'sum'
        }).reset_index()
    grouped_df = grouped_df.sort_values(by='game_date', ascending=False)


number_of_games = st.select_slider(
    label='Select the number of games for the sample size',
    options=range(1,len(grouped_df) + 1))

innings = st.multiselect(
    options=[str(x) for x in range(1,10)],
    label='Select an Inning:'
)

if len(innings) > 0:
    grouped_df['Sum'] = sum([grouped_df[str(inning)] for inning in innings])


chart_data = grouped_df.copy()
chart_data['Label'] = chart_data['game_date'] + "\n" + chart_data['Team']

stat_list = chart_data['Sum'].to_list()

st.bar_chart(chart_data.head(number_of_games), x='Label', y='Sum')

#st.table(stat_df.head(number_of_games))
st.table(grouped_df.head(number_of_games))
