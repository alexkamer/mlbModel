import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import altair as alt
import requests
from io import StringIO
import re


# Notes: Team/Opponent Only returns a correct thing for both teams, both doesn't work

st.title('NRFI Finder')

@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data

pitcher_boxscores = load_data('datasets/complex_pitchers.csv')
simple_basic_gamelogs = load_data('datasets/basicGameLogs.csv')


pitcher_boxscores = pitcher_boxscores.sort_values(by='game_date', ascending=False)
pitcher_boxscores = pitcher_boxscores[pitcher_boxscores['isStarter']]


r_per_inning = load_data('datasets/r_per_inning.csv')



grouped_runs_df = r_per_inning.groupby(['game_id','homeOrAway']).agg({
    '1': 'sum', '2': 'sum', '3': 'sum', '4': 'sum',
    '5': 'sum', '6': 'sum', '7': 'sum', '8': 'sum', '9': 'sum'
    }).reset_index()


teams = pitcher_boxscores[pitcher_boxscores['seasonNumber'] == 2024]['Team'].unique()
game_id_dict = {}
game_date_dict= {}

number_of_games = st.select_slider(label='Select the number of games:', options=range(1,21))

for team in teams:
    game_id_dict[team] = pitcher_boxscores[pitcher_boxscores['Team'] == team]['game_id'].to_list()[:number_of_games]
    game_date_dict[team] = pitcher_boxscores[pitcher_boxscores['Team'] == team]['game_date'].to_list()[:number_of_games]



inning_selection = st.selectbox(
    options=list(range(1,10)),
    label= 'Select an Inning:'
)

# game_type = st.selectbox(
#     options=['Both', 'Team Only', 'Opponent Only'],
#     label='Select the NRFI Filter'
# )


display_df = []


#team_name = 'Houston Astros'

for team_name in sorted(teams):
    game_id_list = game_id_dict[team_name]


    merged_df = pd.merge(grouped_runs_df, pitcher_boxscores, on='game_id', how='inner').sort_values(by='game_date')
    merged_df = merged_df[::-1]

    full_df = merged_df[merged_df['game_id'].isin(game_id_list)].copy()

    team_df = full_df[full_df['Team'] == team_name].sort_values(by='game_date', ascending=False)
    # opponent_df = full_df[full_df['Team'] != team_name].sort_values(by='game_date', ascending=False)

    # combined_df = full_df.groupby(['game_id', 'game_date']).agg({
    #     '1': 'sum', '2': 'sum', '3': 'sum', '4': 'sum',
    #     '5': 'sum', '6': 'sum', '7': 'sum', '8': 'sum', '9': 'sum'
    #     }).reset_index().sort_values(by='game_date', ascending=False)





    stat_list = team_df[str(inning_selection)].to_list()



    display_dict = {'Team' : team_name}
    hit_rate = 0
    for x in range(1, number_of_games + 1):
        display_dict[str(x)] = stat_list[x-1]
        if stat_list[x-1] >0:
            hit_rate += 1
    display_dict['Hit Rate'] = f"{round(hit_rate/number_of_games,2) * 100}%"

    display_df.append(display_dict)




display_df = pd.DataFrame(display_df)
st.dataframe(display_df, hide_index=True)




