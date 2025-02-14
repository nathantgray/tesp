# Copyright (C) 2021-2024 Battelle Memorial Institute
# See LICENSE file at https://github.com/pnnl/tesp
# file: schedule_server.py
"""Implements simple server for providing access to common data to many agents

This is a simple server that provides access to many commonly used data, 
typically in files on disk. Traditionally each software entity that needed
them would load the entire file from disk and store it for local use. In cases
where a large number of entities would be instantiated, storing all this data
in memory lead to an untenably large memory footprint. To solve this problem,
this simple server was implemented; it reads in the data from disk once and
provides two simple APIs for other entities to extract the data.



"""

import json
import numpy as np
import pandas as pd
from multiprocessing.managers import SyncManager

from .data import arguments

# Global for storing the data to be served
sch_df_dict = {}
cache_output = {}

#
# power_sch = ["pv_power", "../solar/auto_run/solar_pv_power_profiles/8-node_dist_hourly_forecast_power.csv"]
#

# # schedule files must be .csv
# schedule_dir = "../../../examples/analysis/dsot/data/schedule_df/"
# appliance_sch = ['responsive_loads', 'unresponsive_loads']
# wh_sch = ['small_1', 'small_2', 'small_3', 'small_4', 'small_5', 'small_6',
#           'large_1', 'large_2', 'large_3', 'large_4', 'large_5', 'large_6']
# comm_sch = ['retail_heating', 'retail_cooling', 'retail_lights', 'retail_plugs', 'retail_gas',
#             'retail_exterior', 'retail_occupancy',
#             'lowocc_heating', 'lowocc_cooling', 'lowocc_lights', 'lowocc_plugs', 'lowocc_gas',
#             'lowocc_exterior', 'lowocc_occupancy',
#             'office_heating', 'office_cooling', 'office_lights', 'office_plugs', 'office_gas',
#             'office_exterior', 'office_occupancy',
#             'alwaysocc_heating', 'alwaysocc_cooling', 'alwaysocc_lights', 'alwaysocc_plugs', 'alwaysocc_gas',
#             'alwaysocc_exterior', 'alwaysocc_occupancy',
#             'street_lighting'
#             ]
# copy_sch = ['constant','responsive_loads']


# Proxy class to be shared with different processes
# Don't put big data in here since that will force it to be piped to the
# other process when instantiated there, instead just return a portion of
# the global data when requested.
class DataProxy(object):
    def __init__(self):
        pass

    @staticmethod
    def forecasting_pv_schedules(name, time, window_length, col_num):
        """ Returns window length values of the given time for the name of schedule forecast and column

        Args:
            name (str): schedule name for data frame
            time (any): current time
            window_length (int): length of window
            col_num (int): column number 1 to n
        """
        idx = name + str(col_num)
        try:
            cache = cache_output[idx]
        except:
            cache_output[idx] = [0, 0]
            cache = cache_output[idx]

        if cache[0] != time:
            cache[0] = time
            cache[1] = sch_df_dict[name].loc[pd.date_range(time, periods=window_length, freq='H')]
        # print(name, " ", time)
        return cache[1][col_num]

    @staticmethod
    def forecasting_schedules(name, time, len_forecast):
        """ Returns len_forecast values from the given time as for the name schedule forecast

        Args:
            name (str): schedule name for data frame used to forecast
            time (any): current time at which DA optimization occurs
            len_forecast (int): length of forecast in hours
        """
        cache = cache_output[name]
        if cache[0] != time:
            dataframe = sch_df_dict[name]
            # First let's make sure that the year of time_begin is same as data frame and ignore seconds
            time_begin = time.replace(year=dataframe.index[0].year, second=0)
            time_stop = time_begin + pd.Timedelta(hours=len_forecast)
            # Now let's check if time_stop has gone to the next year
            if time_stop.year > time_begin.year:  # instead of next year, use the same year values
                temp = pd.concat([dataframe[time_begin:],
                                  dataframe[:time_stop.replace(year=dataframe.index[0].year)]])['data'].values
            elif time_stop.year == time_begin.year:  # if the window lies in the same year
                temp = dataframe[time_begin:time_stop]['data'].values
            else:
                raise UserWarning("Something is wrong with dates in forecasting_schedules function!!")
            cache[0] = time
            cache[1] = np.mean(temp[0:-1].reshape(-1, 60), axis=1)
            # print(name, " ", time)
        return cache[1]
    
    
    @staticmethod
    def read_tou_schedules(name, time, col_num):
        """ Returns tou price values of the given time for the name of schedule forecast and column

        Args:
            name (str): schedule name for data frame
            time (any): current time
            col_num (int): column number 1 to n
        """
        idx = name + str(col_num)
        try:
            cache = cache_output[idx]
        except:
            cache_output[idx] = [0, 0]
            cache = cache_output[idx]
        if cache[0] != time:
            cache[0] = time
            cache[1] = sch_df_dict[name].loc[pd.to_datetime(time)]
        return cache[1][col_num]


def schedule_server(config_file, port):

    with open(config_file, 'r', encoding='utf-8') as lp:
        ppc = json.load(lp)
    ppc = ppc["ScheduleServer"]
    schedule_dir = ppc["schedule_dir"]
    appliance_sch = ppc["appliance_sch"]
    wh_sch = ppc["wh_sch"]
    comm_sch = ppc["comm_sch"]
    copy_sch = ppc["copy_sch"]
    power_sch = ppc["power_sch"]
    tou_sch = ppc["tou_sch"]
    # port = ppc["port"]

    # load data frames schedules
    for sch in appliance_sch + wh_sch + comm_sch:
        sch_df_dict[sch] = pd.read_csv(schedule_dir + sch + '.csv', index_col=0)
        sch_df_dict[sch].index = pd.to_datetime(sch_df_dict[sch].index)
        cache_output[sch] = [0, 0]

    # create a data frame for constant schedule with all entries as 1.0. Copy it from any other data frame
    for cpy in copy_sch:
        sch = cpy[0]
        sch_df_dict[sch] = sch_df_dict[cpy[1]].copy(deep=True)
        sch_df_dict[sch]['data'] = 1.0
        cache_output[sch] = [0, 0]

    # create a data frame for PV, file format (time, pvpowerdso1, pvpowerdso2, pvpowerdso3, ... numdso)
    for ds in power_sch:
        sch = ds[0]
        sch_df_dict[sch] = pd.read_csv(ds[1], index_col=0, header=None)
        sch_df_dict[sch].index = pd.to_datetime(sch_df_dict[sch].index)
        cache_output[sch] = [0, 0]

    # create a data frame for tou rate schedule, file format (time, DSO_1 price, DSO_2 price, ...)
    for ds in tou_sch:
        sch = ds[0]
        sch_df_dict[sch] = pd.read_csv(ds[1], index_col=0, header=1)
        sch_df_dict[sch].index = pd.to_datetime(sch_df_dict[sch].index)
        cache_output[sch] = [0, 0]

    # start the server on address(host,port)
    print('Serving data. Press <ctrl>-c to stop.')

    class myManager(SyncManager):
        pass
    myManager.register('DataProxy', DataProxy)
    mgr = myManager(address=('', port), authkey=b'DataProxy01')
    server = mgr.get_server()
    server.serve_forever()


def main():
    error, args = arguments(description="Schedule server", args='ip')
    if error:
        return

    print('Schedule server metadata file: ', args.input_file[0])
    print('Schedule server port: ', args.port[0])
    schedule_server(args.input_file[0], int(args.port[0]))


if __name__ == '__main__':
    main()
