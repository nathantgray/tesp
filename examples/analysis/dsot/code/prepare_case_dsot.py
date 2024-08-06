# Copyright (C) 2018-2023 Battelle Memorial Institute
# file: prepare_case_dsot.py
""" Sets up a simple DSO+T use-case with one feeder

Public Functions:
    None
"""

import os
import sys
import json
import shutil
import datetime
import numpy as np

from tesp_support.api.helpers import HelicsMsg

import tesp_support.dsot.helpers_dsot as helpers
import tesp_support.dsot.case_merge as cm
import tesp_support.dsot.glm_dictionary as gd

recs_data = False
#recs_data = True
if recs_data:
    rcs = "RECS"
    sys.path.append('../')
    import recs.commercial_feeder_glm as com_FG
    import recs.copperplate_feeder_glm as cp_FG
    import recs.residential_feeder_glm as res_FG
    import recs.prep_substation_recs as prep
    import pandas as pd
else:
    rcs = ""
    import tesp_support.original.commercial_feeder_glm as com_FG
    import tesp_support.original.copperplate_feeder_glm as cp_FG
    import tesp_support.dsot.residential_feeder_glm as res_FG
    import prep_substation_dsot as prep


# Simulation settings for the experimental case
def prepare_case(node, mastercase, pv=None, bt=None, fl=None, ev=None):

    # We need to load in the master metadata (*system_case_config.json)
    with open(mastercase + '.json', 'r', encoding='utf-8') as json_file:
        sys_config = json.load(json_file)

    # Get path for other data
    data_Path = sys_config['dataPath']
    case_type = sys_config['caseType']
    sys_config['market'] = False
    if pv is not None:
        case_type['pv'] = pv
        if pv > 0:
            sys_config['caseName'] = sys_config['caseName'] + "_pv"
    if bt is not None:
        case_type['bt'] = bt
        if bt > 0:
            sys_config['caseName'] = sys_config['caseName'] + "_bt"
            sys_config['market'] = True
    if fl is not None:
        case_type["fl"] = fl
        if fl > 0:
            sys_config['caseName'] = sys_config['caseName'] + "_fl"
            sys_config['market'] = True
    if ev is not None:
        case_type["ev"] = ev
        if ev > 0:
            sys_config['caseName'] = sys_config['caseName'] + "_ev"
            sys_config['market'] = True

    # loading default agent data
    with open(os.path.join(data_Path, sys_config['dsoAgentFile']), 'r', encoding='utf-8') as json_file:
        case_config = json.load(json_file)
        if recs_data:
            # Overwriting default_case_config.json
            case_config['FeederGenerator']['SolarPercentage'] = 11
            case_config['FeederGenerator']['StoragePercentage'] = 3
            case_config['FeederGenerator']['EVPercentage'] = 8
    # loading building and DSO metadata
    with open(os.path.join(data_Path, sys_config['dso' + rcs + 'PopulationFile']), 'r', encoding='utf-8') as json_file:
        dso_config = json.load(json_file)
    # loading residential metadata
    with open(os.path.join(data_Path, sys_config['dso' + rcs + 'ResBldgFile']), 'r', encoding='utf-8') as json_file:
        res_config = json.load(json_file)
    # loading commercial building metadata
    with open(os.path.join(data_Path, sys_config['dsoCommBldgFile']), 'r', encoding='utf-8') as json_file:
        comm_config = json.load(json_file)
    # loading battery metadata
    with open(os.path.join(data_Path, sys_config['dsoBattFile']), 'r', encoding='utf-8') as json_file:
        batt_config = json.load(json_file)
    # loading ev model metadata
    with open(os.path.join(data_Path, sys_config['dsoEvModelFile']), 'r', encoding='utf-8') as json_file:
        ev_model_config = json.load(json_file)
    # loading hvac set point metadata
    # record aggregated hvac_setpoint_data from survey:
    # In this implementation individual house set point schedule may not
    # make sense but aggregated behavior will do.
    with open(os.path.join(data_Path, sys_config['hvac' + rcs + 'SetPoint']), 'r', encoding='utf-8') as json_file:
        hvac_setpt = json.load(json_file)

    # print(json.dumps(sys_config, sort_keys = True, indent = 2))
    # print(json.dumps(dso_config, sort_keys = True, indent = 2))
    # print(json.dumps(case_config, sort_keys = True, indent = 2))
    # print(json.dumps(res_config, sort_keys = True, indent = 2))
    # print(json.dumps(comm_config, sort_keys = True, indent = 2))
    # print(json.dumps(batt_config, sort_keys = True, indent = 2))
    # print(json.dumps(ev_model_config, sort_keys = True, indent = 2))
    # print(json.dumps(hvac_setpt, sort_keys = True, indent = 2))

    port = str(sys_config['port'])
    caseName = sys_config['caseName']
    start_time = sys_config['StartTime']
    end_time = sys_config['EndTime']

    # setting Tmax in seconds
    ep = datetime.datetime(1970, 1, 1)
    s = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    e = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    sIdx = (s - ep).total_seconds()
    eIdx = (e - ep).total_seconds()
    sys_config['Tmax'] = int((eIdx - sIdx))

    dt = sys_config['dt']
    gen = sys_config['gen']
    genFuel = sys_config['genfuel']
    tso_config = sys_config['DSO']
    out_Path = sys_config['outputPath']

    sim = case_config['SimulationConfig']
    bldPrep = case_config['BuildingPrep']
    mktPrep = case_config['MarketPrep']
    weaPrep = case_config['WeatherPrep']
    weather_config = {}

    sim['CaseName'] = caseName
    sim['TimeZone'] = sys_config['TimeZone']
    sim['StartTime'] = start_time
    sim['EndTime'] = end_time
    sim['port'] = sys_config['port']
    sim['numCore'] = sys_config['numCore']
    sim['keyLoad'] = sys_config['keyLoad']
    # sim['players'] = sys_config['players']
    sim['caseType'] = sys_config['caseType']
    if 'Q_bid_forecast_correction' in list(sys_config.keys()):
        sim['Q_bid_forecast_correction'] = sys_config['Q_bid_forecast_correction']
    else:
        sim['Q_bid_forecast_correction'] = {"default": {"correct": False}}
    sim['agent_debug_mode'] = sys_config['agent_debug_mode']
    sim['metricsFullDetail'] = sys_config['metricsFullDetail']
    sim['simplifiedFeeders'] = sys_config['simplifiedFeeders']
    sim['OutputPath'] = sys_config['caseName']  # currently only used for the experiment management scripts
    sim['priceSensLoad'] = sys_config['priceSensLoad']
    sim['quadratic'] = sys_config['quadratic']
    sim['quadraticFile'] = sys_config['dsoQuadraticFile']
    
    # =================== fernando 2021/06/25 - removing 10 AM bid correction to AMES =======
    if case_type['fl'] == 1:
        print('Correction of DSO bid for 10 AM AMES bid is performed')
    else:
        sim['Q_bid_forecast_correction'] = {'default': sim['Q_bid_forecast_correction']['default']}
        print('NO 10 AM AMES bid correction')

    # We need to create the experiment folder. If it already exists, we delete it and then create it
    if caseName != "" and caseName != ".." and caseName != ".":
        if os.path.isdir(caseName):
            print("experiment folder already exists, deleting and moving on...")
            shutil.rmtree(caseName)
        os.makedirs(caseName)
        # copy system case config for this case
        with open(os.path.join(caseName, 'generate_case_config.json'), 'w', encoding='utf-8') as json_file:
            json.dump(sys_config, json_file, indent=2)
    else:
        print('Case name is blank or Case name is "." or ".." and could cause file deletion')
        exit(1)

    # We need to create the experiment out folder. If it already exists, we delete it and then create it
    if out_Path != "" and out_Path != ".." and out_Path != ".":
        if os.path.isdir(out_Path):
            print("experiment folder already exists, deleting and moving on...")
            shutil.rmtree(out_Path)
        os.makedirs(out_Path)
    else:
        out_Path = caseName

    # write player helics config json file for load and generator players
    helpers.write_players_msg(caseName, sys_config, dt)

    tso = HelicsMsg("pypower", dt)
    # config helics subs/pubs
    # Running renewables wind, solar
    if sys_config['genPower']:
        for i in range(len(gen)):
            if genFuel[i][0] in sys_config['renewables']:
                idx = str(genFuel[i][2])
                for plyr in ["genMn", "genForecastHr"]:
                    player = sys_config[plyr]
                    if player[6] and not player[8]:
                        tso.subs_n(player[0] + "player/" + player[0] + "_power_" + idx, "string")
                    if player[7] and not player[8]:
                        tso.subs_n(player[0] + "player/" + player[0] + "_pwr_hist_" + idx, "string")

    # Create empty list for glm dictionary files
    if recs_data:
        glm_dict_list = {}
        agent_dict_list = {}

    # First step is to create the dso folders and populate the feeders
    for dso_key, dso_val in dso_config.items():
        # print('dso ->', dso_key)
        # print('val ->', json.dumps(dso_val, sort_keys=True, indent=2))

        if 'DSO' not in dso_key:
            continue

        sub_key = dso_val['substation']
        bus = str(dso_val['bus_number'])
        # seed the random number here
        np.random.seed(dso_val['random_seed'])

        # write the tso published connections for this substation
        tso.pubs_n(False, "cleared_q_rt_" + bus, "string")
        tso.pubs_n(False, "cleared_q_da_" + bus, "string")
        tso.pubs_n(False, "lmp_rt_" + bus, "string")
        tso.pubs_n(False, "lmp_da_" + bus, "string")
        tso.pubs_n(False, "three_phase_voltage_" + bus, "string")

        # write the tso subscribe connections for this substation
        tso.subs_n("dso" + sub_key + "/rt_bid_" + bus, "string")
        tso.subs_n("dso" + sub_key + "/da_bid_" + bus, "string")

        try:
            # running reference load, using a player for the load reference for comparison
            player = sys_config['refLoadMn']
            if player[6] and player[8]:
                tso.subs_n(player[0] + "player/" + player[0] + "_load_" + bus, "string")
            if player[7] and player[8]:
                tso.subs_n(player[0] + "player/" + player[0] + "_ld_hist_" + bus, "string")
            if not dso_val['used']:
                # running reference load res and ind, (no gridlabd instance, using a player for the load)
                player = sys_config['gldLoad']
                if player[6] and player[8]:
                    tso.subs_n(player[0] + "player/" + player[0] + "_load_" + bus, "string")
                if player[7] and player[8]:
                    tso.subs_n(player[0] + "player/" + player[0] + "_ld_hist_" + bus, "string")
                continue
        except:
            pass

        os.makedirs(caseName + '/' + dso_key)

        # copy dso default config
        sim['DSO'] = dso_key
        sim[dso_key] = dso_val
        sim['CaseName'] = dso_key
        sim['Substation'] = sub_key
        sim['OutputPath'] = caseName + '/' + dso_key
        sim['BulkpowerBus'] = dso_val['bus_number']
        sim['DSO_type'] = dso_val['utility_type']
        if recs_data:
            sim['state'] = dso_val['state']
            sim['income_level'] = dso_val['income_level']
        sim['rooftop_pv_rating_MW'] = dso_val['rooftop_pv_rating_MW']
        sim['scaling_factor'] = dso_val['scaling_factor']
        sim['serverPort'] = 5150 + (int(bus) // 20)

        bldPrep['SolarDataPath'] = sys_config['solarDataPath']
        prefix = ''
        if node == 8:
            prefix = '8-node '
        bldPrep['SolarPPlayerFile'] = prefix + dso_key+'/'+dso_key+'_'+sys_config['solarPPlayerFile']
        bldPrep['SolarQPlayerFile'] = prefix + dso_key+'/'+dso_key+'_'+sys_config['solarQPlayerFile']
        # (Laurentiu Marinovici 11/18/2019) adding the residential metadata to case_config to be able to
        # eliminate the hardcoded path to the file in feederGenerator file
        bldPrep['MetaDataPath'] = "../data/"
        bldPrep['CommBldgMetaData'] = comm_config
        bldPrep['ResBldgMetaData'] = res_config
        bldPrep['BattMetaData'] = batt_config
        bldPrep['EvModelMetaData'] = ev_model_config
        bldPrep['EvDrivingDataFile'] = sys_config['dsoEvDrivingFile']
        bldPrep['ASHRAEZone'] = dso_val['ashrae_zone']

        # Following block is for AMES:
        PQ_val = [0, 0, 0, 0]
        for i in range(len(tso_config)):
            if bus == str(tso_config[i][0]):
                PQ_val = tso_config[i]
        mktPrep['DSO']['Bus'] = PQ_val[0]
        mktPrep['DSO']['Pnom'] = PQ_val[3]
        mktPrep['DSO']['Qnom'] = PQ_val[4]
        # This block now assigns scaling factors to each DSO
        mktPrep['DSO']['number_of_customers'] = dso_config[dso_key]['number_of_customers']
        mktPrep['DSO']['RCI customer count mix'] = dso_config[dso_key]['RCI customer count mix']
        mktPrep['DSO']['number_of_gld_homes'] = dso_config[dso_key]['number_of_gld_homes']

        # Weather is set per substation, with all feeders under the substation having the same weather profile
        # The values below need to refer to the DSO weather profile
        # The weather profile choice/name/path/source/coordinates should match
        # Coordinates (lat/long/) for solar gain calcs and such
        # NOTE: This can be misused
        weather_agent_name = 'weather_' + sub_key
        weaPrep['WeatherChoice'] = str.upper(os.path.splitext(dso_val['weather_file'])[1][1:])
        weaPrep['Name'] = weather_agent_name
        weaPrep['DataSource'] = dso_val['weather_file']
        weaPrep['Latitude'] = dso_val['latitude']
        weaPrep['Longitude'] = dso_val['longitude']
        weaPrep['TimeZoneOffset'] = dso_val['time_zone_offset']

        # could eliminate code here by changing helpers_dsot.py, since only one weather for DSO
        weather_config[weather_agent_name] = {
                'type': weaPrep['WeatherChoice'],
                'source': weaPrep['DataSource'],
                'latitude': weaPrep['Latitude'],
                'longitude': weaPrep['Longitude'],
                'time_zone_offset': weaPrep['TimeZoneOffset']}

        # make weather agent folder
        try:
            os.makedirs(caseName + '/' + weather_agent_name)
        except:
            pass

        # (Laurentiu Marinovici 11/07/2019)
        # we are going to copy the .dat file from its location into the weather agent folder
        shutil.copy(os.path.join(os.path.abspath(sys_config['WeatherDataSourcePath']), dso_val['weather_file']),
                    os.path.join(os.path.abspath(caseName), weather_agent_name, 'weather.dat'))

        # We need to generate the total population of commercial buildings by type and size
        num_res_customers = dso_val['number_of_gld_homes']
        num_comm_customers = round(num_res_customers * dso_val['RCI customer count mix']['commercial'] /
                                   dso_val['RCI customer count mix']['residential'])
        num_comm_bldgs = num_comm_customers / dso_val['comm_customers_per_bldg']
        comm_bldgs_pop = com_FG.define_comm_bldg(comm_config, dso_val['utility_type'], num_comm_bldgs)
        bldPrep['CommBldgPopulation'] = comm_bldgs_pop

        # print(json.dumps(comm_bldgs_pop, sort_keys = True, indent = 2))
        print("\n!!!!! Initially, there are {0:d} commercial buildings !!!!!".format(
            len(bldPrep['CommBldgPopulation'].keys())))

        # write out a configuration for each substation
        # WARNING!!!!! some fields in case_config are changed, yet not saved to the file,
        # in the subsequent part that processes each feeder;
        # the reason is the way the code was written for feeder generator
        # when only one feeder was expected
        with open(caseName + '/case_config_' + str(dso_val['bus_number']) + '.json', 'w') as outfile:
            json.dump(case_config, outfile, ensure_ascii=False, indent=2)

        HelicsMsg.gld = HelicsMsg("gld" + case_config['SimulationConfig']['Substation'], 30)
        HelicsMsg.dso = HelicsMsg("dso" + case_config['SimulationConfig']['Substation'], dt)
        HelicsMsg.dso.config("uninterruptible", True)
        feeders = dso_val['feeders']
        feedercnt = 1
        for feed_key, feed_val in feeders.items():
            print("\t<<<<< Chosen feeder -->> {0} >>>>>".format(feed_val['name']))
            if sim['simplifiedFeeders']:
                feed_val['name'] = 'sim_' + feed_val['name']
                print("\t<<<<< Going with the simplified feeders. >>>>>")
                print("\t<<<<< Feeder name changed to -->> {0} >>>>>".format(feed_val['name']))
            else:
                print("\t<<<<< Going with the full feeders. >>>>>")
            os.makedirs(caseName + '/' + feed_key)
            sim['OutputPath'] = caseName + '/' + feed_key
            sim['CaseName'] = feed_key
            case_config['BackboneFiles']['TaxonomyChoice'] = feed_val['name']
            res_FG.populate_feeder(config=case_config)

            # Then we want to create a JSON dictionary with the Feeder information
            gd.glm_dict(caseName + '/' + feed_key + '/' + feed_key, config=case_config,
                        ercot=sim['simplifiedFeeders'])
            shutil.move(caseName + '/' + feed_key + '/' + feed_key + '_glm_dict.json',
                        caseName + '/' + dso_key + '/' + feed_key + '_glm_dict.json')

            # Next we create the agent dictionary along with the substation YAML file
            if recs_data:
                prep.prep_substation(caseName + '/' + feed_key + '/' + feed_key,
                                     caseName + '/' + dso_key + '/' + feed_key,
                                     caseName + '/' + weather_agent_name + '/',
                                     feedercnt,
                                     config=case_config,
                                     hvacSetpt=hvac_setpt,
                                     Q_forecast=sim['Q_bid_forecast_correction'],
                                     Q_dso_key=dso_key,
                                     usState = sim['state'],
                                     dsoType = dso_val['utility_type'])
            else:
                prep.prep_substation(caseName + '/' + feed_key + '/' + feed_key,
                                     caseName + '/' + dso_key + '/' + feed_key,
                                     caseName + '/' + weather_agent_name + '/',
                                     feedercnt,
                                     config=case_config,
                                     hvacSetpt=hvac_setpt,
                                     Q_forecast=sim['Q_bid_forecast_correction'],
                                     Q_dso_key=dso_key)
            feedercnt += 1
            print("=== DONE WITH FEEDER {0:s} for {1:s}. ======\n".format(feed_key, dso_key))

        # =================== Laurentiu Marinovici 12/13/2019 - Copperplate feeder piece =======
        if sim["CopperplateFeeder"]:
            print("!!!!! There are {0:d} / {1:d} commercial buildings left !!!!!".format(
                len(bldPrep['CommBldgPopulation'].keys()), len(comm_bldgs_pop)))
            if len(bldPrep['CommBldgPopulation'].keys()) > 0:
                print("!!!!! We are going with the copperplate feeder now. !!!!!")
                feed_key = "copperplate_feeder"
                feed_val['name'] = feed_key
                dso_val['feeders'][feed_key] = feed_val
                os.makedirs(caseName + '/' + feed_key)
                sim['OutputPath'] = caseName + '/' + feed_key
                sim['CaseName'] = feed_key
                case_config['BackboneFiles']['TaxonomyChoice'] = sim['CopperplateFeederName']
                case_config['BackboneFiles']['CopperplateFeederFile'] = sim['CopperplateFeederFile']
                cp_FG.populate_feeder(config=case_config)

                gd.glm_dict(caseName + '/' + feed_key + '/' + feed_key, config=case_config,
                            ercot=sim['simplifiedFeeders'])
                shutil.move(caseName + '/' + feed_key + '/' + feed_key + '_glm_dict.json',
                            caseName + '/' + dso_key + '/' + feed_key + '_glm_dict.json')

                # Next we create the agent dictionary along with the substation YAML file
                if recs_data:
                    prep.prep_substation(caseName + '/' + feed_key + '/' + feed_key,
                                         caseName + '/' + dso_key + '/' + feed_key,
                                         caseName + '/' + weather_agent_name + '/',
                                         feedercnt,
                                         config=case_config,
                                         hvacSetpt=hvac_setpt,
                                         Q_forecast=sim['Q_bid_forecast_correction'],
                                         Q_dso_key=dso_key,
                                         usState = sim['state'],
                                         dsoType = dso_val['utility_type'])
                else:
                    prep.prep_substation(caseName + '/' + feed_key + '/' + feed_key,
                                         caseName + '/' + dso_key + '/' + feed_key,
                                         caseName + '/' + weather_agent_name + '/',
                                         feedercnt,
                                         config = case_config,
                                         hvacSetpt = hvac_setpt,
                                         Q_forecast = sim['Q_bid_forecast_correction'],
                                         Q_dso_key = dso_key)
                feedercnt += 1
                print("=== DONE WITH COPPERPLATE FEEDER {0:s} for {1:s}. ======\n".format(feed_key, dso_key))

        # ======================================================================================
        print("\n=== MERGING THE FEEDERS UNDER ONE SUBSTATION =====")
        os.makedirs(caseName + "/" + sub_key)
        cm.merge_glm(os.path.abspath(caseName + '/' + sub_key + '/' + sub_key + '.glm'), list(dso_val['feeders'].keys()), 20)

        print("\n=== MERGING/WRITING THE SUBSTATION(GRIDLABD) MESSAGE FILE =====")
        HelicsMsg.gld.write_file(os.path.abspath(caseName + '/' + sub_key + '/' + sub_key + '.json'))

        print("\n=== MERGING/WRITING THE FEEDERS GLM DICTIONARIES =====")
        cm.merge_glm_dict(os.path.abspath(caseName + '/' + dso_key + '/' + sub_key + '_glm_dict.json'), list(dso_val['feeders'].keys()), 20)
        if recs_data:
            glm_dict_list[dso_key] = os.path.abspath(caseName + '/' + dso_key + '/' + sub_key + '_glm_dict.json')

        print("\n=== MERGING/WRITING THE SUBSTATION AGENT DICTIONARIES =====")
        cm.merge_agent_dict(os.path.abspath(caseName + '/' + dso_key + '/' + sub_key + '_agent_dict.json'), list(dso_val['feeders'].keys()))
        if recs_data:
            agent_dict_list[dso_key] = os.path.abspath(caseName + '/' + dso_key + '/' + sub_key + '_agent_dict.json')

        print("\n=== MERGING/WRITING THE DSO MESSAGE FILE =====")
        HelicsMsg.dso.write_file(os.path.abspath(caseName + '/' + dso_key + '/' + sub_key + '.json'))

        # cleaning after feeders had been merged
        foldersToDelete = [name for name in os.listdir(os.path.abspath(caseName))
                           if os.path.isdir(os.path.join(os.path.abspath(caseName), name)) and 'feeder' in name]
        print("=== Removing the following folders: {0}. ===".format(foldersToDelete))
        [shutil.rmtree(os.path.join(os.path.abspath(caseName), folder)) for folder in foldersToDelete]

        # for dso_key, dso_val in substation_config.items():
        filesToDelete = [name for name in os.listdir(os.path.abspath(caseName + '/' + dso_key))
                         if os.path.isfile(os.path.join(os.path.abspath(caseName + '/' + dso_key), name)) and 'feeder' in name]
        print("=== Removing the following files: {0} for {1}. ===".format(filesToDelete, dso_key))
        [os.remove(os.path.join(os.path.abspath(caseName + '/' + dso_key), fileName)) for fileName in filesToDelete]

    # Residential population summary
    if recs_data:
        hse_df = pd.DataFrame()
        hvac_agent_df = pd.DataFrame()
        # Get house parameters from each DSO glm_dict
        for dso_k, f_str in glm_dict_list.items():
            with open(f_str) as f:
                glm_dict = json.load(f)
            temp_df = pd.DataFrame.from_dict(glm_dict['houses'],orient='index')
            temp_df = temp_df.reset_index()
            temp_df['DSO'] = dso_k # add a column for DSO number
            # Add columns to distinguish houses and each DER
            for inc in ['Low', 'Middle', 'Upper']:
                for k, v in {'house':inc,'battery':'bat','solar':'sol','ev':'ev'}.items():
                    for val in glm_dict['billingmeters'].values():
                        children = val['children']
                        if len([s for s in children if inc in s]) > 0:
                            if len([s for s in children if v in s]) > 0:
                                temp_df.loc[temp_df['index']==[s for s in children if inc in s][0],k] = 'Yes'
                            else:
                                temp_df.loc[temp_df['index']==[s for s in children if inc in s][0],k] = 'No'
            # Merge all DSO house parameters into one dataframe
            hse_df = pd.concat([hse_df,temp_df],ignore_index=True)
        # Get HVAC agent data
        for dso_k, f_str in agent_dict_list.items():
            with open(f_str) as f:
                agent_dict = json.load(f)
            temp_df2 = pd.DataFrame.from_dict(agent_dict['hvacs'],orient='index')
            temp_df2 = temp_df2.reset_index()
            temp_df2['DSO'] = dso_k # add a column for DSO number
            hvac_agent_df = pd.concat([hvac_agent_df,temp_df2],ignore_index=True)
        # Save for later analysis
        hse_df.to_csv(os.path.abspath(caseName + '/' + 'house_parameters.csv'))
        hvac_agent_df.to_csv(os.path.abspath(caseName + '/' + 'hvac_agents.csv'))
        # Get totals
        tot_hses = len(hse_df.loc[hse_df['house']=='Yes'])
        low_hses = len(hse_df.loc[(hse_df['income_level']=='Low')])
        middle_hses = len(hse_df.loc[(hse_df['income_level']=='Middle')])
        upper_hses = len(hse_df.loc[(hse_df['income_level']=='Upper')])
        sol_hses = len(hse_df.loc[(hse_df['house']=='Yes') & (hse_df['solar']=='Yes')])
        ev_hses = len(hse_df.loc[(hse_df['house']=='Yes') & (hse_df['ev']=='Yes')])
        bat_hses = len(hse_df.loc[(hse_df['house']=='Yes') & (hse_df['battery']=='Yes')])
        elec_wh_hses = len(hse_df.loc[(hse_df['house']=='Yes') & (hse_df['wh_gallons']!=0)])
        elec_sh_hses = len(hse_df.loc[(hse_df['house']=='Yes') & (hse_df['fuel_type']=='electric')])
        print(f"=== RESIDENTIAL POPULATION SUMMARY ===")
        print(f"=== Income (Percent of all homes) ===")
        print(f"=== Low: {round(100*low_hses/tot_hses,2)}%, Middle: {round(100*middle_hses/tot_hses,2)}%, Upper: {round(100*upper_hses/tot_hses,2)}%. ===")
        print(f"=== DERs (Percent of all homes) ===")
        print(f"=== Solar: {round(100*sol_hses/tot_hses,2)}%, EVs: {round(100*ev_hses/tot_hses,2)}%, Batteries: {round(100*bat_hses/tot_hses,2)}%. ===")
        print(f"=== Electric Water Heating/Space Heating (Percent of all homes) ===")
        print(f"=== Water Heating: {round(100*elec_wh_hses/tot_hses,2)}%, Space Heating: {round(100*elec_sh_hses/tot_hses,2)}%. ===")
    tso.write_file(caseName + '/tso_h.json')

    # Also create the launch, kill and clean scripts for this case
    helpers.write_dsot_management_script(master_file="generate_case_config",
                                         case_path=caseName,
                                         system_config=sys_config,
                                         substation_config=dso_config,
                                         weather_config=weather_config)


if __name__ == "__main__":
    if len(sys.argv) > 6:
        prepare_case(int(sys.argv[1]), sys.argv[2], pv=int(sys.argv[3]), bt=int(sys.argv[4]), fl=int(sys.argv[5]), ev=int(sys.argv[6]))
    else:
        # prepare_case(8, "8_system_case_config", pv=0, bt=0, fl=0, ev=0)
        # prepare_case(8, "8_system_case_config", pv=0, bt=1, fl=0, ev=0)
        # prepare_case(8, "8_system_case_config", pv=0, bt=0, fl=1, ev=0)
        # prepare_case(8, "8_hi_system_case_config", pv=1, bt=0, fl=0, ev=0)
        # prepare_case(8, "8_hi_system_case_config", pv=1, bt=1, fl=0, ev=1)
        prepare_case(8, "8_hi_system_case_config", pv=1, bt=0, fl=1, ev=1)
        prepare_case(8, "8_hi_system_case_config", pv=1, bt=1, fl=1, ev=1)
        prepare_case(8, "8_hi_system_case_config", pv=1, bt=0, fl=1, ev=0)
        # prepare_case(8, "8_hi_system_case_config", pv=1, bt=1, fl=0, ev=0)
        # prepare_case(8, "8_hi_system_case_config", pv=1, bt=0, fl=0, ev=1)

        # prepare_case(200, "200_system_case_config", pv=0, bt=0, fl=0, ev=0)
        # prepare_case(200, "200_system_case_config", pv=0, bt=1, fl=0, ev=0)
        # prepare_case(200, "200_system_case_config", pv=0, bt=0, fl=1, ev=0)
        # prepare_case(200, "200_hi_system_case_config", pv=1, bt=0, fl=0, ev=0)
        # prepare_case(200, "200_hi_system_case_config", pv=1, bt=1, fl=0, ev=1)
        # prepare_case(200, "200_hi_system_case_config", pv=1, bt=0, fl=1, ev=1)
