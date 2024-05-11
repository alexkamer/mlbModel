import streamlit as st
st.title('Batter Prop Comparison')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import altair as alt

@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data

df = load_data('datasets/complex_batters.csv')
predicted_lineups= load_data('datasets/predicted_lineups.csv')

def implied_probability_to_american_odds(implied_prob):
    if implied_prob < 0.5:
        return f"+{int((100 / implied_prob) - 100)}"
    elif implied_prob == 0:
        return 0
    else:
        return f"-{int((100 / implied_prob))}"


teams = df['Team'].unique()
starting_pitchers = df['Opposing_Pitcher'].unique()

team_name = st.selectbox(
    label='Select a Team:',
    options = sorted(teams)
    )
if team_name:
    team_id = df[df['Team'] == team_name]['team_id'].iloc[0]





predicted_lineup = predicted_lineups[str(team_id)].to_list()

player_name = st.selectbox(
    label='Select a Player:',
    options = sorted(predicted_lineup)
    )

batter_df = df[df['Name'] == player_name]
batter_df = batter_df[batter_df['isStarter']]

batter_df = batter_df.drop(['namefield', 'name', 'note', 'game_datetime', 'game_date', 'away_id', 'home_id', 'game_type', 'status','home_pitcher_note', 'away_pitcher_note','current_inning','inning_state','venue_id', 'venue_name', 'national_broadcasts','summary','losing_Team'], axis=1)


batter_df = batter_df.rename(columns={
    'isWinner' : 'Team Won Game',
    'h' : 'Hits',
    'r' : 'Runs',
    'bb' : 'Walks',
    'k' : 'Strikeouts',
    'hr' : 'Homeruns',
    'sb' : 'Stolen Bases',
    'ab' : 'At Bats',
    'doubles' : 'Doubles',
    'triples' : 'Triples',
    'rbi' : 'Runs Batted In'
})


col1, col2 = st.columns(2)
with col1:
    prop_name = st.selectbox(
        label = 'Select a Prop:',
        options=sorted(['At Bats', 'Runs', 'Hits', 'Doubles', 'Triples', 'Homeruns', 'Runs Batted In', 'Stolen Bases', 'Walks', 'Strikeouts'])
    )

    home_or_away = st.selectbox(
        label='Home/Away:',
        options=['Both','Away','Home']
    )

    vs_team = st.selectbox(
        label='Vs. Specific Team',
        options=['Any'] + sorted(teams)
    )

    specific_season = st.selectbox(
        label='Select A Season',
        options= ['Any'] + sorted(batter_df['seasonNumber'].unique())[::-1]
    )


with col2:
    prop_value = st.number_input(label='Enter the Prop Line:', step=0.5, value=0.0, min_value=0.0)

    isWin = st.selectbox(
        label='Did Team Win:',
        options=['Neither', 'Yes', 'No']
    )
    vs_pitcher = st.selectbox(
        label='Vs. Specific Pitcher:',
        options= ['Any'] + sorted([str(x) for x in starting_pitchers])
    )



if home_or_away == 'Home':
    batter_df = batter_df[batter_df['Team'] == batter_df['home_name']]
elif home_or_away == 'Away':
    batter_df = batter_df[batter_df['Team'] == batter_df['away_name']]

if isWin == 'Yes':
    batter_df = batter_df[batter_df['Team'] == batter_df['winning_team']]
elif isWin == 'No':
    batter_df = batter_df[batter_df['Team'] == batter_df['losing_team']]


if vs_pitcher != 'Any':
    if vs_pitcher in batter_df['Opposing_Pitcher'].to_list():
        batter_df = batter_df[batter_df['Opposing_Pitcher'] == vs_pitcher]
        st.write(vs_pitcher)
    else:
        st.write("No Matchup vs", vs_pitcher)

if specific_season != 'Any':
    batter_df = batter_df[batter_df['seasonNumber'] == specific_season]

number_of_games = st.select_slider(
    'Select the number of games for the sample size',
    options=range(1,len(batter_df) + 1),
    value=len(batter_df)/2
    )

batter_df = batter_df.tail(number_of_games)

chart_data = batter_df
chart_data = chart_data.sort_values('date', ascending=False)
chart_data['Label'] = chart_data['date'] + "\n" + chart_data['Opponent']

if prop_name and prop_value:

    fig, ax = plt.subplots()
    fig.patch.set_facecolor('#2d2d2d')  # Set the outer background color
    ax.set_facecolor('#2d2d2d')
    ax.yaxis.grid(True, color='gray', linestyle='-', linewidth=0.5) 

    categories = chart_data["Label"].to_list()
    values = chart_data[prop_name].to_list()
    hit_rate = {"Win": 0, "Loss" : 0, "Push" : 0}
    for i,val in enumerate(values):
        if val > prop_value:
            color = 'green'
            hit_rate['Win'] += 1
        elif val < prop_value:
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
    ax.axhline(y=prop_value, color='black', linestyle='--')

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


st.table(batter_df)


