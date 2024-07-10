import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import altair as alt

st.set_page_config(page_title="MLB Team Standings", layout="wide")
st.title('MLB Team Standings')

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

def style_dataframe(df):
    return df.style.set_properties(**{
        'background-color': 'lightgrey',
        'color': 'black',
        'border-color': 'white'
    }).set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#4CAF50'), ('color', 'white')]},
        {'selector': 'tr:nth-of-type(even)', 'props': [('background-color', '#f2f2f2')]},
    ]).format(precision=2)

# Allow users to select columns
all_columns = df.columns.tolist()
selected_columns = st.multiselect("Select columns to display", all_columns, default=["Team", "standingSummary", "total_wins", "total_losses", "total_winPercent"])

# Display the styled dataframe with selected columns
if selected_columns:
    styled_df = style_dataframe(df[selected_columns])
    st.dataframe(styled_df, use_container_width=True)
else:
    st.warning("Please select at least one column to display.")

# Add a download button for the full dataframe
csv = df.to_csv(index=False)
st.download_button(
    label="Download full data as CSV",
    data=csv,
    file_name="mlb_standings.csv",
    mime="text/csv",
)

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
