import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import StringIO

pd.set_option('display.max_columns', 500)

@st.cache_data
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data

@st.cache_data
def load_props_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        data = response.content.decode('utf-8')
        data_io = StringIO(data)
        props_df = pd.read_csv(data_io)
        props_df = props_df.drop_duplicates(['prop_id'], keep='last')
        props_df = props_df[props_df['league'] == 'MLB']
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_day_props = props_df[props_df['start_time'] == current_date]
        batter_props = current_day_props[~current_day_props['position'].isin(['P', 'SP'])]
        batter_props = batter_props.sort_values(by=['player_name','stat_type','odds_type'])
        batter_props = batter_props.drop_duplicates()
        return batter_props
    else:
        st.error(f"Failed to retrieve data: status code {response.status_code}")
        return pd.DataFrame()

@st.cache_data
def create_organized_prop_df(_batter_boxscores, _batter_props, _actual_num_of_games):
    organized_prop_df = []
    for player_name in _batter_props['player_name'].unique():
        if player_name in _batter_boxscores['Name'].to_list():
            player_props = _batter_props[_batter_props['player_name'] == player_name]
            player_boxscore = _batter_boxscores[_batter_boxscores['Name'] == player_name][::-1]

            for index, row in player_props.iterrows():
                prop_dict = {
                    'Team': player_boxscore['Team'].iloc[0],
                    'game_date': row['start_time'],
                    'Name': row['player_name'],
                    'prop_line': row['prop_line'],
                    'odds_type': row['odds_type'],
                    'prop_type': row['stat_type'],
                    'PP_ID': row['PP_ID'],
                    'statsAPI_ID': player_boxscore['personId'].iloc[0],
                    'Hit Rate': 0,
                    'Push Rate': 0,
                    'Hit': 0,
                    'Push': 0,
                    'Game Size': 0
                }

                stat_list = player_boxscore[row['stat_type']].to_list()

                number_of_games = _actual_num_of_games

                if len(stat_list) < (number_of_games + 1):
                    number_of_games = len(stat_list)
                else:
                    stat_list = stat_list[:number_of_games]
                
                prop_dict['Game Size'] = number_of_games
                
                prop_dict['Hit'] = len([num for num in stat_list if num > row['prop_line']])
                prop_dict['Push'] = len([num for num in stat_list if num == row['prop_line']])
                prop_dict['Hit Rate'] = f"{round(prop_dict['Hit'] / prop_dict['Game Size'] * 100,2)}%"
                prop_dict['Push Rate'] = f"{round(prop_dict['Push'] / prop_dict['Game Size'] * 100,2)}%"

                for i in range(1, _actual_num_of_games+1):
                    try:
                        prop_dict[str(i)] = stat_list[i-1]
                    except:
                        prop_dict[str(i)] = None

                organized_prop_df.append(prop_dict)

    return pd.DataFrame(organized_prop_df)

# Load and preprocess data
batter_boxscores = load_data('datasets/complex_batters.csv')
batter_boxscores = batter_boxscores.rename(columns={
    'h' : 'Hits',
    'Batter Fantasy Score' : 'Hitter Fantasy Score',
    'k' : 'Hitter Strikeouts',
    'hr' : 'Home Runs',
    'rbi' : 'RBIs',
    'r' : 'Runs',
    'singles' : 'Singles',
    'TB' : 'Total Bases',
    'doubles' : 'Doubles',
    'H+R+RBIs' : 'Hits+Runs+RBIs',
    'bb': 'Walks',
    'sb' : 'Stolen Bases'
})

batter_props = load_props_data('http://192.168.1.200/data/all_prop_data.csv')

# Streamlit app
st.title('Batter Prize Picks Analysis')

actual_num_of_games = st.select_slider(
    'Select the number of games for the sample size',
    options=range(1,100),
    value=10
)

organized_prop_df = create_organized_prop_df(batter_boxscores, batter_props, actual_num_of_games)

player = st.selectbox(
    options=sorted(organized_prop_df['Name'].unique()),
    label='Select a Player:'
)

player_df = organized_prop_df[organized_prop_df['Name'] == player]

st.data_editor(player_df)
