import streamlit as st
st.title('Pitcher Per Inning Prize Picks Analysis')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import altair as alt
import requests
from io import StringIO
import re

import streamlit_shadcn_ui as ui




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
pitcher_boxscores = pitcher_boxscores[pitcher_boxscores['isStarter']]

k_per_inning = load_data('datasets/k_per_inning.csv')
h_per_inning = load_data('datasets/h_per_inning.csv')
pitches_per_inning = load_data('datasets/pitches_per_inning.csv')




k_per_inning = k_per_inning.drop_duplicates(subset=['game_id', 'Name'], keep='last')
h_per_inning = h_per_inning.drop_duplicates(subset=['game_id', 'Name'], keep='last')
pitches_per_inning = pitches_per_inning.drop_duplicates(subset=['game_id', 'Name'], keep='last')


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
    props_df = pd.read_csv(data_io)

props_df = props_df.drop_duplicates(['prop_id'], keep='last')
props_df = props_df[props_df['league'] == 'MLBLIVE']

current_date = datetime.now().strftime('%Y-%m-%d')

current_day_props = props_df[props_df['start_time'] == current_date]


col1,col2 = st.columns(2)
with col1:
    player = st.selectbox(
        options=sorted(current_day_props['player_name'].unique()),
        label='Select a Player:'
    )

    homeAway = st.selectbox(
        options=['Both', 'Home', 'Away'],
        label='Select if Home or Away:'
    )
with col2:
    prop_type = st.selectbox(
        options=sorted(current_day_props[current_day_props['player_name'] == player]['stat_type'].unique()),
        label='Select a prop type:'
    )

if player:
    pitcher_k_per_inning = k_per_inning[k_per_inning['Name'] == player]
    pitcher_h_per_inning = h_per_inning[h_per_inning['Name'] == player]
    pitcher_pitches_per_inning = pitches_per_inning[pitches_per_inning['Name'] == player]

    pitcher_df = pitcher_boxscores[pitcher_boxscores['Name'] == player]
    pitcher_df = pitcher_df[::-1]

if prop_type:
    prop_line = current_day_props[(current_day_props['player_name'] == player) & (current_day_props['stat_type'] == prop_type)]['prop_line'].iloc[0]
    innings_included = [str(num) for num in re.findall(r'\d+', current_day_props[(current_day_props['player_name'] == player) & (current_day_props['stat_type'] == prop_type)]['description'].iloc[0])]

if homeAway == 'Home':
    pitcher_df = pitcher_df[pitcher_df['Team'] == pitcher_df['home_name']]
elif homeAway == 'Away':
    pitcher_df = pitcher_df[pitcher_df['Team'] == pitcher_df['away_name']]





number_of_games = st.select_slider(
    'Select the number of games for the sample size',
    options=range(1,len(pitcher_k_per_inning) + 1))



#st.table(current_day_props[(current_day_props['player_name'] == player) & (current_day_props['stat_type'] == prop_type)])

st.write(f"{current_day_props[(current_day_props['player_name'] == player) & (current_day_props['stat_type'] == prop_type)]['prop_line'].iloc[0]} {current_day_props[(current_day_props['player_name'] == player) & (current_day_props['stat_type'] == prop_type)]['description'].iloc[0]}")

pitcher_df = pitcher_df.head(number_of_games)
game_id_list = pitcher_df['game_id'].to_list()

pitcher_k_per_inning = pitcher_k_per_inning[pitcher_k_per_inning['game_id'].isin(game_id_list)]
pitcher_h_per_inning = pitcher_h_per_inning[pitcher_h_per_inning['game_id'].isin(game_id_list)]
pitcher_pitches_per_inning = pitcher_pitches_per_inning[pitcher_pitches_per_inning['game_id'].isin(game_id_list)]

chart_data = pd.merge(pitcher_df,pitcher_k_per_inning, on='game_id', how='left')
chart_data = pitcher_df.copy()
chart_data['Label'] = chart_data['date'] + "\n" + chart_data['Opponent']


if prop_type == 'Pitcher Strikeouts':
    if len(innings_included) > 0:
        pitcher_k_per_inning['Sum'] = sum([pitcher_k_per_inning[str(inning)] for inning in innings_included])

    stat_list = pitcher_k_per_inning['Sum'].to_list()

elif prop_type == 'Hits Allowed':
    if len(innings_included) > 0:
        pitcher_h_per_inning['Sum'] = sum([pitcher_h_per_inning[str(inning)] for inning in innings_included])
    stat_list = pitcher_h_per_inning['Sum'].to_list()

elif prop_type == 'Pitches Thrown':
    if len(innings_included) > 0:
        pitcher_pitches_per_inning['Sum'] = sum([pitcher_pitches_per_inning[str(inning)] for inning in innings_included])
    stat_list = pitcher_pitches_per_inning['Sum'].to_list()

if prop_type:

    fig, ax = plt.subplots()
    fig.patch.set_facecolor('#2d2d2d')  # Set the outer background color
    ax.set_facecolor('#2d2d2d')
    ax.yaxis.grid(True, color='gray', linestyle='-', linewidth=0.5) 

    categories = chart_data["Label"].to_list()
    values = stat_list
    hit_rate = {"Win": 0, "Loss" : 0, "Push" : 0}
    for i,val in enumerate(values):
        if val > prop_line:
            color = 'green'
            hit_rate['Win'] += 1
        elif val < prop_line:
            color = 'red'
            hit_rate['Loss'] += 1
        else:
            color = 'gray'
            hit_rate['Push'] += 1
        ax.bar(categories[i], val, color=color)

        fontsize = 15
        plt.xticks(rotation=45, fontsize=min(fontsize,90/len(values)), color='white')
        plt.yticks(color='white')
        plt.tight_layout()

        ax.text(i,val +0.5, f'{val}', ha='center', va='bottom', color='white')        
    ax.axhline(y=prop_line, color='black', linestyle='--')

    ax.set_xlabel('Date and Opponent', color='white')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"Wins: {hit_rate['Win']}")
        st.write(f"Implied Win Probability: {round(hit_rate['Win']/(hit_rate['Win'] + hit_rate['Loss'] + hit_rate['Push']) * 100,2)}%")
        st.write(f"Implied Odds {implied_probability_to_american_odds(hit_rate['Win']/(hit_rate['Win'] + hit_rate['Loss'] + hit_rate['Push']))}")
    with col2:
        st.write(f"Losses: {hit_rate['Loss']}")
        st.write(f"Implied Loss Probability: {round(hit_rate['Loss']/(hit_rate['Win'] + hit_rate['Loss'] + hit_rate['Push']) * 100,2)}%")
        st.write(f"Implied Odds {implied_probability_to_american_odds(hit_rate['Loss']/(hit_rate['Win'] + hit_rate['Loss'] + hit_rate['Push']))}")

    with col3:
        st.write(f"Pushes: {hit_rate['Push']}")
        st.write(f"Implied Loss Probability: {round(hit_rate['Push']/(hit_rate['Win'] + hit_rate['Loss'] + hit_rate['Push']) * 100,2)}%")
        if hit_rate['Push'] > 0:
            st.write(f"Implied Odds {implied_probability_to_american_odds(hit_rate['Push']/(hit_rate['Win'] + hit_rate['Loss'] + hit_rate['Push']))}")

    st.pyplot(fig)








ui.avatar(current_day_props[(current_day_props['player_name'] == player) & (current_day_props['stat_type'] == prop_type)]['image_url'].iloc[0])
st.table(current_day_props[(current_day_props['player_name'] == player) & (current_day_props['stat_type'] == prop_type)])
st.table(pitcher_pitches_per_inning)