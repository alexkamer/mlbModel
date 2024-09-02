import streamlit as st
st.title('Batter Prop Comparison')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import altair as alt

@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data

df = load_data('datasets/complex_batters.csv')
predicted_lineups= load_data('datasets/predicted_lineups.csv')


teams = df['Team'].unique()
starting_pitchers = df['Opposing_Pitcher'].unique()

team_name = st.selectbox(
    label='Select a Team:',
    options = sorted(teams)
    )
if team_name:
    team_id = df[df['Team'] == team_name]['team_id'].iloc[0]

predicted_lineup = predicted_lineups[str(team_id)].to_list()


col1, col2 = st.columns(2)

with col1:
    player_name_1 = st.selectbox(
        label='Select a Player:',
        options = sorted(predicted_lineup)
        )
    player_1_df = df[(df['Name'] == player_name_1) & (df['isStarter'])]
    player_1_df = player_1_df.drop(['namefield', 'note','name','game_date','game_datetime','game_type','status','doubleheader','game_num', 'home_pitcher_note','away_pitcher_note','inning_state','national_broadcasts', 'series_status','losing_Team', 'summary'],axis=1)

with col2:
    player_name_2 = st.selectbox(
        label='Select a Player:',
        options = sorted([name for name in predicted_lineup if name != player_name_1])
        )
    player_2_df = df[(df['Name'] == player_name_2) & (df['isStarter'])]
    player_2_df = player_2_df.drop(['namefield', 'note','name','game_date','game_datetime','game_type','status','doubleheader','game_num', 'home_pitcher_note','away_pitcher_note','inning_state','national_broadcasts', 'series_status','losing_Team', 'summary'],axis=1)


common_elements = list(filter(lambda x: x in player_1_df['game_id'].to_list(), player_2_df['game_id'].to_list()))


player_1_df = player_1_df[player_1_df['game_id'].isin(common_elements)]
player_2_df = player_2_df[player_2_df['game_id'].isin(common_elements)]

player_1_df = player_1_df.rename(columns={
    'isWinner' : 'Team Won Game',
    'h' : 'Hits',
    'r' : 'Runs',
    'bb' : 'Walks',
    'k' : 'Strikeouts',
    'hr' : 'Homeruns',
    'sb' : 'Stolen Bases',
    'ab' : 'At Bats',
    'doubles' : 'Doubles',
    'triples' : 'Triples',
    'rbi' : 'Runs Batted In'
})

player_2_df = player_2_df.rename(columns={
    'isWinner' : 'Team Won Game',
    'h' : 'Hits',
    'r' : 'Runs',
    'bb' : 'Walks',
    'k' : 'Strikeouts',
    'hr' : 'Homeruns',
    'sb' : 'Stolen Bases',
    'ab' : 'At Bats',
    'doubles' : 'Doubles',
    'triples' : 'Triples',
    'rbi' : 'Runs Batted In'
})

prop_name = st.selectbox(
    label = 'Select a Prop:',
    options=sorted(['At Bats', 'Runs', 'Hits', 'Doubles', 'Triples', 'Homeruns', 'Runs Batted In', 'Stolen Bases', 'Walks', 'Strikeouts'])
)
stat_correl = st.multiselect(
    'Which stats would you like to include on the chart?',
    sorted(['Team Won Game', 'Pitcher Recorded Win','Innings Pitched', 'Hits Allowed', 'Runs Allowed', 'Earned Runs', 'Walks', 'Strikeouts', 'Homeruns Allowed', 'Pitches Thrown', 'Pitching Outs'])
)
number_of_games = st.select_slider(
    'Select the number of games for the sample size',
    options=range(1,len(common_elements) + 1))

num_same = 0

for index in range(0,number_of_games):
    if player_1_df[prop_name].to_list()[::-1][index] > 0.5 and player_2_df[prop_name].to_list()[::-1][index] > 0.5:
        num_same += 1

st.write(f"{num_same} / {number_of_games}")
col1,col2 = st.columns(2)

with col1:

    st.bar_chart(
    player_1_df.tail(number_of_games), x='date', y=prop_name
    )
    st.table(player_1_df.tail(number_of_games))

with col2:
    st.bar_chart(
    player_2_df.tail(number_of_games), x='date', y=prop_name
    )
    st.table(player_2_df.tail(number_of_games))

