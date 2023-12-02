import streamlit as st
import numpy as np
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

import requests

# use full width of the page
st.set_page_config(layout="wide")
# read the json file
competitions = pd.read_json("./asset/files/competitions.json")

st.title('Football Analysis App')

# define available season options for different tournaments
fifa_season = ('2022', '2018')
laliga_season = ('2020/2021', '2019/2020', '2018/2019')
PL_season = ('2015/2016', '2003/2004')
season = fifa_season
# columns for selecting season and tournament
select_col1, select_col2 = st.columns(2)

with select_col1:
    option_1 = st.selectbox(
        'Football League',
        ('FIFA World Cup', 'La Liga', 'Premier League'))

# poulate seson option according to league selected
if option_1 == 'FIFA World Cup':
    season = fifa_season
elif option_1 == 'La Liga':
    season = laliga_season
elif option_1 == 'Premier League':
    season = PL_season

with select_col2:
    option_2 = st.selectbox(
        'Season',
        season)
st.write('You selected:', option_1, 'and', option_2)

# get the competition id from competition name
def get_competiton_id(df: pd.DataFrame, competition_name: str) -> int:
    id = df.query('competition_name == @competition_name')["competition_id"].unique()
    return id[0]
# get the season id from seson name
def get_season_id(df: pd.DataFrame, season_name: str) -> int:
    id = df.query('season_name == @season_name')["season_id"].unique()
    return id[0]

def get_match_url(df: pd.DataFrame, competition_name: str, season_name: str) -> str:
    name = get_competiton_id(df, competition_name)
    season = get_season_id(df, season_name)
    base_url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/matches/{name}/{season}.json"
    return base_url

@st.cache_data(max_entries=10, show_spinner=True)
def get_match_data(url: str)->pd.DataFrame:
    response = requests.get(url)
    matches_data = {'match_date': [], 'home_team': [],
                    'home_score': [], 'away_score': [],
                    'away_team': [], 'match_id': []}
    if response.status_code == 200:
        json_data = response.json()
        event_id = json_data[0]['match_id']
        for match in json_data:
            new_match = {'match_date': match['match_date'], 'home_team': match['home_team']['home_team_name'], 
                         'away_team': match['away_team']['away_team_name'], 'home_score': match['home_score'], 
                         'away_score': match['away_score'], 'match_id': match['match_id']}
            for k, v in new_match.items():
                matches_data[k].append(v)
    else:
        print("Failed to fetch the file. Status code:", response.status_code)
    matches_df = pd.DataFrame(matches_data)

    return matches_df

@st.cache_data(max_entries=10, show_spinner=True)
def get_lineup_data(event_id: str) -> dict:
    lineup = {}
    lineup_url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/lineups/{event_id}.json"
    response = requests.get(lineup_url)
    if response.status_code == 200:
        json_data = response.json()
        for data in json_data:
            team = data["team_name"]
            lineup[team] = []
            for player in data["lineup"]:
                starting_11 = False
                for pos in player['positions']:
                    if pos['start_reason'] == 'Starting XI':
                        starting_11 = True
                if nickname := player["player_nickname"]:
                    lineup[team].append((nickname, starting_11))
                else:
                    lineup[team].append((player["player_name"], starting_11))
    else:
        print("Failed to fetch the file. Status code:", response.status_code)
    return lineup

# user selected name and season
competition_name_selected, season_name_selected = option_1, option_2

match_url = get_match_url(competitions, competition_name_selected, season_name_selected)
matches_df = get_match_data(match_url)

# Build Ag-Grid options
gd = GridOptionsBuilder.from_dataframe(matches_df)
gd.configure_default_column(resizable=True, 
                            cellStyle={'text-align':'center'})
gd.configure_column(field="match_id", 
                    hide=True)
gd.configure_column(field="match_date", 
                    header_name="Date",
                    type=['dateColumnFilter', 'customDateTimeFormat'],
                    custom_format_string="dd/MM/yyyy",
                    width='20%',
                    initialSort='asc')
gd.configure_column(field="home_team",
                    header_name="Team 1",
                    width='30%')
gd.configure_column(field="away_team",
                    header_name="Team 2",
                    width='30%')
#configures last row to use custom styles based on cell's value, injecting JsCode on components front end
home_score_jscode = JsCode("""
function(params) {
    if (params.data['home_score'] > params.data['away_score']) {
        return {
            'color': 'green',
            'text-align': 'center',
            'font-size': '22px',
            'font-weight': 'bold'
        }
    } else if(params.data['home_score'] < params.data['away_score']) {
        return {
            'color': 'red',
            'text-align': 'center',
            'font-size': '22px',
            'font-weight': 'bold'     
        }
    } else {
        return {
            'text-align': 'center',
            'font-size': '22px',
            'font-weight': 'bold'
        }
    }
};
""")
gd.configure_column(field="home_score",
                    header_name="",
                    type=["numericColumn"],
                    width='10%',
                    cellStyle=home_score_jscode)

away_score_jscode = JsCode("""
function(params) {
    if (params.data['home_score'] < params.data['away_score']) {
        return {
            'color': 'green',
            'text-align': 'center',
            'font-size': '22px',
            'font-weight': 'bold'
        }
    } else if(params.data['home_score'] > params.data['away_score']) {
        return {
            'color': 'red',
            'text-align': 'center',
            'font-size': '22px',
            'font-weight': 'bold'     
        }
    } else {
        return {
            'text-align': 'center',
            'font-size': '22px',
            'font-weight': 'bold'
        }
    }
};
""")

gd.configure_column(field="away_score",
                    header_name="",
                    type=["numericColumn"],
                    width='10%',
                    cellStyle=away_score_jscode)
gd.configure_pagination(enabled=False)
gd.configure_selection(selection_mode="single", use_checkbox=True)
gd.configure_selection('single', pre_selected_rows=[0])
grid_options = gd.build()

# display match lineup
lineup_col1, lineup_col2 = st.columns((2,1))
with lineup_col1:
    # Display the Ag-Grid table
    matches_ag_grid = AgGrid(matches_df, 
                    gridOptions=grid_options,
                    enable_enterprise_modules=True,
                    fit_columns_on_grid_load=True,
                    height=500,
                    width='100%',
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    allow_unsafe_jscode=True)

selected_row = matches_ag_grid["selected_rows"]

with lineup_col2:
    if selected_row:
        match_id = selected_row[0]['match_id']
        lineup = get_lineup_data(match_id)
        starting_lineup = {team : [player for (player, starting_11) in lineup[team] if starting_11] for team in lineup.keys()}
        lineup_df = pd.DataFrame(starting_lineup)

        # Build Ag-Grid options
        gdl = GridOptionsBuilder.from_dataframe(lineup_df)
        gdl.configure_default_column(resizable=True, 
                            cellStyle={'text-align':'center'})
        grid_options_l = gdl.build()
        lineup_ag_grid = AgGrid(lineup_df,
                                gridOptions=grid_options_l)

