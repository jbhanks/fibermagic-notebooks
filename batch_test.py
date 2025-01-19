import pandas as pd
import numpy as np
from fibermagic.IO.NeurophotometricsIO import extract_leds
import os
import pathlib
from analysis_utils import *

# If not already installed, uncomment and and run:
# pip install git+https://github.com/faustrp/fibermagic.git

basepath = '/home/james/Massive/PROJECTDATA/NAcC gDA3m + rAdo1.3 FR20-PR/DATA/'




from rudi_demodulate import *
import copy
from rudi_demodulate import demodulate as detrend

def run_detrend(df, method):
    # df2 = copy.deepcopy(df)
    # from fibermagic import demodulate as detrend
    df["zdFF"] = detrend(df , "Timestamp", "Signal", "Reference", "Channel", steps=False, method=method, smooth=10, standardize=True)
    df.reset_index().set_index(['Region', 'Channel', 'FrameCounter'])
    return df


recs = organize_logs(basepath)

# def organize_logs(basepath, newest_only=True):
protocols = [dir for dir in
                os.listdir(basepath) if not dir.startswith('.')]
recordings = {}
for protocol in protocols:
    recordings[protocol] = []
    # get paths while excluding dotfiles
    for f in pathlib.Path(basepath + protocol).glob('**/[!.]*/'):
        logfile = f / 'logs.csv'
        logs = read_experiment(logfile)
        mice_by_exp = str(logfile.parents[0]).split('/')[-1].split(',')
        for mouse in mice_by_exp:
            new_recording = get_one(mouse, logs)
            new_recording['path'] = f
            new_recording['protocol'] = protocol
            recordings[protocol].append(new_recording)
        recordings[protocol] = [rec for rec in
                                recordings[protocol] if rec is not None]
    if newest_only == True:
        recordings[protocol] = keep_newest_only(recordings[protocol])
    else:
        pass
    # return recordings


for schedule in recs.keys():
    for rec in recs[schedule]:
        rec = get_photometry(rec)
        rec['photometry'] = count_frames(rec['photometry'])
        rec['photometry'] = convert_to_long(rec['photometry'])
        rec['detrended'] = run_detrend(rec['photometry'], "airPLS")
        # rec['detrended'] = run_detrend(rec['photometry'], "biexponential decay")


all_logs = []
all_synced = []

for schedule in recs.keys():
    for idx,rec in enumerate(recs[schedule]):
        nu_df, synced = synchronize_files(rec)
        nu_df['schedule'] = schedule
        synced['schedule'] = schedule
        all_logs.append(nu_df)
        all_synced.append(synced)
        # recs[schedule][idx]['nu_logs'] = nu_df
        # recs[schedule][idx]['synced'] = synced


catlogs = pd.concat(all_logs)
catsync = pd.concat(all_synced)



#####
from fibermagic.core.perievents import perievents

# peri = perievents(rec['detrended'], rec['synced'].Event=='FD', window=20, frequency=10)
# peri
#
# from pathlib import Path
# output_path = Path('Perievents rAdo1.3+GCaMP8m/biexponential decay/PR5')
# schedule = 'PR5'
# peri.to_csv(mouse + schedule + '-20s.csv')

# figR = px.scatter(peri.loc['Region0R'].reset_index(), x='Timestamp', y='Trial', color='zdFF', range_color=(-5,5),
#                  color_continuous_scale=['blue', 'grey', 'red'], height=300).update_yaxes(autorange="reversed", title_text='Reward #', title_font={'size': 20}, tickfont={'size': 18}).update_xaxes(title_text=None, showticklabels=False).update_layout(title={'text':"Adenosine", 'x':0.5})
# for scatter in figR.data:
#     scatter.marker.symbol = 'square'
# figR.show()



df = catsync
logs = catlogs
logs = logs.rename(columns={'SystemTimestamp':'Timestamp'})
window=5
frequency=10

# def perievents(df, logs, window, frequency):
    """
    produces perievent slices for each event in logs
    :param df: df with 'Channel' as index and value columns
    :param logs: logs df with columns event and same index as df
    :param window: number of SECONDS to cut left and right off
    :param frequency: int, frequency of recording in Hz
    :return: perievent dataframe with additional indices event, timestamp and Trial
    """
channels = df.index.unique(level='Channel')

if 'Channel' not in logs.index.names:  # make indices the same to intersect
    logs['Channel'] = [list(channels)] * len(logs)
    logs = logs.explode('Channel').set_index('Channel', append=True)
    logs = logs.swaplevel(-1, -2)

logs = logs.loc[df.index.intersection(logs.index)]  # remove events that are not recorded

df = df.sort_index()  # to slice it in frame ranges
logs['Trial'] = logs.groupby(logs.index.names[:-1]).cumcount()
peri = []
timestamps = np.arange(-window, window + 1e-9, 1 / frequency)

failed = []

# extract slice for each event and concat
for index, row in logs.iterrows():
    start = index[:-1] + (index[-1] - window * frequency,)
    end = index[:-1] + (1 + index[-1] + window * frequency,)
    print(start, end)
    single_event = df.iloc[start[2]:end[2]]
    print("single event shape", single_event.shape)
    if single_event.shape[0] != 101:
        failed.append(single_event)
        continue
    #single_event[row.index] = row
    single_event['Timestamp'] = timestamps
    print(single_event)
    peri.append(single_event)  # Set on copy warning can be ignored because it is a copy anyways

peri = pd.concat(peri)

peri = peri.set_index(list(logs.columns), append=True)
peri = peri.reset_index(['FrameCounter'], drop=True)
    # return peri















# if not os.path.exists("plots"):
#     os.mkdir("plots")
#
# def makePlot(wavelength, region):
#     import plotly.express as px
#     region0R_red = df[df.wave_len == 560][['FrameCounter', 'Region0R']]
#     px.line(region0R_red, x='FrameCounter', y='Region0R')
#     fig = px.Figure()
#     fig.write_image("images/fig1.pdf")
#


# df = recs['PR2'][0]['photometry']


df = catsync
logs = catlogs
logs = logs.rename(columns={'SystemTimestamp':'Timestamp'})
window=5
frequency=10

# def perievents2(detrended, behavior, window, frequency):
    """
    produces perievent slices for each event in behavior
    :param detrended: df with 'Channel' as index and value columns
    :param behavior: behavior df with columns event and same index as df
    :param window: number of SECONDS to cut left and right off
    :param frequency: int, frequency of recording in Hz
    :return: perievent dataframe with additional indices event, timestamp and Trial
    """
channels = detrended.index.unique(level='Channel')

if 'Channel' not in behavior.index.names:  # make indices the same to intersect
    behavior['Channel'] = [list(channels)] * len(behavior)
    behavior = behavior.explode('Channel').set_index('Channel', append=True)
    behavior = behavior.swaplevel(-1, -2)
behavior = behavior.loc[detrended.index.intersection(behavior.index)]  # remove events that are not recorded

detrended = detrended.sort_index()
behavior['Trial'] = behavior.groupby(behavior.index.names[:-1]).cumcount()
peri = list()
timestamps = np.arange(-window, window + 1e-9, 1 / frequency)

# extract slice for each event and concat
for index, row in behavior.iterrows():
    start = index[:-1] + (index[-1] - window * frequency,)
    end = index[:-1] + (index[-1] + window * frequency,)

    single_event = detrended.loc[start:end]
    single_event[row.index] = row
    single_event['Timestamp'] = timestamps
    peri.append(single_event)  # Set on copy warning can be ignored because it is a copy anyways
peri = pd.concat(peri)

peri = peri.set_index(list(behavior.columns), append=True)
peri = peri.reset_index(['FrameCounter'], drop=True)
    # return peri





