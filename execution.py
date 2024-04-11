import pandas as pd
import streamlit as st
import os
import altair as alt

files = os.listdir('data')

yakker = pd.DataFrame()
for file in files:

    cur_yakker = pd.read_csv(f'data/{file}')
    file = file[:-4]

    split = file.split('_')
    date = f'{split[0]}/{split[1]}/{split[2]}'

    if len(split) == 4:
        team = split[3]
    elif len(split) == 5:
        team = f'{split[3]} {split[4]}'
    elif len(split) == 6:
        team = f'{split[3]} {split[4]} {split[5]}'
    elif len(split) == 7:
        team = f'{split[3]} {split[4]} {split[5]} {split[6]}'

    cur_yakker['Game'] = f'{date} - {team}'

    yakker = pd.concat([yakker, cur_yakker])

yakker = yakker[yakker['PitcherTeam'] == 'Georgia tech']

st.header('GT Pitcher Execution')

pitcher = st.selectbox('Select Pitcher', yakker['Pitcher'].unique())

games = yakker['Game'].unique().tolist()
games.insert(0, 'All Games')
games = st.multiselect('Select Game', games, default='All Games')

yakker = yakker[(yakker['Pitcher'] == pitcher) & ((yakker['Game'].isin(games)) | ('All Games' in games))]
yakker['calledLoc'] = round(pd.to_numeric(yakker['calledLoc'], errors='coerce'), 0)
yakker.loc[yakker['TaggedPitchType'] == 'Changeup', 'calledLoc'] = 0
yakker = yakker.dropna(subset=['TaggedPitchType', 'calledLoc', 'PitchCall'])
yakker['calledLoc'] = yakker['calledLoc'].astype(int)
yakker = yakker[yakker['calledLoc'] != 6]
yakker['TaggedPitchType'] = yakker['TaggedPitchType'].apply(lambda x: x.replace(' ', '').capitalize())

pitches = sorted(yakker['TaggedPitchType'].unique())
pitches.insert(0, 'All Pitches')
pitches = st.multiselect('Select Pitch Type', pitches, default='All Pitches')

locations = sorted(yakker['calledLoc'].round().astype(int).unique())
locations.insert(0, 'All Locations')
locations = st.multiselect('Select Location', locations, default='All Locations')

yakker = yakker[(yakker['TaggedPitchType'].isin(pitches) | ('All Pitches' in pitches)) & (yakker['calledLoc'].isin(locations) | ('All Locations' in locations))]

yakker = yakker[(yakker['PlateLocSide'] > -2) & (yakker['PlateLocSide'] < 2) & (yakker['PlateLocHeight'] > 0) & (yakker['PlateLocHeight'] < 5)]

yakker['Result'] = yakker['PitchCall']

# if result is InPlay, change to HardHit if exit speed > 67.5
yakker.loc[(yakker['Result'] == 'InPlay') & (yakker['ExitSpeed'] > 67.5), 'Result'] = 'Hard Hit'
yakker.loc[(yakker['Result'] == 'InPlay') & (yakker['Result'] != "Hard Hit"), 'Result'] = 'Soft Contact'

yakker['HardHit'] = yakker['Result'].apply(lambda x: 1 if x == 'Hard Hit' else 0)
yakker['SoftContact'] = yakker['Result'].apply(lambda x: 1 if x == 'Soft Contact' else 0)

yakker['Exit Velo'] = round(yakker['ExitSpeed'], 1).fillna('')

results = sorted(yakker['Result'].unique())
results.insert(0, 'All Results')
results = st.multiselect('Select Result', results, default='All Results')

yakker = yakker[(yakker['Result'].isin(results) | ('All Results' in results))]

def executed(PlateLocSide, PlateLocHeight, calledLoc):
    if -17/24 < PlateLocSide < 17/24 and 5/4 < PlateLocHeight < 3:
        if calledLoc == 1:
            if PlateLocSide > 0 and PlateLocHeight < 17/8:
                return True
        elif calledLoc == 2:
            if PlateLocSide > 0 and PlateLocHeight > 17/8:
                return True
        elif calledLoc == 3:
            if PlateLocSide < 0 and PlateLocHeight > 17/8:
                return True
        elif calledLoc == 4:
            if PlateLocSide < 0 and PlateLocHeight < 17/8:
                return True
    return False

# Apply the function to the yakker DataFrame
yakker['Executed'] = yakker.apply(lambda row: executed(row['PlateLocSide'], row['PlateLocHeight'], row['calledLoc']), axis=1)

yakker = yakker.rename(columns={'TaggedPitchType': 'Pitch', 'calledLoc': 'Spot'})

# add line break
st.write('')
st.write('')
st.write('')
st.write('')

scatter = alt.Chart(yakker).mark_circle(size=100).encode(
    alt.X('PlateLocSide', axis=alt.Axis(labels=False, ticks=False, title='')),
    alt.Y('PlateLocHeight', axis=alt.Axis(labels=False, ticks=False, title='')),
    color='Pitch',
    tooltip=['Pitch', 'Spot', 'Result', 'Exit Velo', 'Executed', 'Game']
)

# Define the lines
k_zone = pd.DataFrame({
    'x': [-17/24, 17/24, 17/24, -17/24, -17/24],
    'y': [5/4, 5/4, 3, 3, 5/4]
}).reset_index()

# Create the lines chart
k_zone_chart = alt.Chart(k_zone).mark_line(color='black').encode(
    x='x:Q',
    y='y:Q',
    order='index'
)

batters_box_1 = pd.DataFrame({
    'x': [-29/24, -29/24, -29/24],
    'y': [0, 5, 0]
})

batters_box_2 = pd.DataFrame({
    'x': [29/24, 29/24, 29/24],
    'y': [0, 5, 0]
})

vert_line = pd.DataFrame({
    'x': [0, 0],
    'y': [5/4, 3]
})

horz_line = pd.DataFrame({
    'x': [-17/24, 17/24],
    'y': [17/8, 17/8]
})

batter_box_1_chart = alt.Chart(batters_box_1).mark_line(color='black', strokeDash=[5,5]).encode(
    x='x:Q',
    y='y:Q'
)

batter_box_2_chart = alt.Chart(batters_box_2).mark_line(color='black', strokeDash=[5,5]).encode(
    x='x:Q',
    y='y:Q'
)

vert_line_chart = alt.Chart(vert_line).mark_line(color='black', strokeDash=[5,5]).encode(
    x='x:Q',
    y='y:Q'
)

horz_line_chart = alt.Chart(horz_line).mark_line(color='black', strokeDash=[5,5]).encode(
    x='x:Q',
    y='y:Q'
)


# Combine scatter plot and lines
combined_chart = scatter + k_zone_chart + batter_box_1_chart + batter_box_2_chart + vert_line_chart + horz_line_chart

st.altair_chart(combined_chart)

no_change = yakker[yakker['Spot'] != 0]

executed_pct = round(no_change['Executed'].mean() * 100, 1)

if(yakker['HardHit'].sum() + yakker['SoftContact'].sum()) == 0:
    hard_hit_pct = 0
else:
    hard_hit_pct = round((yakker['HardHit'].sum() / (yakker['HardHit'].sum() + yakker['SoftContact'].sum())) * 100, 1)


if(yakker[yakker['Result'] == 'StrikeSwinging'].shape[0] + yakker[yakker['Result'] == 'Foul'].shape[0] + yakker[yakker['Result'] == 'Soft Contact'].shape[0] + yakker[yakker['Result'] == 'Hard Hit'].shape[0]) == 0:
    whiff_pct = 0
else:
    whiff_pct = round(yakker[yakker['Result'] == 'StrikeSwinging'].shape[0] / (yakker[yakker['Result'] == 'StrikeSwinging'].shape[0] + yakker[yakker['Result'] == 'Foul'].shape[0] + 
                                                                           yakker[yakker['Result'] == 'Soft Contact'].shape[0] + yakker[yakker['Result'] == 'Hard Hit'].shape[0]) * 100, 1)
    
st.write(f'Executed: {executed_pct}%')
st.write(f'Hard Hit: {hard_hit_pct}%')
st.write(f'Whiff: {whiff_pct}%')