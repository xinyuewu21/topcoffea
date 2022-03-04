#This script plots the two histograms for the charge flip measurement
#To create the histograms run topeft with work_queue_run.py with the --split-lep-flavor option (can also do --skip-sr and skip all hists but invmass)
#Should run over DY mc samples
#make sure the output of the script is in histos/plotsTopEFT.pkl.gz

from __future__ import print_function, division
from collections import defaultdict, OrderedDict
import gzip
import pickle
import json
import os
import uproot
import matplotlib.pyplot as plt
import numpy as np
from coffea import hist, processor 
from coffea.hist import plot
import os, sys
import uproot3
import topcoffea.modules.GetValuesFromJsons as getVal

from topcoffea.plotter.plotter import plotter

import argparse
parser = argparse.ArgumentParser(description='You can customize your run')
parser.add_argument('--filepath','-i'   , default='histos/plotsTopEFT.pkl.gz', help = 'path of file with histograms')
#This is the output of the script. It is hardcoded to a web area. Use command line option to change
parser.add_argument('--outpath','-p'   , default='../../../../www/chargeflip', help = 'Name of the output directory')
args = parser.parse_args()

path = args.filepath

with gzip.open(path) as fin:
  hin = pickle.load(fin)
  hists = ['invmass']
  for thing in hists:
    fig, ax = plt.subplots(1, 1, figsize=(7,7))
    h = hin[thing]
    h = h.sum("appl")
    h = h.sum("systematic")
    hOS = h.integrate("channel", ["2los_ee_CRZ_0j"])
    hSS = h.integrate("channel", ["2lss_ee_CRZ_0j"])
    hOS.scale(1000*getVal.get_lumi("2018"))
    hSS.scale(1000*getVal.get_lumi("2018"))
    hist.plot1d(hOS, overlay="sample", ax=ax, clear=False, density=False)
    hist.plot1d(hSS, overlay="sample", ax=ax, clear=False, density=False)
    fig.savefig(os.path.join(args.outpath, thing))
    hOS = hOS.sum("sample")
    hSS = hSS.sum("sample")
    fout = uproot3.create('new_output.root')
    fout['OS_invmass'] = hist.export1d(hOS)
    fout['SS_invmass'] = hist.export1d(hSS)
    fout.close()
