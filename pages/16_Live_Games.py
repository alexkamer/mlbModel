import pandas as pd
from datetime import datetime, timedelta
import concurrent.futures
import statsapi
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


@st.cache_resource
def load_data(filepath):
    data = pd.read_csv(filepath)
    return data

roster_df = load_data('datasets/roster_df.csv')
all_play_by_play_df = load_data('datasets/all_play_by_play.csv')
all_play_by_play_df = all_play_by_play_df.drop_duplicates(subset=['game_ID', 'atBatIndex','atBatResult'], keep='last')

def findTeamKeys():
    mlbTeamKeys = []
    url = "https://statsapi.mlb.com/api/v1/teams/"
    response = requests.get(url)



    data = response.json()
    for team in data['teams']:
        #if team.get('sport', {}).get('name', '') == "Major League Baseball":
        mlbTeamKeys.append(
            {
            'Team' : team.get('name'),
            'team_id' : team.get('id'),
            'team_abbr' : team.get('abbreviation'),
            'league' : team.get('league',{}).get('name'),
            'division' : team.get('division',{}).get('name'),
            'sport' : team.get('sport', {}).get('name')
            }
        )
    return pd.DataFrame(mlbTeamKeys)

statsApiTeamKeys = findTeamKeys()
mlbTeamKeys = statsApiTeamKeys[statsApiTeamKeys['sport'] == 'Major League Baseball']
team_ids = mlbTeamKeys['team_id'].to_list() 

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


in_Progress_Games = daySlate[daySlate['status'] == 'In Progress']
in_Progress_Games['label'] = in_Progress_Games.apply(lambda row: f"{row['away_name']} @ {row['home_name']}", axis=1)





if len(in_Progress_Games) >0:




    game_list = sorted(in_Progress_Games['label'].to_list())

    if 'game_label_selection' not in st.session_state:
        st.session_state.game_label_selection = game_list[0]

    def safe_index(options,value,default):
        try:
            return options.index(value)
        except:
            return options.index(default)

    def update_label_selection():
        st.session_state.game_label_selection = st.session_state.game_label_selection_input

    with st.sidebar:
        #label_selection = st.selectbox(label='Select a Game:', options=game_list)
        st.selectbox(
            label='Select a Game:',
            options=sorted(game_list),
            index=game_list.index(st.session_state.game_label_selection),
            key='game_label_selection_input',
            on_change=update_label_selection
        )
    

    #game_selection = in_Progress_Games[in_Progress_Games['label'] == label_selection]
    game_selection = in_Progress_Games[in_Progress_Games['label'] == st.session_state.game_label_selection]

    game_id = game_selection['game_id'].iloc[0]
    st.dataframe(game_selection)

    play_by_play_response = requests.get(f'https://statsapi.mlb.com/api/v1/game/{game_id}/playByPlay')
    play_by_play_data = play_by_play_response.json()
    play_by_play = play_by_play_data.get('allPlays')
    current_play = play_by_play_data.get('currentPlay')
    scoring_plays = play_by_play_data.get('scoringPlays')
    plays_by_inning = play_by_play_data.get('playsByInning')

    play_by_play_df = []
    append_to_df = play_by_play_df.append  # Bind the append method to a local variable for faster access

    for play in play_by_play:
        result = play.get('result', {})
        about = play.get('about', {})
        count = play.get('count', {})
        matchup = play.get('matchup', {})
        batter = matchup.get('batter', {})
        pitcher = matchup.get('pitcher', {})
        bat_side = matchup.get('batSide', {})
        pitch_hand = matchup.get('pitchHand', {})

        base_play_dict = {
            'result.type': result.get('type'),
            'result.event': result.get('event'),
            'result.description': result.get('description'),
            'result.rbi': result.get('rbi'),
            'result.awayScore': result.get('awayScore'),
            'result.homeScore': result.get('homeScore'),
            'result.isOut': result.get('isOut'),
            'about.atBatIndex': about.get('atBatIndex'),
            'about.halfInning': about.get('halfInning'),
            'about.isTopInning': about.get('isTopInning'),
            'about.isScoringPlay': about.get('isScoringPlay'),
            'about.inning': about.get('inning'),
            'about.captivatingIndex': about.get('captivatingIndex'),
            'final.count.balls': count.get('balls'),
            'final.count.strikes': count.get('strikes'),
            'final.count.outs': count.get('outs'),
            'matchup.batterName': batter.get('fullName'),
            'matchup.batterId': batter.get('id'),
            'matchup.batSide': bat_side.get('code'),
            'matchup.pitcherName': pitcher.get('fullName'),
            'matchup.pitcherId': pitcher.get('id'),
            'matchup.pitchHand': pitch_hand.get('code'),
        }

        for pitch in play.get('playEvents', []):
            if pitch.get('isPitch'):
                pitch_count = pitch.get('count', {})
                pitch_details = pitch.get('details', {})
                pitch_type = pitch_details.get('type', {})
                pitch_data = pitch.get('pitchData', {})

                play_dict = {
                    **base_play_dict,
                    'pitch.count.balls': pitch_count.get('balls'),
                    'pitch.count.strikes': pitch_count.get('strikes'),
                    'pitch.count.outs': pitch_count.get('outs'),
                    'pitch.details.call': pitch_details.get('call', {}).get('description'),
                    'pitch.description': pitch_details.get('description'),
                    'pitch.isInPlay': pitch_details.get('isInPlay'),
                    'pitch.isStrike': pitch_details.get('isStrike'),
                    'pitch.isBall': pitch_details.get('isBall'),
                    'pitch.isOut': pitch_details.get('isOut'),
                    'pitch.pitchType': pitch_type.get('description'),
                    'pitch.pitchNumber': pitch.get('pitchNumber'),
                    'pitch.pitchData.startSpeed': pitch_data.get('startSpeed'),
                    'pitch.pitchData.endSpeed': pitch_data.get('endSpeed'),
                }

                append_to_df(play_dict)

    play_by_play_df = pd.DataFrame(play_by_play_df)

    col1, col2 = st.columns(2)
    with col1:
        batter_col, pitcher_col = st.columns(2)

        batter_name = current_play.get('matchup', {}).get('batter', {}).get('fullName')
        pitcher_name = current_play.get('matchup', {}).get('pitcher', {}).get('fullName')

        if 'batter_name' not in st.session_state:
            st.session_state.batter_name = batter_name
        if 'pitcher_name' not in st.session_state:
            st.session_state.pitcher_name = pitcher_name


        def update_batter_name():
            st.session_state.batter_name = st.session_state.batter_name_input
        def update_pitcher_name():
            st.session_state.pitcher_name = st.session_state.pitcher_name_input

        with pitcher_col:
            try:
                #preset_p = sorted(play_by_play_df['matchup.pitcherName'].unique()).index(pitcher_name)
                st.selectbox(label='Select the Pitcher:', options=sorted(play_by_play_df['matchup.pitcherName'].unique()), index=sorted(play_by_play_df['matchup.pitcherName'].unique()).index(st.session_state.pitcher_name), key='pitcher_name_input', on_change=update_pitcher_name)

            except:
                st.write(f'{st.session_state.pitcher_name} has not played yet')
                st.selectbox(label='Select the Pitcher:', options=sorted(play_by_play_df['matchup.pitcherName'].unique()), key='pitcher_name_input', on_change=update_pitcher_name)

                #preset_b = sorted(play_by_play_df['matchup.pitcherName'].unique())[0]

            #st.selectbox(label='Select the Pitcher:', options=sorted(play_by_play_df['matchup.pitcherName'].unique()), index=sorted(play_by_play_df['matchup.pitcherName'].unique()).index(st.session_state.pitcher_name), key='pitcher_name_input', on_change=update_pitcher_name)
               
            #pitcher_name = st.selectbox(label='Select the Pitcher:', options=sorted(play_by_play_df['matchup.pitcherName'].unique()), index=preset_p)

            pitcher_df = play_by_play_df[play_by_play_df['matchup.pitcherName'] == st.session_state.pitcher_name].copy()
            end_p_ab = pitcher_df.drop_duplicates('about.atBatIndex', keep='last').copy()

            st.write(f'Number of ABs: {len(end_p_ab)}')
            st.write(f'Pitches Per AB: {round(end_p_ab['pitch.pitchNumber'].sum()/len(end_p_ab),3)}')
            #st.write(pitcher_df['pitch.pitchType'].value_counts())

            result = pitcher_df.groupby('pitch.pitchType').agg(
                average_speed=('pitch.pitchData.startSpeed', 'mean'),
                pitch_count=('pitch.pitchType', 'count')
            ).reset_index()
            st.dataframe(result)
            pitcher_pitchCheck = st.checkbox(label='Specific pitch number check?')
            if pitcher_pitchCheck:
                pitcherPitchNum = st.select_slider(label='Select the pitch number:', options=range(1,11))
                pitcherPitchSpeed = st.slider(
                    'Select the pitch speed:',
                    min_value=80.0,
                    max_value=101.0,
                    value=90.0,  # Default value
                    step=0.05
                )
                new_res = pitcher_df[(pitcher_df['pitch.pitchNumber'] == pitcherPitchNum)].groupby('pitch.pitchType').agg(
                    average_speed=('pitch.pitchData.startSpeed', 'mean'),
                    pitch_count=('pitch.pitchType', 'count')
                ).reset_index()

                
                st.write(f"{len(pitcher_df[(pitcher_df['pitch.pitchNumber'] == pitcherPitchNum) & (pitcher_df['pitch.pitchData.startSpeed'] > pitcherPitchSpeed)])}/{len(pitcher_df[(pitcher_df['pitch.pitchNumber'] == pitcherPitchNum)])}")
                st.dataframe(new_res)
                st.dataframe(pitcher_df[(pitcher_df['pitch.pitchNumber'] == pitcherPitchNum)])
            else:
                st.dataframe(end_p_ab)
            st.dataframe(pitcher_df)

        with batter_col:
            try:
                st.selectbox(label='Select the Batter:', options=sorted(play_by_play_df['matchup.batterName'].unique()), index=sorted(play_by_play_df['matchup.batterName'].unique()).index(st.session_state.batter_name), key='batter_name_input', on_change=update_batter_name)

                #preset_b = sorted(play_by_play_df['matchup.batterName'].unique()).index(batter_name)
            except:
                # preset_b = sorted(play_by_play_df['matchup.batterName'].unique())[0]
                st.write(f'{st.session_state.batter_name} has not played yet')
                st.selectbox(label='Select the Batter:', options=sorted(play_by_play_df['matchup.batterName'].unique()), key='batter_name_input', on_change=update_batter_name)

            #batter_name = st.selectbox(label='Select the Batter:', options=sorted(play_by_play_df['matchup.batterName'].unique()), index=preset_b)
            batter_df = play_by_play_df[play_by_play_df['matchup.batterName'] == st.session_state.batter_name].copy()
            all_batter_pbp = all_play_by_play_df[all_play_by_play_df['batter_name'] == st.session_state.batter_name].copy()
            all_batter_pbp['atBatResult'] = all_batter_pbp['atBatResult'].replace({
                    'Groundout': 'Other',
                    'Pop Out': 'Other',
                    'Fielders Choice Out' : 'Other',
                    'Lineout' : 'Other',
                    'Sac Fly' : 'Other',
                    'Forceout' : 'Other'
                })
            numberGames = 30
            value_counts = all_batter_pbp.tail(numberGames)['atBatResult'].value_counts()
            percentages = round(all_batter_pbp.tail(numberGames)['atBatResult'].value_counts(normalize=True) * 100,2)

            # Combine the counts and percentages into a single DataFrame
            result_df = value_counts.to_frame(name='Count')
            result_df['Percent'] = percentages


            st.dataframe(result_df)

            end_ab = batter_df.drop_duplicates('about.atBatIndex', keep='last').copy()

            st.write(f'Number of ABs: {len(end_ab)}')
            st.write(f'AB was in play/# of ABs: {end_ab['pitch.isInPlay'].sum()}/{len(end_ab)}')
            st.write(f'Strikeouts / ABs: {end_ab['result.event'].value_counts().get('Strikeout', 0)}/{len(end_ab)}')
            st.write(f'Pitches per AB: {(end_ab['pitch.pitchNumber'].sum() + end_ab['final.count.balls'].sum()) / len(end_ab)}')
            
            pitchCheck = st.checkbox('Specific pitch check?')
            pitcherCheck = st.checkbox('Specific pitcher only?')
            if pitchCheck and pitcherCheck:
                pitchNum = st.select_slider(label='Select the pitch number:.', options=range(1,12))
                st.dataframe(batter_df[(batter_df['pitch.pitchNumber'] == pitchNum) & (batter_df['matchup.pitcherName'] == pitcher_name)])
            elif pitchCheck:
                pitchNum = st.select_slider(label='Select the pitch number:', options=range(1,11),key='batter_pitch')
                st.dataframe(batter_df[(batter_df['pitch.pitchNumber'] == pitchNum)])
            elif pitcherCheck:
                st.dataframe(batter_df[(batter_df['matchup.pitcherName'] == pitcher_name)])
            else:
                st.dataframe(batter_df)
            st.dataframe(batter_df)
        
            
        refreshButton = st.button(label='Refresh')

        if refreshButton:
            st.rerun()

    with col2:
        st.dataframe(play_by_play_df)



    lineScore_response = requests.get(f'https://statsapi.mlb.com/api/v1/game/{game_id}/linescore')
    lineScore_data = lineScore_response.json()

    contextMetrics_response = requests.get(f'https://statsapi.mlb.com/api/v1/game/{game_id}/contextMetrics')
    contextMetrics_data = contextMetrics_response.json()

    batter_name = current_play.get('matchup', {}).get('batter', {}).get('fullName')
    pitcher_name = current_play.get('matchup', {}).get('pitcher', {}).get('fullName')

    batter_data = roster_df[roster_df['Name'] == batter_name]
    pitcher_data = roster_df[roster_df['Name'] == pitcher_name]

    inning_linescore = lineScore_data.get('innings',[])
    lineScore_filter = st.selectbox(label='Select the Line Score filter:', options=sorted(['runs', 'hits', 'errors', 'leftOnBase']))

    inning_data = {
    'Inning': [inning['num'] for inning in inning_linescore],
    'Home': [inning['home'].get(lineScore_filter,0) for inning in inning_linescore],
    'Away': [inning['away'].get(lineScore_filter,0) for inning in inning_linescore]
    }
    linescore_df = pd.DataFrame(inning_data)
    home_total = linescore_df['Home'].sum()
    away_total = linescore_df['Away'].sum()

    # Add the totals as a new column
    linescore_df.loc['Total'] = ['Total', home_total, away_total]

    # Transpose the DataFrame to show the linescore horizontally
    linescore_horizontal = linescore_df.set_index('Inning').T
    linescore_horizontal = linescore_horizontal.reindex(['Away', 'Home'])


    away_column, home_column = st.columns(2)

    with away_column:
        away_dict = {
            'Team' : contextMetrics_data['game']['teams']['away']['team']['name'],
            'winProbability' : contextMetrics_data['awayWinProbability'],
            'Score' : contextMetrics_data['game']['teams']['away']['score'],
            'Wins' : contextMetrics_data['game']['teams']['away']['leagueRecord']['wins'],
            'Losses' : contextMetrics_data['game']['teams']['away']['leagueRecord']['losses'],
            'winPct' : contextMetrics_data['game']['teams']['away']['leagueRecord']['pct']
        }
        st.write(away_dict['Team'])
        st.write(away_dict['winProbability'])
        st.write(away_dict['Score'])
        st.write(away_dict['Wins'])
        st.write(away_dict['Losses'])
        st.write(away_dict['winPct'])


    with home_column:
        home_dict = {
            'Team' : contextMetrics_data['game']['teams']['home']['team']['name'],
            'winProbability' : contextMetrics_data['homeWinProbability'],
            'Score' : contextMetrics_data['game']['teams']['home']['score'],
            'Wins' : contextMetrics_data['game']['teams']['home']['leagueRecord']['wins'],
            'Losses' : contextMetrics_data['game']['teams']['home']['leagueRecord']['losses'],
            'winPct' : contextMetrics_data['game']['teams']['home']['leagueRecord']['pct']
        }
        st.write(home_dict['Team'])
        st.write(home_dict['winProbability'])
        st.write(home_dict['Score'])
        st.write(home_dict['Wins'])
        st.write(home_dict['Losses'])
        st.write(home_dict['winPct'])


    st.dataframe(linescore_horizontal)

    st.write("### Current Count:")
    st.write(f"Balls: {lineScore_data['balls']}")
    st.write(f"Strikes: {lineScore_data['strikes']}")
    st.write(f"Outs: {lineScore_data['outs']}")




    # batter_col, pitcher_col = st.columns(2)
    # with batter_col:
    #     st.header(batter_name)
    #     team_logo = batter_data['Team_Logo'].iloc[0] if len(batter_data['Team_Logo']) > 0 else None
    #     batter_image = batter_data['headShot'].iloc[0] if len(batter_data['headShot']) > 0 else None
    #     st.markdown(f"""
    #         <div style="text-align: center; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
    #             <div style="position: relative; width: 200px; height: 200px; margin: 0 auto;">
    #                 <img src="{team_logo}" style="width: 100%; height: 100%;">
    #                 <img src="{batter_image}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
    #         </div>
    #         """, unsafe_allow_html=True)
    
    # with pitcher_col:
    #     st.header(pitcher_name)

    #     team_logo = pitcher_data['Team_Logo'].iloc[0] if len(pitcher_data['Team_Logo']) > 0 else None
    #     pitcher_image = pitcher_data['headShot'].iloc[0] if len(pitcher_data['headShot']) > 0 else None
    #     st.markdown(f"""
    #         <div style="text-align: center; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
    #             <div style="position: relative; width: 200px; height: 200px; margin: 0 auto;">
    #                 <img src="{team_logo}" style="width: 100%; height: 100%;">
    #                 <img src="{pitcher_image}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
    #         </div>
    #         """, unsafe_allow_html=True)
        




    # st.write(contextMetrics_data)
    # st.write(lineScore_data)

else:
    st.write('No Games on currently')


