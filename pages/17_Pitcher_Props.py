import pandas as pd
from datetime import datetime, timedelta
import concurrent.futures
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
from streamlit import session_state as ss
@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data

pitchers_data = load_data('datasets/complex_pitchers.csv')
team_stats = load_data('datasets/team_stats.csv')
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


def get_opponents(daySlate, team):
    games = daySlate[(daySlate['away_name'] == team) | (daySlate['home_name'] == team)]
    
    if games.empty:
        return None, None
    else:
        for _, game in games.iterrows():
            if game['away_name'] == team:
                opponent = game['home_name']
                homeAway= '@'
            else:
                opponent = game['away_name']
                homeAway = 'vs.'
        return homeAway, opponent

def find_team_rank(df, team_name):
    """
    Returns the rank of the specified team in the sorted DataFrame.
    
    Parameters:
        df (pd.DataFrame): DataFrame sorted by the strikeouts column.
        team_name (str): The name of the team to find the rank for.
    
    Returns:
        int: The rank of the team, or None if the team is not found.
    """
    try:
        # Find the index of the row where the team_name matches
        df = df.reset_index()
        rank = df[df['Team'] == team_name].index[0] + 1  # Adding 1 to convert index to rank
        return rank
    except IndexError:
        # If the team is not found
        return None

def determine_result(row):
    if row[ss.prop_type_selection] > row['prop_line']:
        return 'Win'
    elif row[ss.prop_type_selection] < row['prop_line']:
        return 'Loss'
    else:
        return 'Push'


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
# prop_lines = prop_lines[(prop_lines['league'] == 'MLB') & (prop_lines['position'] == 'P') & (prop_lines['player_name'].isin(pitcher_names)) & (prop_lines['odds_type'] == 'standard')]
prop_lines = prop_lines[(prop_lines['league'] == 'MLB') & (prop_lines['position'] == 'P') & (prop_lines['player_name'].isin(pitcher_names))]


pitcher_names = sorted(prop_lines['player_name'].unique())

if 'pitcher_label_selection' not in st.session_state:
    st.session_state.pitcher_label_selection = pitcher_names[0]

def update_pitcher_label_selection():
    st.session_state.pitcher_label_selection = st.session_state.pitcher_label_selection_input

if 'odds_type_selection' not in ss:
    ss.odds_type_selection = 'standard'

def update_odds_type():
    ss.odds_type_selection = ss.odds_type_selection_input


if 'prop_type_selection' not in ss:
    ss.prop_type_selection = 'Pitcher Strikeouts'

def update_prop_type():
    ss.prop_type_selection = ss.prop_type_selection_input
    

with st.sidebar:
    #label_selection = st.selectbox(label='Select a Game:', options=game_list)
    st.selectbox(
        label='Select a Game:',
        options=sorted(pitcher_names),
        index=pitcher_names.index(st.session_state.pitcher_label_selection),
        key='pitcher_label_selection_input',
        on_change=update_pitcher_label_selection
    )


    pitcher_prop_df = prop_lines[(prop_lines['player_name'] == ss.pitcher_label_selection)].copy()
    pitcher_prop_df['start_time'] = pd.to_datetime(pitcher_prop_df['start_time'])

    max_date = pitcher_prop_df['start_time'].max()
    pitcher_prop_df = pitcher_prop_df[(pitcher_prop_df['start_time'] == max_date)]

    odds_types = sorted(pitcher_prop_df['odds_type'].unique())

    st.selectbox(
        label='Select the Odds type',
        options=odds_types,
        index=odds_types.index(ss.odds_type_selection),
        key='odds_type_selection_input',
        on_change=update_odds_type
    )




    pitcher_prop_df = pitcher_prop_df[pitcher_prop_df['odds_type'] == ss.odds_type_selection]
    st.dataframe(pitcher_prop_df)
    prop_list = sorted(pitcher_prop_df['stat_type'].unique())
    try:
        st.selectbox(
            label='Select the Prop type',
            options= [None] + prop_list,
            index=prop_list.index(ss.prop_type_selection),
            key='prop_type_selection_input',
            on_change=update_prop_type
        )
    except:
        st.selectbox(
            label='Select the Prop type',
            options= [None] + prop_list,
            key='prop_type_selection_input',
            on_change=update_prop_type
        )

    pitcher_prop_df = pitcher_prop_df[pitcher_prop_df['stat_type'] == ss.prop_type_selection]











pitcher_df = pitchers_data[(pitchers_data['Name'] == ss.pitcher_label_selection) & (pitchers_data['isStarter']) & (pitchers_data['seasonNumber'] == 2024)].copy()



cumulative_props = prop_lines[(prop_lines['player_name'] == ss.pitcher_label_selection) & (prop_lines['stat_type'] == ss.prop_type_selection) & (prop_lines['odds_type'] == ss.odds_type_selection)]

cumulative_props = cumulative_props.drop('Team', axis=1)
# Merge the two DataFrames on the date columns and player name
merged_df = pd.merge(
    pitcher_df, 
    cumulative_props, 
    left_on=['Name', 'date'], 
    right_on=['player_name', 'start_time']
)

merged_df['game_date'] = pd.to_datetime(merged_df['game_date'])

merged_df = merged_df.rename(columns={'k': 'Pitcher Strikeouts', 'er': 'Earned Runs Allowed', 'h': 'Hits Allowed', 'pitching_outs' : 'Pitching Outs'})



merged_df = merged_df.drop_duplicates('game_date', keep='first')
try:
    # Calculate dynamic figure size based on the number of data points
    num_dates = len(merged_df['game_date'])
    fig_width = max(8, num_dates * 1.2)  # Adjust the width as needed

    # Plotting the bar chart
    plt.figure(figsize=(fig_width, 6))
    bar_width = 2  # Adjusted bar width for better appearance

    # Plotting the bars for 'k' values
    # Adjusting the offset so the bars don't touch but are still separate
    k_bars = plt.bar(merged_df['game_date'] - pd.Timedelta(hours=25), merged_df[ss.prop_type_selection], width=bar_width, label=ss.prop_type_selection, color='blue')
    prop_line_bars = plt.bar(merged_df['game_date'] + pd.Timedelta(hours=25), merged_df['prop_line'], width=bar_width, label='prop_line', color='orange')
    # Adding labels and title
    plt.xlabel('Date')
    plt.ylabel('Strikeouts')
    plt.title(f'Comparison of Actual {ss.prop_type_selection} and Prop Line')

    # Rotate x-axis labels for better readability
    plt.xticks(merged_df['game_date'], rotation=45, ha='right')

    # Display values on top of the bars
    for bar in k_bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2), ha='center', va='bottom')

    for bar in prop_line_bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2), ha='center', va='bottom')

    # Use tight layout to minimize white space
    plt.tight_layout()

    plt.legend()

    # Display the chart in Streamlit
    st.pyplot(plt)
except:
    st.header("Bar Chart currently unavailable")

try:
    col1, col2,col3 = st.columns(3)
    with col1:
        simple_prop_df = merged_df[['game_date', str(ss.prop_type_selection), 'prop_line', 'Opponent']].copy()

        st.dataframe(pitcher_prop_df)


        homeAway, opponent = get_opponents(daySlate, pitcher_prop_df['Team'].iloc[0])
        team_stats = team_stats.sort_values(by=ss.prop_type_selection)

        rank = find_team_rank(team_stats, opponent)

        if 1 <= rank <= 10:
            rank_color = "red"
        elif 11 <= rank <= 20:
            rank_color = "yellow"
        elif 21 <= rank <= 30:
            rank_color = "green"
        else:
            rank_color = "black"  # Default color, though it should not be needed if rank is always within 1-30


        st.subheader(f"{ss.prop_type_selection} Hit Rate: {(simple_prop_df[ss.prop_type_selection] > simple_prop_df['prop_line']).sum()} / {len(simple_prop_df)} &ensp; Push Rate: {(simple_prop_df[ss.prop_type_selection] == simple_prop_df['prop_line']).sum()}")

        simple_prop_df['rank'] = simple_prop_df['Opponent'].apply(lambda team: find_team_rank(team_stats, team))
        simple_prop_df['Win/Loss'] = simple_prop_df.apply(determine_result, axis=1)

        st.dataframe(simple_prop_df.sort_values(by='game_date', ascending=False), hide_index=True)

    with col2:
        prop_line = pitcher_prop_df['prop_line'].iloc[0]
        st.markdown(f"""### Prop Line: {prop_line} {homeAway} {opponent} <span style="color:{rank_color};">({rank})</span>""", unsafe_allow_html=True)
        opponentLog = pitchers_data[(pitchers_data['Opponent'] == opponent) & (pitchers_data['isStarter']) & (pitchers_data['seasonNumber'] == 2024)].copy()
        opponentLog = opponentLog.drop_duplicates(subset='date', keep='last')
        opponentLog = opponentLog.sort_values(by='date', ascending=False)
        

        opponentPropLog = prop_lines.copy()
        opponentPropLog = opponentPropLog[(opponentPropLog['stat_type'] == ss.prop_type_selection) & (opponentPropLog['odds_type'] == ss.odds_type_selection)]
        opponentLog = opponentLog.drop('Team', axis=1)
        # Merge the two DataFrames on the date columns and player name
        merged_opponent_df = pd.merge(
            opponentLog, 
            opponentPropLog, 
            left_on=['Name', 'date'], 
            right_on=['player_name', 'start_time']
        )
        merged_opponent_df = merged_opponent_df.rename(columns={'k': 'Pitcher Strikeouts', 'er': 'Earned Runs Allowed', 'h': 'Hits Allowed', 'pitching_outs' : 'Pitching Outs'})
        merged_opponent_df['Win/Loss'] = merged_opponent_df.apply(determine_result, axis=1)
        merged_opponent_df = merged_opponent_df.drop_duplicates(subset='date', keep='last')

        st.dataframe(merged_opponent_df[['date','Name',ss.prop_type_selection, 'prop_line', 'Win/Loss']], hide_index=True)
    with col3:

        pitcher_df = pitcher_df.rename(columns={'k': 'Pitcher Strikeouts', 'er': 'Earned Runs Allowed', 'h': 'Hits Allowed', 'pitching_outs' : 'Pitching Outs'})

        simple_pitcher_df = pitcher_df[[ss.prop_type_selection, 'date', 'Opponent','Team']]

        st.subheader(f"During this Season: {(pitcher_df[ss.prop_type_selection] >= prop_line).sum()} / {len(pitcher_df)}")
        st.write(f"During this Season at home: {(pitcher_df[pitcher_df['Team'] == pitcher_df['home_name']][ss.prop_type_selection] > prop_line).sum()} / {len(pitcher_df[pitcher_df['Team'] == pitcher_df['home_name']])}")
        st.write(f"During this Season on road: {(pitcher_df[pitcher_df['Team'] == pitcher_df['away_name']][ss.prop_type_selection] > prop_line).sum()} / {len(pitcher_df[pitcher_df['Team'] == pitcher_df['away_name']])}")
        st.subheader(f"L5 Games: {(pitcher_df.tail(5)[ss.prop_type_selection] > prop_line).sum()} / {len(pitcher_df.tail(5))}")


        st.dataframe(simple_pitcher_df.sort_values(by='date',ascending=False), hide_index=True)

        




except:
    st.header('Prop Type Unavailable')