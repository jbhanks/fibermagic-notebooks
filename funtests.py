def read_project_logs(project_path, subdirs, sync_fun=sync_from_TTL_gen, ignore_dirs=['meta']):
    """
    Merges all log files from a project into one
    :param ignore_dirs: list of directories to exclude from reading
    :param sync_fun: function to sync custom log files to NPM's FrameCounter
                     should return a df with 'Event' and 'Timestamp as columns
                     and 'FrameCounter' as Index
    :param subdirs:  name of subsequent directory levels to be included as columns
    :param project_path: project root path
    :return: Dataframe with logs in the following form:
                                  Event  Timestamp
    subdir[0] subdir[1] FrameCounter
    Trial 1   mouse A   345       LL         0.5
                        456       SI        0.56
                        8765      FD        0.57
              mouse B   567       ...         ...
    Trial 2   mouse A   765       ...
              mouse B   456
    ...       ...
    """
    dfs = list()

    def recursive_listdir(path, levels):
        import os
        if levels:
            for dir in os.listdir(path):
                if dir in ignore_dirs:
                    continue
                recursive_listdir(path / dir, levels - 1)
        else:
            region_to_mouse = pd.read_csv(path / 'region_to_mouse.csv')
            for mouse in region_to_mouse.mouse.unique():
                for file in os.listdir(path):
                    if '.log' in file and mouse in file:
                        logs = pd.read_csv(path / file)
                        logs = sync_fun(logs, path)
                        for i in range(len(subdirs)):
                            logs[subdirs[i]] = path.parts[- (len(subdirs) - i)]
                        logs['Mouse'] = mouse
                        dfs.append(logs)
    recursive_listdir(Path(project_path), len(subdirs))
    df = pd.concat(dfs)
    df = df.reset_index().set_index([*subdirs, 'Mouse', 'FrameCounter'])
    return df

def read_project_logs2(project_path, subdirs, sync_fun=sync_from_TTL_gen, ignore_dirs=['meta']):
    dfs = list()

    def recursive_listdir(path, levels):
        import os
        if levels:
            for dir in os.listdir(path):
                if dir in ignore_dirs:
                    continue
                recursive_listdir(path / dir, levels - 1)
        else:
            region_to_mouse = pd.read_csv(path / 'region_to_mouse.csv')
            for mouse in region_to_mouse.mouse.unique():
                for file in os.listdir(path):
                    if '.log' in file and mouse in file:
                        logs = pd.read_csv(path / file)
                        logs = sync_fun(logs, path)
                        for i in range(len(subdirs)):
                            logs[subdirs[i]] = path.parts[- (len(subdirs) - i)]
                        logs['Mouse'] = mouse
                        dfs.append(logs)
    recursive_listdir(Path(project_path), len(subdirs))
    df = pd.concat(dfs)
    df = df.reset_index().set_index([*subdirs, 'Mouse', 'FrameCounter'])
    return df


import os
from pathlib import Path
import pandas as pd
import numpy as np
from fibermagic.IO.NeurophotometricsIO import extract_leds
from fibermagic.IO.NeurophotometricsIO import read_project_logs, read_project_rawdata
from fibermagic.IO.NeurophotometricsIO import sync_from_TTL_gen

dfs = list()


basepath = '/home/jam/Downloads/NAcC gDA3m + rAdo1.3 FR20-PR/DATA/'
schedules = [dir for dir in os.listdir(basepath) if dir.startswith('PR')]
# print(schedules)
d = {schedule:([f for f in os.listdir(basepath + schedule) if f.startswith('B')]) for schedule in schedules}
schedule = schedules[0]
print('the schedule is', schedule)
id = d[schedule][0]
fullpath = basepath + schedule + '/' + id + '/'
filepath = fullpath + 'logs.csv'

# print(fullpath)

project_path = basepath
subdirs = [schedule]
sync_fun = 'sync_from_TTL_gen'
ignore_dirs = ['meta', 'processed', '.DS_Store']
project_path = Path('Processing')
print('the items in the path are', os.listdir(basepath + schedule))

path = Path(project_path)
levels = len(subdirs)


region_to_mouse = pd.read_csv(basepath + schedule + '/' + 'region_to_mouse.csv')
for mouse in region_to_mouse.mouse.unique():
    for file in os.listdir(fullpath):
        if '.log' in file:
            logs = pd.read_csv(fullpath + file)
            print(logs)
            logs2 = sync_from_TTL_gen(logs, Path(fullpath))
            for i in range(len(subdirs)):
                logs[subdirs[i]] = path.parts[- (len(subdirs) - i)]
            logs['Mouse'] = mouse
            dfs.append(logs)



logs = read_project_logs(basepath,
                                 [schedule], 'logs.csv', ignore_dirs=['meta', 'processed', '.DS_Store'])




# Each experiment should create a `logs.csv` and a `photometry.csv` file. These files should be in a folder named with the mice used in that run separated by a comma.
# For example if your ran mice M101 abd M105, the folder should be called `M101,M105` and contain `logs.csv` and `photometry.csv` and no other files or folders.
# Those folders should in turn be in folders named for the experimental protocol (for example `PR20` for progressive ratio 20).
# In the case where you have the same mouse ID repeated twice, all but the most recent trial will be dropped by default (`repeat_trials=False`). If you have an experiment where the same animal is used in multiple trials set `repeat_trials=True` and to each trial will be added a column `trial_number`, which will be generated according to the dates in the files.



##############
# def sync_from_TTL_gen(logs, path):
    """
    attaches Bonsai frame numbers to the the logs
    :param logs: log df with column SI@0.0
    :param sync_signals: df with timestamps of recorded sync signals from FP, columns Item1 and Item2
    :param timestamps: df with timestamp for each FP frame, columns Item1 and Item2
    :return: log file with new column Frame_Bonsai with FP frame number for each event
    """
sync_signals = pd.read_csv(filepath)
timestamps = pd.read_csv(path / 'time.csv')

logs['Event'] = logs['SI@0.0'].str.split('@').str.get(0)
logs['Timestamp'] = logs['SI@0.0'].str.split('@').str.get(1).astype(float)

# join FP SI with logs
sync_signals = sync_signals.drop('Item1', axis=1)
logs['Timestamp_Bonsai'] = sync_signals.loc[(logs.Timestamp // 1).astype(int)].reset_index(drop=True)

# convert Bonsai Timestamps to Frame number
logs['FrameCounter'] = timestamps.Item2.searchsorted(logs.Timestamp_Bonsai) // 3
logs = logs[['FrameCounter', 'Event', 'Timestamp']]
return logs.set_index('FrameCounter')


