def perievents2(detrended, behavior, window, frequency):
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
    return peri
