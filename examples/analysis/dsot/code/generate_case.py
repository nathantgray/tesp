# Copyright (C) 2019-2023 Battelle Memorial Institute
# file: generate_case.py
""" Utility function to split a year run to monthly runs. This is DSO+T specific helper functions
"""

import json
import prepare_case_dsot as prep_case


def generate_case(case_name, port, pv=None, bt=None, fl=None, ev=None):

    with open(case_name + '.json', 'r', encoding='utf-8') as json_file:
        ppc = json.load(json_file)
    split_case = ppc['splitCase']
    case_start_year = ppc['caseStartYear']
    case_end_year = ppc['caseEndYear']

    if split_case:
        while True:
            for i in range(12):
                directory_name = str(case_start_year) + "_" + '{0:0>2}'.format(i+1)
                ppc['caseName'] = node + "_" + directory_name
                ppc['port'] = int(port + i)

                year = case_start_year
                month = '{0:0>2}'.format(i)
                daytime = "-29 00:00:00"
                if i == 0:
                    daytime = "-01 00:00:00"
                    month = '01'
                ppc['StartTime'] = str(year) + "-" + month + daytime

                year = case_start_year
                month = '{0:0>2}'.format(i+2)
                daytime = "-01 00:00:00"
                if i == 11:
                    daytime = "-30 00:00:00"
                    month = '12'
                ppc['EndTime'] = str(year) + "-" + month + daytime

                with open("generate_case_config.json", 'w') as outfile:
                    json.dump(ppc, outfile, indent=2)
                prep_case.prepare_case(int(node), "generate_case_config", pv=pv, bt=bt, fl=fl, ev=ev)

            if case_start_year == case_end_year:
                break
            case_start_year += 1


node = "8"
# node = "200"

generate_case(node + "_system_case_config", 5570, pv=1, bt=1, fl=1, ev=1)
# generate_case(node + "_system_case_config", 5570, pv=0, bt=0, fl=0, ev=0)
# generate_case(node + "_system_case_config", 5570, pv=0, bt=1, fl=0, ev=0)
# generate_case(node + "_system_case_config", 5570, pv=0, bt=0, fl=1, ev=0)
# generate_case(node + "_hi_system_case_config", 5570, pv=1, bt=0, fl=0, ev=0)
# generate_case(node + "_hi_system_case_config", 5570, pv=1, bt=1, fl=0, ev=1)
# generate_case(node + "_hi_system_case_config", 5570, pv=1, bt=0, fl=1, ev=1)
