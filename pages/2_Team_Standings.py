import streamlit as st
st.title('MLB Team Standings')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import altair as alt


@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data

df = load_data('datasets/record_df.csv')

def format_percent(df):
    for col in df.columns:
        if 'Percent' in col:
            df[col] = df[col].apply(lambda x: "{:.2%}".format(x))
    return df




standings_filter = st.selectbox(
    options=['Both', 'Home', 'Away'],
    label='Select the type of standings you would like to see'
)

columns_to_include = ['Team', 'Abbreviation', 'espn_team_id', 'standingSummary']
stat_cols = ['OTLosses', 'OTWins', 'avgPointsAgainst', 'avgPointsFor', 'differential', 'divisionWinPercent', 'gamesBehind', 'gamesPlayed', 'leagueWinPercent','losses', 'playoffSeed', 'pointDifferential','points','pointsAgainst', 'pointsFor', 'streak', 'winPercent', 'wins', 'divisionGamesBehind', 'divisionPercent', 'magicNumberDivision', 'magicNumberWildcard','playoffPercent', 'wildCardPercent']

if standings_filter == 'Home':
    extension = 'home_'
    columns_to_include.extend([f"{extension}{x}" for x in stat_cols])
    standing_df = df[columns_to_include]

elif standings_filter == 'Away':
    extension = 'road_'
    columns_to_include.extend([f"{extension}{x}" for x in stat_cols])
    standing_df = df[columns_to_include]

elif standings_filter == 'Both':
    extension = 'total_'
    columns_to_include.extend([f"{extension}{x}" for x in stat_cols])
    standing_df = df[columns_to_include]
    

standing_df['Division'] = standing_df['standingSummary'].str.split(' in ', expand=True)[1]
standing_df['Spot in Division'] = standing_df['standingSummary'].str.split(' in ', expand=True)[0]

standing_df['Record'] = standing_df.apply(lambda row: f"{int(row[f'{extension}wins'])}-{int(row[f'{extension}losses'])}", axis=1)
standing_df['OT Record'] = standing_df.apply(lambda row: f"{int(row[f'{extension}OTWins'])}-{int(row[f'{extension}OTLosses'])}", axis=1)



standing_df = standing_df.sort_values(by=['Division', 'Spot in Division'])



# Tab names and their corresponding filters
tabs_filters = {
    "Overall": None,
    "AL": "AL",
    "NL": "NL",
    'AL East': 'AL East',
    'AL West': 'AL West',
    'AL Central': 'AL Cent',
    'NL West': 'NL West',
    'NL East': 'NL East',
    'NL Central': 'NL Cent'
}

# Create tabs
tabs = st.tabs(list(tabs_filters.keys()))

# Display DataFrames in each tab
for tab, filter_str in zip(tabs, tabs_filters.values()):
    with tab:
        if filter_str is None:
            display_df = standing_df.copy()  # For 'Overall' tab, display all data
        else:
            display_df = standing_df[standing_df['Division'].str.contains(filter_str, case=False, na=False)].copy()

        display_df = display_df[['Team', 'standingSummary','Record', 'OT Record']]
        st.dataframe(display_df, hide_index=True)
