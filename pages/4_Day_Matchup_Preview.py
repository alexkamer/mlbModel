import pandas as pd
from datetime import datetime, timedelta
import concurrent.futures
import statsapi
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import streamlit as st
import requests

@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data
batter_boxscores = load_data('datasets/complex_batters.csv')
pitcher_boxscores = load_data('datasets/complex_pitchers.csv')
predicted_lineups = load_data('datasets/predicted_lineups.csv')

def findTeamKeys():
    mlbTeamKeys = []
    url = "https://statsapi.mlb.com/api/v1/teams/"
    response = requests.get(url)



    data = response.json()
    for team in data['teams']:
        #if team.get('sport', {}).get('name', '') == "Major League Baseball":
        mlbTeamKeys.append(
            {
            'Team' : team.get('name'),
            'team_id' : team.get('id'),
            'team_abbr' : team.get('abbreviation'),
            'league' : team.get('league',{}).get('name'),
            'division' : team.get('division',{}).get('name'),
            'sport' : team.get('sport', {}).get('name')
            }
        )
    return pd.DataFrame(mlbTeamKeys)

statsApiTeamKeys = findTeamKeys()
mlbTeamKeys = statsApiTeamKeys[statsApiTeamKeys['sport'] == 'Major League Baseball']

team_ids = mlbTeamKeys['team_id'].to_list()
daySlate = []
current_date = datetime.now()
#current_date = datetime.now() - timedelta(days=1)

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
daySlate.to_csv('datasets/daySlate.csv', index = False)

game_options = []
for idx, row in daySlate.iterrows():
    game_options.append(f"{row['away_name']} @ {row['home_name']}")

game_option = st.selectbox(
    label='Select a Game:',
    options = sorted(game_options)
    )
if game_option:
    row = daySlate[daySlate['away_name'] == game_option.split(" @ ")[0]]
    st.write(game_option)
    away_team = row['away_name'].iloc[0]
    home_team = row['home_name'].iloc[0]

away_lineup = predicted_lineups[str(row['away_id'].iloc[0])].to_list()
home_lineup = predicted_lineups[str(row['home_id'].iloc[0])].to_list()
st.table(row[['game_id', 'game_date', 'status', 'away_name', 'home_name', 'away_score', 'home_score', 'home_probable_pitcher', 'away_probable_pitcher']])

away_team_preview = []
home_team_preview = []

away_team_projection = []
home_team_projection = []

player = away_lineup[0]
for player in away_lineup:
    player_df = batter_boxscores[(batter_boxscores['Name'] == player) & (batter_boxscores['isStarter'])]
    #player_df = player_df[player_df['Team'] == player_df['away_name']]
    player_df = player_df.tail(10)
    away_team_preview.append({
        'Name' : player,
        'Batting Average' : round(player_df['avg'].mean(),3),
        'AtBats' : player_df['ab'].mean(),
        'Hits' : player_df['h'].mean(),
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

    away_team_projection.append({
        'Name' : player,
        'Projected Strikeouts' : round(player_df['team_strikeouts'].mean() * player_df['average_of_team_strikeouts'].mean(),2),
        'Projected Hits' : round(player_df['team_hits'].mean() * player_df['average_of_team_hits'].mean(),2),
        'Projected Walks' : round(player_df['team_walks'].mean() * player_df['average_of_team_walks'].mean(),2)  ,
        'Projected Runs' : round(player_df['team_runs'].mean() * player_df['average_of_team_runs'].mean(),2)      
    })



for player in home_lineup:
    player_df = batter_boxscores[(batter_boxscores['Name'] == player) & (batter_boxscores['isStarter'])]
    #player_df = player_df[player_df['Team'] == player_df['home_name']]

    player_df = player_df.tail(10)

    home_team_preview.append({
        'Name' : player,
        'Batting Average' : round(player_df['avg'].mean(),3),
        'AtBats' : player_df['ab'].mean(),
        'Hits' : player_df['h'].mean(),
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
    st.dataframe(away_team_preview)
    st.dataframe(away_team_projection)

with col2:
    st.dataframe(home_team_preview)
    st.dataframe(home_team_projection)

st.header('Starting Pitcher Preview')

away_pitcher = row['away_probable_pitcher'].iloc[0]
home_pitcher = row['home_probable_pitcher'].iloc[0]

away_pitcher_df = pitcher_boxscores[(pitcher_boxscores['Name'] == away_pitcher) & (pitcher_boxscores['isStarter']) & (pitcher_boxscores['seasonNumber'] == 2024)]
home_pitcher_df = pitcher_boxscores[(pitcher_boxscores['Name'] == home_pitcher) & (pitcher_boxscores['isStarter']) & (pitcher_boxscores['seasonNumber'] == 2024)]

st.write(f"{away_pitcher} : {away_pitcher_df['isWinner'].sum()}-{len(away_pitcher_df)-away_pitcher_df['isWinner'].sum()} @ {home_pitcher} : {home_pitcher_df['isWinner'].sum()}-{len(home_pitcher_df)-home_pitcher_df['isWinner'].sum()}")
st.write(f"{away_pitcher} on the Road Record: {away_pitcher_df[away_pitcher_df['away_name'] == away_pitcher_df['Team']]['isWinner'].sum()}-{len(away_pitcher_df[away_pitcher_df['away_name'] == away_pitcher_df['Team']])-away_pitcher_df[away_pitcher_df['away_name'] == away_pitcher_df['Team']]['isWinner'].sum()} @ {home_pitcher} at Home Record: {home_pitcher_df[home_pitcher_df['home_name'] == home_pitcher_df['Team']]['isWinner'].sum()}-{len(home_pitcher_df[home_pitcher_df['home_name'] == home_pitcher_df['Team']])-home_pitcher_df[home_pitcher_df['home_name'] == home_pitcher_df['Team']]['isWinner'].sum()}")
