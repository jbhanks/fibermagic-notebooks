import pandas as pd
import numpy as np
from fibermagic.IO.NeurophotometricsIO import extract_leds
import os
import pathlib
from rudi_demodulate import *
from analysis_utils import *
import copy
from rudi_demodulate import demodulate as detrend
from fibermagic.core.perievents import perievents


def keep_newest_only(df_dict):
    from collections import defaultdict
    new = []
    df_dict = sorted(df_dict, key=lambda d: d['mouse'])
    grouped_data = defaultdict(list)
    for item in df_dict:
        grouped_data[item['mouse']].append(item)
    # Select the item with the maximum 'date' from each group
    new.append([max(group, key=lambda x: x['date']) for group in grouped_data.values()])
    return new[0]


def read_experiment(logfile):
    abspath = logfile.absolute()
    logs = pd.read_csv(abspath)
    logs.columns = ['ComputerTimestamp', 'SystemTimestamp', 'animal.ID', 'Event', 'pi.time', 'pc.time', 'datetimestamp']
    return logs

def get_one(mouse, logs):
    from dateutil.parser import parse
    mouse_log = logs[logs['animal.ID']==mouse]
    # Drop any empty dataframes
    if len(mouse_log)==0:
        return None
    # Make a dictionary for each animal for each experimental run including info about it and the data itself
    print("the dimensions of the log for ", mouse, " are ", mouse_log.shape )
    new_recording = dict(
        path = None,
        mouse = mouse,
        protocol = None,
        date = parse(logs.datetimestamp.iloc[0]),
        logs = mouse_log,
        photometry = None)
    return new_recording


def organize_logs(basepath, newest_only=True):
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
    return recordings


def get_photometry(recording):
    from fibermagic.IO.NeurophotometricsIO import extract_leds
    filepath = pathlib.Path(recording['path'] / 'photometry.csv')
    df = pd.read_csv(filepath)
    df = df.rename(columns={'R0':'Region0R','G1':'Region1G'})
    df = df.rename(columns={'Timestamp':'SystemTimestamp'})
    df = df[df.SystemTimestamp>=recording['logs'].iloc[0]['SystemTimestamp']]
    if 'Flags' in df.columns:  # legacy fix: Flags were renamed to LedState
        df = df.rename(columns={'Flags': 'LedState'})
    df = extract_leds(df).dropna()
    print("the final dimensions of the photometry for ", recording['mouse'], " are ", df.shape )
    recording['photometry'] = df
    return recording



def count_frames(df):
    # dirty hack to come around dropped frames until we find better solution -
    # it makes about 0.16 s difference
    #df = df.iloc[0:]
    df.FrameCounter = np.arange(0, len(df)) // len(df.wave_len.unique())
    df = df.set_index('FrameCounter')
    df.head(5)
    return df


# Convert to long format
def convert_to_long(df):
    NPM_RED = 560
    NPM_GREEN = 470
    NPM_ISO = 410
    regions = [column for column in df.columns if 'Region' in column]
    dfs = list()
    for region in regions:
        channel = NPM_GREEN if 'G' in region else NPM_RED
        sdf = pd.DataFrame(data={
            'Region': region,
            'Channel': channel,
            'Timestamp': df.SystemTimestamp[df.wave_len == channel],
            'Signal': df[region][df.wave_len == channel],
            'Reference': df[region][df.wave_len == NPM_ISO]
        }
        )
        dfs.append(sdf)
    df = pd.concat(dfs).reset_index().set_index('Region').dropna()
    return df

def synchronize_files(recording):
    behavior = recording['logs']
    photometry = recording['photometry']
    mouse = recording['mouse']
    df = recording['detrended']
    logs = logs.rename(columns={'SystemTimestamp':'Timestamp'})
    df = df.reset_index()
    logsG = pd.merge_asof(logs, df[df.Channel == 470], on="Timestamp", direction = "nearest")
    logsG = logsG[['Region', 'Channel', 'FrameCounter', 'Event', 'Timestamp', 'animal.ID']]
    logsR = pd.merge_asof(logs, df[df.Channel == 560], on="Timestamp", direction = "nearest")
    logsR = logsR[['Region', 'Channel', 'FrameCounter', 'Event', 'Timestamp', 'animal.ID']]
    photometry_synced = pd.concat([logsR, logsG], axis=0)
    photometry_synced = slogs.reset_index(drop=True).set_index(['Region', 'Channel', 'FrameCounter'])
    df = df.reset_index(drop=True).set_index(['Region', 'Channel', 'FrameCounter'])
    return df,photometry_synced
