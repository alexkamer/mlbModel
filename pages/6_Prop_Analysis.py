import streamlit as st
st.title('Prize Picks Analysis')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import altair as alt


@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data

prop_lines = load_data('prize_picks_lines.csv')
pitcher_df = load_data('datasets/complex_pitchers.csv')
batter_df = load_data('datasets/complex_batters.csv')
prop_lines = prop_lines.drop_duplicates()


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

most_recent_date = sorted(prop_lines['game_date'].to_list())[-1]
single_day_props = prop_lines[prop_lines['game_date'] == most_recent_date]


col1, col2 = st.columns(2)

with col1:
    position_type = st.selectbox(
        label = "Hitter or Pitcher:",
        options=["Hitters", "Pitchers"]
    )

    if position_type == 'Pitchers':
        simple_props = single_day_props[single_day_props['position'] == 'P']

    else:
        simple_props = single_day_props[single_day_props['position'] != 'P']


    player_names = simple_props['Name'].unique()
    player_name = st.selectbox(
        label='Select a Player:',
        options=sorted(player_names)
        )


player_df = simple_props[simple_props['Name'] == player_name]

prop_types = player_df['prop_type'].unique()

with col2:
    prop_type = st.selectbox(
        label='Select a Prop',
        options=sorted(prop_types)
    )

    player_df = player_df[player_df['prop_type'] == prop_type]

    odds_type = st.selectbox(
        label='Select the Odds Type',
        options=sorted(player_df['odds_type'].unique())
    )

    player_df = player_df[player_df['odds_type'] == odds_type]

    prop_value = player_df['prop_line'].iloc[0]

if position_type == 'Pitchers':
    player_stats_df = pitcher_df[pitcher_df['Name'] == player_name][::-1]
else:
    player_stats_df = batter_df[batter_df['Name'] == player_name][::-1]

number_of_games = st.select_slider(
        'Select the number of games for the sample size',
        options=range(1,len(player_stats_df) + 1))
player_stats_df = player_stats_df.head(number_of_games)

if prop_type == 'Pitcher Strikeouts':
    stat_list = player_stats_df['k'].to_list()
elif prop_type == 'Pitching Outs':
    stat_list = player_stats_df['pitching_outs'].to_list()    
elif prop_type == 'Walks Allowed':
    stat_list = player_stats_df['bb'].to_list()
elif prop_type == 'Hits Allowed' or prop_type == 'Hits':
    stat_list = player_stats_df['h'].to_list()
#elif prop_type == 'Home Runs':



with st.sidebar:
    st.image(player_df['image_url'].iloc[0])


chart_data = player_stats_df.copy()
chart_data = chart_data.sort_values('date', ascending=False)
chart_data['Label'] = chart_data['date'] + "\n" + chart_data['Opponent']


if prop_type:

    fig, ax = plt.subplots()
    fig.patch.set_facecolor('#2d2d2d')  # Set the outer background color
    ax.set_facecolor('#2d2d2d')
    ax.yaxis.grid(True, color='gray', linestyle='-', linewidth=0.5) 

    categories = chart_data["Label"].to_list()
    values = stat_list
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




#player_df = player_df.drop_duplicates()
st.table(player_df)
st.table(player_stats_df)