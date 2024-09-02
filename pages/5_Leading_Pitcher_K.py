import pandas as pd
from datetime import datetime, timedelta
import concurrent.futures
import statsapi
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import streamlit as st
import requests
from io import StringIO
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import plotly.graph_objects as go
from PIL import Image
from io import BytesIO


@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data

pitchers_data = load_data('datasets/complex_pitchers.csv')
team_ids = list(pitchers_data['team_id'].unique())

daySlate = []
current_date = datetime.now()
# current_date = datetime.now() + timedelta(days=1)

def fetch_schedule(team_id, current_date=current_date.strftime('%Y-%m-%d')):
    sched = statsapi.schedule(date=current_date,team=team_id)
    return sched

with ThreadPoolExecutor(max_workers=30) as executor:
    future_to_team = {executor.submit(fetch_schedule, team): team for team in team_ids}

    for future in as_completed(future_to_team):
        sched = future.result()
        for game in sched:
            # Convert game dict to a hashable form (tuple of items) for storing in a set
            if game not in daySlate:
                daySlate.append(game)

daySlate = pd.DataFrame(daySlate)

pitcher_names = daySlate['home_probable_pitcher'].to_list() + daySlate['away_probable_pitcher'].to_list()
pitcher_names = [x for x in pitcher_names if len(x) > 0]

# Things to add 
# - Add pitcher k prop for day
# - toggle for home/away
# - return last 10 games(offer slider)


url = 'http://3.132.201.233/data/all_prop_data.csv'
@st.cache_resource
def get_props(url):
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
        return pd.read_csv(data_io)


df = get_props(url)
df = df.drop_duplicates(['prop_id'], keep='last')

prop_lines = df.copy()
prop_lines = prop_lines[(prop_lines['league'] == 'MLB') & (prop_lines['position'] == 'P') & (prop_lines['player_name'].isin(pitcher_names)) & (prop_lines['odds_type'] == 'standard')]

k_lines = prop_lines[(prop_lines['stat_type'] == 'Pitcher Strikeouts') & (prop_lines['start_time'] == prop_lines['start_time'].max())]

numberOfGames = st.select_slider(label='Select the amount of games you would like to see', options=range(5,21))


pitchers_df = []

for pitcher in pitcher_names:
    try:
        k_line =  k_lines[k_lines['player_name'] == pitcher]['prop_line'].iloc[0]
    except:
        k_line = None

    
    pitcher_dict = {
        'Name' : pitcher,
        'Strikeout Line' : k_line
    }
    pitcher_df = pitchers_data[pitchers_data['Name'] == pitcher].sort_values(by='date', ascending=False).copy()
    gameNum = 0 
    for index, row in pitcher_df.head(numberOfGames).iterrows():
        gameNum += 1
        pitcher_dict[str(gameNum)] = row.get('k')
    pitchers_df.append(pitcher_dict)
    


pitchers_df = pd.DataFrame(pitchers_df)
pitchers_df = pitchers_df.sort_values(by='Strikeout Line', ascending=False)

st.dataframe(pitchers_df, hide_index=True)

# Initialize a dictionary to keep track of how often each pitcher leads
leading_counts = {pitcher: 0 for pitcher in pitchers_df['Name']}

# Iterate over each game column
for col in pitchers_df.columns[2:]:  # Skip the 'Name' column
    # Find the maximum strikeout value for the game
    max_k = pitchers_df[col].max()
    
    # Find the player(s) with this maximum strikeout
    max_players = pitchers_df[pitchers_df[col] == max_k]['Name'].tolist()
    
    # Increment the count for each leading player
    for player in max_players:
        leading_counts[player] += 1

# Convert the dictionary to a DataFrame for easier display and sorting
leading_counts_df = pd.DataFrame(list(leading_counts.items()), columns=['Pitcher', 'Leading Days'])
leading_counts_df = leading_counts_df.sort_values(by='Leading Days', ascending=False)

# Display the results
st.write("Number of days each pitcher is leading in strikeouts:")
st.dataframe(leading_counts_df)
