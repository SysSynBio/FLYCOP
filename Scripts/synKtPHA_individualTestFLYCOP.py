#!/usr/bin/python3

# Running an individual test, for a particular consortium configuration given by arguments
#cp -p -R synKtPHA_TemplateOptimizeConsortiumV0 synKtPHA_TesttXX
#cd synKtPHA_TestXX
#python3 ../../Scripts/synKtPHA_individualTestFLYCOP.py 30 3.5 0.1 18 0.825 'MaxPHA'

import sys
import importlib
sys.path.append('../../Scripts')
import synKtPHAFLYCOP

sucrPer = float(sys.argv[1])
biomassSynecho = float(sys.argv[2])
biomassKT = float(sys.argv[3])
nh4 = float(sys.argv[4])
fitness = sys.argv[5]

#maxCycles = float(sys.argv[6])
maxCycles = 1000

synKtPHAFLYCOP.synKtPHAFLYCOP_oneConf(sucrPer,biomassSynecho,biomassKT,nh4,fitness,maxCycles,'./IndividualRunsResults/',1)
