import streamlit as st
import pandas as pd
import base64
from PIL import Image
import io

# Custom CSS
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size:1.5rem;
    }
    .dataframe {
        font-size: 12px;
    }
    .dataframe td, .dataframe th {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header image
header_image_url = "https://upload.wikimedia.org/wikipedia/en/thumb/a/a6/Major_League_Baseball_logo.svg/1200px-Major_League_Baseball_logo.svg.png"
st.image(header_image_url, width=300)

st.title('MLB Team Standings')


@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data

df = load_data('datasets/record_df.csv')

@st.cache_resource
def get_team_logo(team_name):
    # This function should return the URL of the team logo
    # You'll need to create a dictionary mapping team names to logo URLs
    team_logos = {
        "New York Yankees": "https://example.com/yankees_logo.png",
        "Boston Red Sox": "https://example.com/redsox_logo.png",
        # Add more teams here
    }
    return team_logos.get(team_name, "https://example.com/default_logo.png")

def add_logo(team_name):
    logo_url = get_team_logo(team_name)
    return f'<img src="{logo_url}" width="30">&nbsp;{team_name}'

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
        display_df['Team'] = display_df['Team'].apply(add_logo)
        
        # Function to color code win-loss record
        def color_record(val):
            wins, losses = map(int, val.split('-'))
            if wins > losses:
                return 'color: green'
            elif wins < losses:
                return 'color: red'
            else:
                return 'color: black'

        # Apply styling
        styled_df = display_df.style.applymap(color_record, subset=['Record'])
        
        # Display styled dataframe
        st.dataframe(styled_df.hide_index(), height=600, use_container_width=True)
