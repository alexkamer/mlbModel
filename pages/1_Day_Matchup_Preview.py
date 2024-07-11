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
st.set_page_config(layout="wide")

@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data
batter_boxscores = load_data('datasets/complex_batters.csv')
pitcher_boxscores = load_data('datasets/complex_pitchers.csv')
predicted_lineups = load_data('datasets/predicted_lineups.csv')
mlb_team_logo_df = load_data('datasets/MLB_Team_Logos.csv')


batter_boxscores = batter_boxscores.sort_values(by='game_datetime')
pitcher_boxscores = pitcher_boxscores.sort_values(by='game_datetime')
basic_gamelogs = load_data('datasets/basicGameLogs.csv')
basic_gamelogs = basic_gamelogs[basic_gamelogs['game_type'] == 'R']

url = 'http://192.168.1.200/data/daySlate.csv'


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
    daySlate = pd.read_csv(data_io)



game_options = []
for idx, row in daySlate.iterrows():
    game_options.append(f"{row['away_name']} @ {row['home_name']}")

game_option = st.selectbox(
    label='Select a Game:',
    options = sorted(game_options)
    )
if game_option:
    row = daySlate[daySlate['away_name'] == game_option.split(" @ ")[0]]
    game_id = row['game_id'].iloc[0]
    away_team = row['away_name'].iloc[0]
    home_team = row['home_name'].iloc[0]
    away_logo = mlb_team_logo_df[mlb_team_logo_df['Team'] == row['away_name'].iloc[0]]['Logos'].iloc[0]
    home_logo = mlb_team_logo_df[mlb_team_logo_df['Team'] == row['home_name'].iloc[0]]['Logos'].iloc[0]

    away_id = row['away_id'].iloc[0]
    home_id = row['home_id'].iloc[0]
    game_boxscore = statsapi.boxscore_data(game_id)


    away_lineup_df = pd.DataFrame(game_boxscore.get('awayBatters')[1:])
    home_lineup_df = pd.DataFrame(game_boxscore.get('homeBatters')[1:])

batter_boxscores = batter_boxscores.rename(columns={'player_name' : 'Name'})
pitcher_boxscores = pitcher_boxscores.rename(columns={'player_name' : 'Name'})

id_to_name = dict(zip(batter_boxscores['personId'], batter_boxscores['Name']))


# Create a new list of player names
try:
    away_lineup = [id_to_name[player_id] for player_id in away_lineup_df['personId'].to_list()]
    home_lineup = [id_to_name[player_id] for player_id in home_lineup_df['personId'].to_list()]
except:
    st.write('Lineups not released yet, predicted lineups:')
    away_lineup = predicted_lineups[str(away_id)].to_list()
    home_lineup = predicted_lineups[str(home_id)].to_list()


#st.table(row[['game_id', 'game_date', 'status', 'away_name', 'home_name', 'away_score', 'home_score', 'home_probable_pitcher', 'away_probable_pitcher']])

st.header('Head to Head Matchups')
currentHomeAway = st.checkbox('With current home/away?')

if currentHomeAway:
    head_to_head = basic_gamelogs[(basic_gamelogs['away_id'] == away_id) & (basic_gamelogs['home_id'] == home_id)].sort_values(by='game_datetime')
else:
    head_to_head = basic_gamelogs[((basic_gamelogs['away_id'] == away_id) & (basic_gamelogs['home_id'] == home_id) | (basic_gamelogs['away_id'] == home_id) & (basic_gamelogs['home_id'] == away_id))].sort_values(by='game_datetime')
 

head_to_head_num_games = st.select_slider(options=range(1,len(head_to_head) + 1), label='Select the number of games: ')

head_to_head = head_to_head[::-1]
display_head_to_head = head_to_head[['game_date', 'away_name', 'home_name', 'home_probable_pitcher', 'away_probable_pitcher', 'away_score', 'home_score', 'venue_name', 'winning_team', 'losing_team']].copy()
display_head_to_head = display_head_to_head.head(head_to_head_num_games)

average_runs = round((display_head_to_head['away_score'].sum() + display_head_to_head['home_score'].sum()) / head_to_head_num_games,2)
st.write(f"Average runs per game in these samples: {average_runs}")
st.write(f"{away_team}  {len(display_head_to_head[display_head_to_head['winning_team'] == away_team])} - {len(display_head_to_head[display_head_to_head['winning_team'] == home_team])}  {home_team}")

display_head_to_head['Run Total'] = display_head_to_head['away_score'] + display_head_to_head['home_score']
display_head_to_head['Run Diff'] = abs(display_head_to_head['home_score'] - display_head_to_head['away_score'])
display_head_to_head['Home Team Won'] = display_head_to_head['winning_team'] == display_head_to_head['home_name']


st.dataframe(display_head_to_head, hide_index=True)




away_team_games = pitcher_boxscores[(pitcher_boxscores['isStarter']) & (pitcher_boxscores['Team'] == away_team)][::-1]
home_team_games = pitcher_boxscores[(pitcher_boxscores['isStarter']) & (pitcher_boxscores['Team'] == home_team)][::-1]

numGames = 5

away_team_l5 = []
home_team_l5 = []

away_wins = 0
home_wins = 0
# Edit code here

def create_game_summary(r):
    winner = 'W' if r['isWinner'] else 'L'
    homeAway = '@' if r['Team'] == r['away_name'] else 'vs.'
    opposingPitcher = r['home_probable_pitcher'] if r['Team'] == r['away_name'] else r['away_probable_pitcher']
    return f"{winner} {r['away_score']}-{r['home_score']} {homeAway} {r['Opponent']}"

away_team_l5 = [create_game_summary(r) for _, r in away_team_games[:numGames].iterrows()]
home_team_l5 = [create_game_summary(r) for _, r in home_team_games[:numGames].iterrows()]

away_wins = sum(1 for game in away_team_l5 if game.startswith('W'))
home_wins = sum(1 for game in home_team_l5 if game.startswith('W'))

col1, col2 = st.columns(2)
with col1:
    st.subheader(f"{away_team} {away_wins}-{numGames - away_wins}")
    for game in away_team_l5:
        st.markdown(f"- {game}")

with col2:
    st.subheader(f"{home_team} {home_wins}-{numGames - home_wins}")
    for game in home_team_l5:
        st.markdown(f"- {game}")

st.markdown("---")





away_team_preview = []
home_team_preview = []

away_team_projection = []
home_team_projection = []

player = away_lineup[0]

battingOrder = 100
for player in away_lineup:
    # player_df = batter_boxscores[(batter_boxscores['Name'] == player) & (batter_boxscores['isStarter'])]

    player_df = batter_boxscores[(batter_boxscores['Name'] == player) & (batter_boxscores['isStarter']) & (batter_boxscores['battingOrder'] == battingOrder)]
    #player_df = player_df[player_df['Team'] == player_df['away_name']]
    player_df = player_df.tail(10)
    away_team_preview.append({
        'Name' : player,
        'battingOrder' : battingOrder,
        'Batting Average' : round(player_df['avg'].mean(),3),
        'AtBats' : round(player_df['ab'].mean(),2),
        'Hits' : round(player_df['h'].mean(),1),
        'Strikeouts' : round(player_df['k'].mean(),1),
        'Runs' : player_df['r'].mean(),
        'Doubles' : player_df['doubles'].mean(),
        'Triples' : player_df['triples'].mean(),
        'Homeruns' : player_df['hr'].mean(),
        'RBIs' : player_df['rbi'].mean(),
        'Stolen Bases' : player_df['sb'].mean(),
        'Walks' : player_df['bb'].mean(),
        'OPS' : player_df['ops'].mean(),
        'OBP' : player_df['obp'].mean(),
        'Total Bases' : player_df['TB'].mean(),
        'Projected Strikeouts' : round(player_df['team_strikeouts'].mean() * player_df['average_of_team_strikeouts'].mean(),2),
        'Projected Hits' : round(player_df['team_hits'].mean() * player_df['average_of_team_hits'].mean(),2),
        'Projected Walks' : round(player_df['team_walks'].mean() * player_df['average_of_team_walks'].mean(),2)
    })

    away_team_projection.append({
        'Name' : player,
        'Projected Strikeouts' : round(player_df['team_strikeouts'].mean() * player_df['average_of_team_strikeouts'].mean(),2),
        'Projected Hits' : round(player_df['team_hits'].mean() * player_df['average_of_team_hits'].mean(),2),
        'Projected Walks' : round(player_df['team_walks'].mean() * player_df['average_of_team_walks'].mean(),2)  ,
        'Projected Runs' : round(player_df['team_runs'].mean() * player_df['average_of_team_runs'].mean(),2)      
    })

    battingOrder += 100


battingOrder = 100



for player in home_lineup:
    # player_df = batter_boxscores[(batter_boxscores['Name'] == player) & (batter_boxscores['isStarter'])]
    player_df = batter_boxscores[(batter_boxscores['Name'] == player) & (batter_boxscores['isStarter']) & (batter_boxscores['battingOrder'] == battingOrder)]


    #player_df = player_df[player_df['Team'] == player_df['home_name']]


    player_df = player_df.tail(10)

    home_team_preview.append({
        'Name' : player,
        'battingOrder' : battingOrder,
        'Batting Average' : round(player_df['avg'].mean(),3),
        'AtBats' : round(player_df['ab'].mean(),2),
        'Hits' : round(player_df['h'].mean(),1),
        'Strikeouts' : player_df['k'].mean(),
        'Runs' : player_df['r'].mean(),
        'Doubles' : player_df['doubles'].mean(),
        'Triples' : player_df['triples'].mean(),
        'Homeruns' : player_df['hr'].mean(),
        'RBIs' : player_df['rbi'].mean(),
        'Stolen Bases' : player_df['sb'].mean(),
        'Walks' : player_df['bb'].mean(),
        'OPS' : player_df['ops'].mean(),
        'OBP' : player_df['obp'].mean(),
        'Total Bases' : player_df['TB'].mean(),
        'Projected Strikeouts' : round(player_df['team_strikeouts'].mean() * player_df['average_of_team_strikeouts'].mean(),2),
        'Projected Hits' : round(player_df['team_hits'].mean() * player_df['average_of_team_hits'].mean(),2),
        'Projected Walks' : round(player_df['team_walks'].mean() * player_df['average_of_team_walks'].mean(),2)
    })
    home_team_projection.append({
        'Name' : player,
        'Projected Strikeouts' : round(player_df['team_strikeouts'].mean() * player_df['average_of_team_strikeouts'].mean(),2),
        'Projected Hits' : round(player_df['team_hits'].mean() * player_df['average_of_team_hits'].mean(),2),
        'Projected Walks' : round(player_df['team_walks'].mean() * player_df['average_of_team_walks'].mean(),2),
        'Projected Runs' : round(player_df['team_runs'].mean() * player_df['average_of_team_runs'].mean(),2)        
    })

    battingOrder += 100

away_team_preview = pd.DataFrame(away_team_preview)
home_team_preview = pd.DataFrame(home_team_preview)
away_team_projection = pd.DataFrame(away_team_projection)
home_team_projection = pd.DataFrame(home_team_projection)


st.header('Batter Previews')

total_row = pd.DataFrame(away_team_projection.sum()).transpose()
total_row.index = ['Total']
away_team_projection = pd.concat([away_team_projection,total_row])

total_row = pd.DataFrame(home_team_projection.sum()).transpose()
total_row.index = ['Total']
home_team_projection = pd.concat([home_team_projection,total_row])

st.write(f"Matchup prediction {away_team}: {round(away_team_projection.at['Total' , 'Projected Runs'],3)} @ {home_team} : {round(home_team_projection.at['Total' , 'Projected Runs'],3)}")

col1, col2 = st.columns(2)
with col1:
    st.dataframe(away_team_preview, hide_index=True)
    st.dataframe(away_team_projection, hide_index=True)

with col2:
    st.dataframe(home_team_preview, hide_index=True)
    st.dataframe(home_team_projection, hide_index=True)

st.header('Starting Pitcher Preview')

away_pitcher = row['away_probable_pitcher'].iloc[0]
home_pitcher = row['home_probable_pitcher'].iloc[0]

away_pitcher_df = pitcher_boxscores[(pitcher_boxscores['Name'] == away_pitcher) & (pitcher_boxscores['isStarter']) & (pitcher_boxscores['seasonNumber'] == 2024)].sort_values(by='game_date', ascending=False)
home_pitcher_df = pitcher_boxscores[(pitcher_boxscores['Name'] == home_pitcher) & (pitcher_boxscores['isStarter']) & (pitcher_boxscores['seasonNumber'] == 2024)].sort_values(by='game_date', ascending=False)

st.write(f"{away_pitcher} : {away_pitcher_df['isWinner'].sum()}-{len(away_pitcher_df)-away_pitcher_df['isWinner'].sum()} @ {home_pitcher} : {home_pitcher_df['isWinner'].sum()}-{len(home_pitcher_df)-home_pitcher_df['isWinner'].sum()}")
st.write(f"{away_pitcher} on the Road Record: {away_pitcher_df[away_pitcher_df['away_name'] == away_pitcher_df['Team']]['isWinner'].sum()}-{len(away_pitcher_df[away_pitcher_df['away_name'] == away_pitcher_df['Team']])-away_pitcher_df[away_pitcher_df['away_name'] == away_pitcher_df['Team']]['isWinner'].sum()} @ {home_pitcher} at Home Record: {home_pitcher_df[home_pitcher_df['home_name'] == home_pitcher_df['Team']]['isWinner'].sum()}-{len(home_pitcher_df[home_pitcher_df['home_name'] == home_pitcher_df['Team']])-home_pitcher_df[home_pitcher_df['home_name'] == home_pitcher_df['Team']]['isWinner'].sum()}")

pitchFilter = st.checkbox(label="Filter DataFrames to Road/Home only?")



col1,col2 = st.columns(2)
with col1:
    st.dataframe
    if pitchFilter:
        st.dataframe(away_pitcher_df[away_pitcher_df['away_probable_pitcher'] == away_pitcher][['winning_team', 'winning_pitcher','Team', 'date', 'Name', 'Opponent', 'away_score', 'home_score']], hide_index=True)
    else:
        st.dataframe(away_pitcher_df[['winning_team', 'winning_pitcher','Team', 'date', 'Name', 'Opponent', 'away_score', 'home_score']], hide_index=True)

with col2:
    if pitchFilter:
        st.dataframe(home_pitcher_df[home_pitcher_df['home_probable_pitcher'] == home_pitcher][['winning_team', 'winning_pitcher','Team', 'date', 'Name', 'Opponent', 'away_score', 'home_score']], hide_index=True)

    else:
        st.dataframe(home_pitcher_df[['winning_team', 'winning_pitcher','Team', 'date', 'Name', 'Opponent', 'away_score', 'home_score']], hide_index=True)
