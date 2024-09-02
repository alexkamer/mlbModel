import streamlit as st
st.title('Prize Picks Analysis')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import altair as alt
import requests
from io import StringIO

import streamlit_shadcn_ui as ui
from streamlit_extras.image_in_tables import table_with_images
pd.set_option('display.max_columns', 500)

@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data


batter_boxscores = load_data('datasets/complex_batters.csv')
pitcher_boxscores = load_data('datasets/complex_pitchers.csv')


url = 'http://192.168.1.200/data/all_prop_data.csv'


response = requests.get(url)
# Check if the request was successful
if response.status_code == 200:
    data = response.content.decode('utf-8')
else:
    print(f"Failed to retrieve data: status code {response.status_code}")
    data = None
if data:
    # Convert string data to StringIO object
    data_io = StringIO(data)
    # Create DataFrame
    all_prop_df = pd.read_csv(data_io)

all_prop_df = all_prop_df.drop_duplicates(['prop_id'], keep='last')

mlbProps = all_prop_df[all_prop_df['league'] == 'MLB']
mlbLiveProps = all_prop_df[all_prop_df['league'] == 'MLBLIVE']

pitcher_boxscores.rename(columns={'Name':'player_name'}, inplace=True)
batter_boxscores.rename(columns={'Name' : 'player_name'}, inplace=True)
pitcher_merged_data = pd.merge(pitcher_boxscores, mlbProps, how='inner', left_on=['player_name', 'game_date'], right_on=['player_name', 'start_time'])
batter_merged_data = pd.merge(batter_boxscores, mlbProps, how='inner', left_on=['player_name', 'game_date'], right_on=['player_name', 'start_time'])


def check_batter_over(row):
    actual_stat = 0
    if row['stat_type'] == 'Total Bases':
        actual_stat = row['TB']
    elif row['stat_type'] == 'Hits+Runs+RBIs':
        actual_stat = row['H+R+RBIs']
    elif row['stat_type'] == 'Hitter Strikeouts':
        actual_stat = row['k']
    elif row['stat_type'] == 'Runs':
        actual_stat = row['r']
    elif row['stat_type'] == 'Hitter Fantasy Score':
        actual_stat = row['Batter Fantasy Score']
    elif row['stat_type'] == 'Stolen Bases':
        actual_stat = row['sb']
    elif row['stat_type'] == 'Home Runs':
        actual_stat = row['hr']
    elif row['stat_type'] == 'Singles':
        actual_stat = row['singles']
    elif row['stat_type'] == 'Hits':
        actual_stat = row['h']
    elif row['stat_type'] == 'Walks':
        actual_stat = row['bb']
    elif row['stat_type'] == 'Doubles':
        actual_stat = row['doubles']
    elif row['stat_type'] == 'RBIs':
        actual_stat = row['rbi']
    return (actual_stat > row['prop_line'], actual_stat)



def check_pitcher_over(row):
    actual_stat = 0
    if row['stat_type'] == 'Pitcher Strikeouts':
        actual_stat = row['k']
    elif row['stat_type'] == 'Walks Allowed':
        actual_stat = row['bb']
    elif row['stat_type'] == 'Hits Allowed':
        actual_stat = row['h']
    elif row['stat_type'] == 'Pitching Outs':
        actual_stat = row['pitching_outs']
    elif row['stat_type'] == 'Pitcher Fantasy Score':
        actual_stat = row['Pitcher Fantasy Score']
    return True if actual_stat > row['prop_line'] else False
pitcher_merged_data['Over_Under'] = pitcher_merged_data.apply(check_pitcher_over, axis=1)
batter_merged_data[['Over_Under', 'actual_stat']] = batter_merged_data.apply(check_batter_over, axis=1, result_type='expand')



pitcher_prop_info = pitcher_merged_data[pitcher_merged_data['position'] == 'P'][['image_url','Over_Under', 'player_name', 'Team_x', 'ip','k', 'bb', 'er', 'h', 'PitcherIsWinBool', 'isStarter','pitch_count_MA3', 'strikeout_MA3', 'walks_MA3', 'h_MA3', 'isWinner','Pitcher Fantasy Score', 'prop_line', 'odds_type','game_date', 'Opponent', 'stat_type', 'Opponent']].sort_values(by='game_date', ascending=False)
pitcher_prop_info = pitcher_prop_info.rename(columns={'Team_x': 'Team'})

batter_prop_info = batter_merged_data[batter_merged_data['position_y'] != 'P'][[ 'image_url','Over_Under', 'actual_stat', 'player_name', 'k', 'bb', 'r', 'h', 'Batter Fantasy Score', 'doubles','hr','sb', 'H+R+RBIs','isStarter', 'Team_x', 'game_date', 'prop_line', 'stat_type', 'odds_type', 'Opponent']].sort_values(by='game_date', ascending=False)
batter_prop_info = batter_prop_info.rename(columns={'Team_x': 'Team'})



#st.write(batter_prop_info['stat_type'].unique())

team_name = st.selectbox(
    options= sorted(batter_prop_info['Team'].unique()),
    label='Select a Team:'
)

hitterOrPitcher = st.selectbox(label='Hitters or Pitchers:', options=['Hitters', 'Pitchers'])

if hitterOrPitcher == 'Hitters':

    player_name = st.selectbox(
        options=sorted(batter_prop_info[batter_prop_info['Team'] == team_name]['player_name'].unique()),
        label='Select a player:'
    )

    player_prop_df = batter_prop_info[batter_prop_info['player_name'] == player_name]
else:

    player_name = st.selectbox(
        options=sorted(pitcher_prop_info[pitcher_prop_info['Team'] == team_name]['player_name'].unique()),
        label='Select a player:'
    )

    player_prop_df = pitcher_prop_info[pitcher_prop_info['player_name'] == player_name]


prop_type = st.selectbox(
    options=sorted(player_prop_df['stat_type'].unique()),
    label='Select a prop type:'
)

player_prop_df = player_prop_df[player_prop_df['stat_type'] == prop_type]

odds_type = st.selectbox(
    options=sorted(player_prop_df['odds_type'].unique()),
    label='Select an odds type:'
)

player_prop_df = player_prop_df[(player_prop_df['stat_type'] == prop_type) & (player_prop_df['odds_type'] == odds_type)]
player_prop_df['Over_Under'] = player_prop_df['Over_Under'].astype(int)


st.bar_chart(
    player_prop_df, x='game_date', y='Over_Under'
)

df_html = table_with_images(df=player_prop_df, url_columns=("image_url",))
st.markdown(df_html, unsafe_allow_html=True)



temp = batter_prop_info[batter_prop_info['odds_type'] == 'demon']
st.write(temp['Over_Under'].value_counts())