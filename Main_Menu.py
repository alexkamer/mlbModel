import streamlit as st
st.set_page_config(layout="wide")


dayMatchup = st.Page('pages/1_Day_Matchup_Preview.py', title='Day Schedule')
teamStandings = st.Page('pages/2_Team_Standings.py', title='League Standings')
injuryReport = st.Page('pages/3_Injury_Report.py', title='Injury Report')
batterPropComparison = st.Page('pages/4_Player_Stats_Correlation.py', title='Batter Prop Comparison')
pitcherPerInning = st.Page('pages/8_Stats_Per_Inning.py', title='Pitcher Stats Per Inning')
pitcherLiveProps = st.Page('pages/10_Pitcher_Per_Inning_Analysis.py', title='Pitcher Live Props')
teamPerInning = st.Page('pages/11_Team_Per_Inning_Stats.py', title='Team Per Inning Statistics')
liveGames = st.Page('pages/16_Live_Games.py', title='Live Games')
pitcherKLeader = st.Page('pages/5_Leading_Pitcher_K.py', title='Pitcher With Most Strikeouts for day')
pitcherProps = st.Page('pages/17_Pitcher_Props.py', title='Pitcher Prop Info')

pg = st.navigation(
    {
        "Schedule/Scores" : [dayMatchup, liveGames, pitcherKLeader],
        "Team Information" : [teamStandings,injuryReport, teamPerInning],
        "Player Info" : [batterPropComparison, pitcherPerInning, pitcherLiveProps, pitcherProps]
    }
)
pg.run()