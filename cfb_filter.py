import streamlit as st

import pandas as pd
import numpy as np

import plotly
pd.options.plotting.backend = "plotly"

import math

path1="/content/drive/My Drive/cfb_example_data/master_encode.csv"
game_data = pd.read_csv(path1)

min_dist = 0
max_dist = 36
min_diff = -99
max_diff = 99
min_yardline = 0
max_yardline = 100
player_select_list = []
remove_all_targets = []

st.set_page_config(layout="wide")

st.container()

plot_spot = st.empty()

with st.container():
    year, location, opponent, offense = st.columns(4)
    
    opp_ = ['ALL'] + game_data.Poss.unique().tolist()
    
    year_selector = year.multiselect('Select year(s)', game_data.Season.unique().tolist())
    
    year_df = game_data[game_data.Season.isin(year_selector)]
    
    location_selector = location.multiselect('Select home/road', year_df['Home/Away'].unique().tolist())
    
    location_df = year_df[year_df['Home/Away'].isin(location_selector)]
    
    if location_df.shape[0] > 0:
        opp_ = ['ALL'] + location_df.Poss.unique().tolist()
        opp_.remove('PSU')
    
    opponent_selector = opponent.multiselect('Select opponent(s)', opp_)
    opponent_selector2 = opponent_selector + ['PSU']
    
    opponent_df = location_df[location_df['Poss'].isin(opponent_selector2)]
    
    offense_selection = offense.radio("Select Offense or Defense", ('Offense', 'Defense'))
    
    if offense_selection == 'Offense':
        offense_df = location_df[location_df['Poss'] == 'PSU']
    else:
        offense_df = location_df[location_df['Poss'].isin(opponent_selector)]  
    
    down, distance, quarter, margin = st.columns(4)
    
    down_selector = down.multiselect('Select down(s)', ['1st ', '2nd ', '3rd ', '4th '])
    
    down_df = offense_df[offense_df['Down'].isin(down_selector)]
    
    if down_df.shape[0] > 0:
        min_dist = down_df.Distance_enc.min()
        max_dist = down_df.Distance_enc.max()
    
    distance_selector = distance.slider('Select distance(s) to line of gain', min_dist, max_dist, (min_dist, max_dist))
    
    distance_df = down_df[down_df.Distance_enc.between(distance_selector[0], distance_selector[1], inclusive='both')]
    
    quarter_selector = quarter.multiselect('Select quarter(s)', [' 1st', ' 2nd', ' 3rd', ' 4th'])
    
    quarter_df = distance_df[distance_df.Quarter.isin(quarter_selector)]
    
    if quarter_df.shape[0] > 0:
        min_diff = quarter_df['Diff Score'].min()
        max_diff = quarter_df['Diff Score'].max()
    
    margin_selector = margin.slider('Select score differential range', min_diff, max_diff, (min_diff, max_diff)) 
    
    margin_df = quarter_df[quarter_df['Diff Score'].between(margin_selector[0], margin_selector[1], inclusive='both')]
    
    yardline, play_type, player, targeted = st.columns(4)
    
    if margin_df.shape[0] > 0:
        min_yardline = quarter_df['Yardline_enc'].min()
        max_yardline = quarter_df['Yardline_enc'].max()
    
    yardline_selector = yardline.slider('Select line of scrimage range', min_yardline, max_yardline, (min_yardline, max_yardline)) 
    
    yardline_df = margin_df[margin_df['Yardline_enc'].between(yardline_selector[0], yardline_selector[1], inclusive='both')]
    
    play_type_selector = play_type.multiselect('Select pass and/or run', ['Run', 'Pass'])
    
    st.write('play_type:', play_type_selector, len(play_type_selector))
    
    if len(play_type_selector)==1:
        if play_type_selector[0] == 'Run':
            play_run_selector_df = yardline_df[yardline_df['Run: Yes=1, No=0']==float(1)]
            st.write('dataframe', play_run_selector_df.head(5))
            player_select_list = play_run_selector_df['Ball Carrier'].unique().tolist()
        else:
            play_pass_selector_df = yardline_df[yardline_df['Pass: Yes=1, No=0']==float(1)]
            player_select_list = play_pass_selector_df['Passer'].unique().tolist()
    else:
        play_type_selector_df_1 = yardline_df[yardline_df['Run: Yes=1, No=0']==float(1)]
        play_type_selector_df = play_type_selector_df_1.append(yardline_df[yardline_df['Pass: Yes=1, No=0']==float(1)])
        player_select_list_ball = play_type_selector_df['Ball Carrier'].unique().tolist()
        player_select_list = player_select_list_ball + play_type_selector_df['Passer'].unique().tolist()
    
    # Pass: Yes=1, No=0	Passer	Completed?: Yes=1, No=0	Targeted	Run: Yes=1, No=0	Ball Carrier
    player_selector = player.multiselect('Select passer/runner', player_select_list)
    
    if len(play_type_selector)==1:
        if play_type_selector[0] == 'Run':
            player_df = play_run_selector_df[play_run_selector_df['Ball Carrier'].isin(player_selector)]
            target_list = ['ALL'] + player_df['Ball Carrier'].unique().tolist()
            if '0' in target_list:
                target_list.remove('0')
        else:
            player_df = play_pass_selector_df[play_pass_selector_df['Passer'].isin(player_selector)]
            target_list = ['ALL'] + player_df['Targeted'].unique().tolist() 
            if '0' in target_list:
                target_list.remove('0')
    else:
        player_df_1 = play_type_selector_df[play_type_selector_df['Ball Carrier'].isin(player_selector)]
        player_df = player_df_1.append(play_type_selector_df[play_type_selector_df['Passer'].isin(player_selector)])
        runner_list = player_df['Ball Carrier'].unique().tolist()
        target_list = ['ALL'] + runner_list + player_df['Targeted'].unique().tolist()
        if '0' in target_list:
            target_list.remove('0')
    
    
    
    targeted_selector = targeted.multiselect('Select target/runner', target_list)
    
    if 'ALL' in targeted_selector:
        target_list.remove('ALL')
        targeted_selector = target_list
    
    #st.write('targets:', targeted_selector)
    
    target_df = player_df[player_df['Targeted'].isin(targeted_selector)]
    
    # calculate completion %, yards per attempt, yards per completion, yards completion histogram
    tar_count = target_df.groupby('Targeted').count().Passer
    tar_yards = target_df.groupby('Targeted').sum().yards_enc
    
    completed_df = target_df[target_df['Completed?: Yes=1, No=0']=='1']
    com_count = completed_df.groupby('Targeted').count().Passer
    
    st.write('stats', com_count.shape[0], completed_df.shape[0])
    
    plot_stats = []
    for counts, yards, player in zip(tar_count, tar_yards, tar_count.index):
        if player in com_count.index:
            comps = com_count[com_count.index == player][0]
            plot_stats.append([player, comps/counts*100, yards/counts, yards/comps])
        else:
            plot_stats.append([player, 0, 0, 0])
    
    
          
    plot_stats_df = pd.DataFrame(plot_stats, columns=['Targeted_Player', 'Completion_%', 'Yards_per_Attempt', 'Yards_per_Completion'])
    
    import plotly.express as px
    
    fig = px.scatter(plot_stats_df, x="Completion_%", y="Yards_per_Attempt",
    	         size="Yards_per_Completion", color="Targeted_Player", hover_name="Targeted_Player")
                     
    #fig = target_df.yards_enc.hist(by=targeted_selector)
    with plot_spot:
        st.plotly_chart(fig, use_container_width=True)
    
    
    st.write('Range diff:', [game_data.shape[0], year_df.shape[0], location_df.shape[0], opponent_df.shape[0], down_df.shape[0], distance_df.shape[0], quarter_df.shape[0], margin_df.shape[0], yardline_df.shape[0]])
    
