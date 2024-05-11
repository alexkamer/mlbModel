import streamlit as st
st.title('Pitcher Prop Comparison')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import altair as alt

st.markdown("![Alt Text](https://static.prizepicks.com/images/players/mlb/Yordan_Alvarez_fdc9c3af-4ad2-43b1-8537-10732d013ed8.webp)")

st.image("https://static.prizepicks.com/images/players/mlb/Yordan_Alvarez_fdc9c3af-4ad2-43b1-8537-10732d013ed8.webp")

daySlate = pd.read_csv('datasets/daySlate.csv')


expected_pitchers = daySlate['home_probable_pitcher'].to_list() + daySlate['away_probable_pitcher'].to_list()
expected_pitchers = [x for x in expected_pitchers if type(x) == str]


df = pd.read_csv('datasets/complex_pitchers.csv')


mlb_teams = ['Any'] + sorted(list(set(df['Team'])))


col1, col2 = st.columns(2)

with col1:
    pitcher_name = st.selectbox(
        label='Select a Pitcher:',
        options = sorted(expected_pitchers)
    )
    prop_type = st.selectbox(
        label='Select a Prop:',
        options = sorted(['Team Won Game', 'Pitcher Recorded Win','Innings Pitched', 'Hits Allowed', 'Runs Allowed', 'Earned Runs', 'Walks', 'Strikeouts', 'Homeruns Allowed', 'Pitches Thrown', 'Pitching Outs'])
    )
    opponent_name = st.selectbox(
        label='Select an Opponent:',
        options = mlb_teams
        )

    stat_correl = st.multiselect(
        'Which stats would you like to include on the chart?',
        sorted(['Team Won Game', 'Pitcher Recorded Win','Innings Pitched', 'Hits Allowed', 'Runs Allowed', 'Earned Runs', 'Walks', 'Strikeouts', 'Homeruns Allowed', 'Pitches Thrown', 'Pitching Outs'])
    )
pitcher_df = df[(df['Name'] == pitcher_name) & (df['isStarter'])]


with col2:
    home_or_away = st.selectbox(
        label='Home or Away?',
        options = ['Both', 'Away', 'Home']
    )
    prop_line = st.number_input(label='Enter the Prop Line:', step=0.5, value=0.0, min_value=0.0)

    is_team_winner = st.selectbox(
        label='Did Team Win Game',
        options=[None,'Yes', 'No']
    )

if home_or_away == 'Home':
    pitcher_df = pitcher_df[pitcher_df['Team'] == pitcher_df['home_name']]
elif home_or_away == 'Away':
    pitcher_df = pitcher_df[pitcher_df['Team'] == pitcher_df['away_name']]

if opponent_name != 'Any':
    pitcher_df = pitcher_df[pitcher_df['Opponent'] == opponent_name]

if is_team_winner == 'Yes':
    pitcher_df = pitcher_df[pitcher_df['isWinner']]
elif is_team_winner == 'No':
    pitcher_df = pitcher_df[pitcher_df['isWinner'] == False]

number_of_games = st.select_slider(
    'Select the number of games for the sample size',
    options=range(1,len(pitcher_df) + 1))
pitcher_df = pitcher_df.tail(number_of_games)
st.write(f'You selected: {pitcher_name}' )

pitcher_df = pitcher_df.rename(columns={
    'isWinner' : 'Team Won Game',
    'pitcherIsWinner' : 'Pitcher Recorded Win',
    'ip' : 'Innings Pitched',
    'h' : 'Hits Allowed',
    'r' : 'Runs Allowed',
    'er' : 'Earned Runs',
    'bb' : 'Walks',
    'k' : 'Strikeouts',
    'hr' : 'Homeruns Allowed',
    'p' : 'Pitches Thrown',
    's' : 'Strikes Thrown',
    'pitching_outs' : 'Pitching Outs'
})
pitcher_df = pitcher_df.drop(['namefield', 'name', 'note', 'game_datetime', 'game_type', 'status','home_pitcher_note', 'away_pitcher_note','current_inning','inning_state','venue_id', 'venue_name', 'national_broadcasts','summary','losing_Team'], axis=1)

pitcher_df = pitcher_df.sort_values(by='date')
st.write(pitcher_df['pitch_count_MA3'].iloc[0])

chart_data = pitcher_df
chart_data = chart_data.sort_values('date', ascending=False)
chart_data['Label'] = chart_data['date'] + "\n" + chart_data['Opponent']

if prop_line and prop_type:

    fig, ax = plt.subplots()
    fig.patch.set_facecolor('#2d2d2d')  # Set the outer background color
    ax.set_facecolor('#2d2d2d')
    ax.yaxis.grid(True, color='gray', linestyle='-', linewidth=0.5) 

    categories = chart_data["Label"].to_list()
    values = chart_data[prop_type].to_list()

    for i,val in enumerate(values):
        if val > prop_line:
            color = 'green'
        elif val < prop_line:
            color = 'red'
        else:
            color = 'gray'
        ax.bar(categories[i], val, color=color)

        fontsize = 15
        plt.xticks(rotation=45, fontsize=min(fontsize,90/len(values)), color='white')
        plt.yticks(color='white')
        plt.tight_layout()

        ax.text(i,val +0.5, f'{val}', ha='center', va='bottom', color='white')        
    ax.axhline(y=prop_line, color='black', linestyle='--')

    ax.set_xlabel('Date and Opponent', color='white')
    st.pyplot(fig)


# st.bar_chart(
#     chart_data, x='Label', y=stat_correl
# )

chart_data