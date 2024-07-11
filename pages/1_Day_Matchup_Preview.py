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

col1, col2 = st.columns(2)

st.header('Head to Head Matchups')
currentHomeAway = st.checkbox('With current home/away?')

if currentHomeAway:
    head_to_head = basic_gamelogs[(basic_gamelogs['away_id'] == away_id) & (basic_gamelogs['home_id'] == home_id)].sort_values(by='game_datetime')
else:
    head_to_head = basic_gamelogs[((basic_gamelogs['away_id'] == away_id) & (basic_gamelogs['home_id'] == home_id) | (basic_gamelogs['away_id'] == home_id) & (basic_gamelogs['home_id'] == away_id))].sort_values(by='game_datetime')

head_to_head_num_games = st.select_slider(options=range(1,len(head_to_head) + 1), label='Select the number of games: ')

head_to_head = head_to_head[::-1]
display_head_to_head = head_to_head[['game_date', 'away_name', 'home_name', 'home_probable_pitcher', 'away_probable_pitcher', 'away_score', 'home_score', 'venue_name', 'winning_team']].copy()
display_head_to_head = display_head_to_head.head(head_to_head_num_games)

# Calculate statistics
average_runs = round((display_head_to_head['away_score'].sum() + display_head_to_head['home_score'].sum()) / head_to_head_num_games, 2)
away_wins = len(display_head_to_head[display_head_to_head['winning_team'] == away_team])
home_wins = len(display_head_to_head[display_head_to_head['winning_team'] == home_team])

# Display summary statistics
st.subheader("Summary Statistics")
col1, col2, col3 = st.columns(3)
col1.metric("***Average Runs per Game***", average_runs)
col2.metric(f"***{away_team} Wins***", away_wins)
col3.metric(f"***{home_team} Wins***", home_wins)

# Prepare and display the head-to-head dataframe
display_head_to_head['Score'] = display_head_to_head.apply(lambda row: f"{row['away_score']} - {row['home_score']}", axis=1)
display_head_to_head['Winner'] = display_head_to_head.apply(lambda row: row['away_name'] if row['winning_team'] == row['away_name'] else row['home_name'], axis=1)
display_head_to_head['Run Total'] = display_head_to_head['away_score'] + display_head_to_head['home_score']
display_head_to_head['Run Diff'] = abs(display_head_to_head['home_score'] - display_head_to_head['away_score'])

st.subheader("Head-to-Head Results")

html_table = """
<table style="width:100%; border-collapse: collapse;">
    <tr style="background-color: #f2f2f2;">
        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Date</th>
        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Away Team</th>
        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Home Team</th>
        <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Score</th>
        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Winner</th>
        <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Total Runs</th>
        <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Run Difference</th>
        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Venue</th>
    </tr>
"""

for _, row in display_head_to_head.iterrows():
    winner_color = "#90EE90" if row['Winner'] == row['away_name'] else "#ADD8E6"
    html_table += f"""
    <tr>
        <td style="padding: 12px; text-align: left; border: 1px solid #ddd;">{row['game_date'].strftime('%b %d, %Y')}</td>
        <td style="padding: 12px; text-align: left; border: 1px solid #ddd;">{row['away_name']}</td>
        <td style="padding: 12px; text-align: left; border: 1px solid #ddd;">{row['home_name']}</td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">{row['Score']}</td>
        <td style="padding: 12px; text-align: left; border: 1px solid #ddd; background-color: {winner_color};">{row['Winner']}</td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">{row['Run Total']}</td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">{row['Run Diff']}</td>
        <td style="padding: 12px; text-align: left; border: 1px solid #ddd;">{row['venue_name']}</td>
    </tr>
    """

html_table += "</table>"

st.markdown(html_table, unsafe_allow_html=True)

st.divider()



away_team_games = pitcher_boxscores[(pitcher_boxscores['isStarter']) & (pitcher_boxscores['Team'] == away_team)][::-1]
home_team_games = pitcher_boxscores[(pitcher_boxscores['isStarter']) & (pitcher_boxscores['Team'] == home_team)][::-1]



numGames = 5

col1, col2 = st.columns(2)

with col1:
    st.header(f"Team's Records in last {numGames} games:")
with col2:
    numGames = st.slider(label='Select the number of games: ', min_value=1, max_value=20, value=5, step=1)


away_team_l5 = []
home_team_l5 = []

away_wins = 0
home_wins = 0
# Edit code here

def create_game_summary(r, mlb_team_logo_df):
    winner = 'W' if r['isWinner'] else 'L'
    homeAway = '@' if r['Team'] == r['away_name'] else 'vs.'
    opposingPitcher = r['home_probable_pitcher'] if r['Team'] == r['away_name'] else r['away_probable_pitcher']
    my_dict = {
        "resultString" : f"{winner} {r['away_score']}-{r['home_score']} {homeAway} {r['Opponent']}", 
        'opponent_logo' :mlb_team_logo_df[mlb_team_logo_df['Team'] == r['Opponent']]['Logos'].iloc[0]
        }

    return my_dict
away_team_l5 = [create_game_summary(r, mlb_team_logo_df) for _, r in away_team_games[:numGames].iterrows()]
home_team_l5 = [create_game_summary(r, mlb_team_logo_df) for _, r in home_team_games[:numGames].iterrows()]

away_wins = sum(1 for game in away_team_l5 if game['resultString'].startswith('W'))
home_wins = sum(1 for game in home_team_l5 if game['resultString'].startswith('W'))

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <h4><img src="{away_logo}" style="width: 10%; height: 10%;"> <b>{away_team} {away_wins}-{numGames - away_wins}</b></h4>
    """, unsafe_allow_html=True)


    for game in away_team_l5:
        st.markdown(f"""
        <p>- {game['resultString']} <img src="{game['opponent_logo']}" style="width: 5%; height: 5%;"> </p>
        """, unsafe_allow_html=True)



with col2:
    st.markdown(f"""
    <h4><img src="{home_logo}" style="width: 10%; height: 10%;"> <b>{home_team} {home_wins}-{numGames - home_wins}</b></h4>
    """, unsafe_allow_html=True)


    for game in home_team_l5:
        st.markdown(f"""
        <p>- {game['resultString']} <img src="{game['opponent_logo']}" style="width: 5%; height: 5%;"> </p>
        """, unsafe_allow_html=True)

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
    if pitchFilter:
        st.dataframe(away_pitcher_df[away_pitcher_df['away_probable_pitcher'] == away_pitcher][['winning_team', 'winning_pitcher','Team', 'date', 'Name', 'Opponent', 'away_score', 'home_score']], hide_index=True)
    else:
        st.dataframe(away_pitcher_df[['winning_team', 'winning_pitcher','Team', 'date', 'Name', 'Opponent', 'away_score', 'home_score']], hide_index=True)

with col2:
    if pitchFilter:
        st.dataframe(home_pitcher_df[home_pitcher_df['home_probable_pitcher'] == home_pitcher][['winning_team', 'winning_pitcher','Team', 'date', 'Name', 'Opponent', 'away_score', 'home_score']], hide_index=True)

    else:
        st.dataframe(home_pitcher_df[['winning_team', 'winning_pitcher','Team', 'date', 'Name', 'Opponent', 'away_score', 'home_score']], hide_index=True)
