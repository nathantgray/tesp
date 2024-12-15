#!/usr/bin/env python3
# Copyright (C) 2021-2023 Battelle Memorial Institute
# file: populate_feeder.py

import sys
import tesp_support.original.tesp_case as tc

tc.make_tesp_case(sys.argv[1])
