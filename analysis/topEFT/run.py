#!/usr/bin/env python
import lz4.frame as lz4f
import pickle
import json
import time
import cloudpickle
import gzip
import os
import argparse

import uproot
import numpy as np
from coffea import hist, processor
from coffea.nanoevents import NanoAODSchema

from topcoffea.modules.dataDrivenEstimation import DataDrivenProducer
import topeft

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='You can customize your run')
    parser.add_argument('jsonFiles'           , nargs='?', default=''           , help = 'Json file(s) containing files and metadata')
    parser.add_argument('--prefix', '-r'     , nargs='?', default=''           , help = 'Prefix or redirector to look for the files')
    parser.add_argument('--test','-t'       , action='store_true'  , help = 'To perform a test, run over a few events in a couple of chunks')
    parser.add_argument('--pretend'        , action='store_true'  , help = 'Read json files but, not execute the analysis')
    parser.add_argument('--nworkers','-n'   , default=8  , help = 'Number of workers')
    parser.add_argument('--chunksize','-s'   , default=100000  , help = 'Number of events per chunk')
    parser.add_argument('--nchunks','-c'   , default=None  , help = 'You can choose to run only a number of chunks')
    parser.add_argument('--outname','-o'   , default='plotsTopEFT', help = 'Name of the output file with histograms')
    parser.add_argument('--outpath','-p'   , default='histos', help = 'Name of the output directory')
    parser.add_argument('--treename'   , default='Events', help = 'Name of the tree inside the files')
    parser.add_argument('--do-errors', action='store_true', help = 'Save the w**2 coefficients')
    parser.add_argument('--do-systs', action='store_true', help = 'Run over systematic samples (takes longer)')
    parser.add_argument('--split-lep-flavor', action='store_true', help = 'Split up categories by lepton flavor')
    parser.add_argument('--skip-sr', action='store_true', help = 'Skip all signal region categories')
    parser.add_argument('--skip-cr', action='store_true', help = 'Skip all control region categories')
    parser.add_argument('--do-np', action='store_true', help = 'Perform nonprompt estimation on the output hist, and save a new hist with the np contribution included. Note that signal, background and data samples should all be processed together in order for this option to make sense.')
    parser.add_argument('--wc-list', action='extend', nargs='+', help = 'Specify a list of Wilson coefficients to use in filling histograms.')
    parser.add_argument('--hist-list', action='extend', nargs='+', help = 'Specify a list of histograms to fill.')
    
    args = parser.parse_args()
    jsonFiles        = args.jsonFiles
    prefix           = args.prefix
    dotest           = args.test
    nworkers         = int(args.nworkers)
    chunksize        = int(args.chunksize)
    nchunks          = int(args.nchunks) if not args.nchunks is None else args.nchunks
    outname          = args.outname
    outpath          = args.outpath
    pretend          = args.pretend
    treename         = args.treename
    do_errors        = args.do_errors
    do_systs         = args.do_systs
    split_lep_flavor = args.split_lep_flavor
    skip_sr          = args.skip_sr
    skip_cr          = args.skip_cr
    do_np            = args.do_np
    wc_lst           = args.wc_list if args.wc_list is not None else []

    # Figure out which hists to include
    if args.hist_list == ["ana"]:
        # Here we hardcode a list of hists used for the analysis
        hist_lst = ["njets","ht","ptbl"]
    else:
        # We want to specify a custom list
        # If we don't specify this argument, it will be None, and the processor will fill all hists 
        hist_lst = args.hist_list

    if dotest:
        nchunks = 2
        chunksize = 10000
        nworkers = 1
        print(f"Running a fast test with {nworkers:d} workers, {nchunks:d} chunks of {chunksize:d} events")

    ### Load samples from json
    samplesdict = {}
    allInputFiles = []

    def LoadJsonToSampleName(jsonFile, prefix):
        sampleName = jsonFile if not '/' in jsonFile else jsonFile[jsonFile.rfind('/')+1:]
        if sampleName.endswith('.json'):
            sampleName = sampleName[:-5]
        with open(jsonFile) as jf:
            samplesdict[sampleName] = json.load(jf)
            samplesdict[sampleName]['redirector'] = prefix

    if isinstance(jsonFiles, str) and ',' in jsonFiles:
        jsonFiles = jsonFiles.replace(' ', '').split(',')
    elif isinstance(jsonFiles, str):
        jsonFiles = [jsonFiles]

    for jsonFile in jsonFiles:
        if os.path.isdir(jsonFile):
            if not jsonFile.endswith('/'): jsonFile+='/'
            for f in os.path.listdir(jsonFile):
                if f.endswith('.json'): allInputFiles.append(jsonFile+f)
        else:
            allInputFiles.append(jsonFile)

    # Read from cfg files
    for f in allInputFiles:
        if not os.path.isfile(f):
            raise Exception(f'[ERROR] Input file {f} not found!')
        # This input file is a json file, not a cfg
        if f.endswith('.json'): 
            LoadJsonToSampleName(f, prefix)
        # Open cfg files
        else:
            with open(f) as fin:
                print(' >> Reading json from cfg file...')
                lines = fin.readlines()
                for l in lines:
                    if '#' in l:
                        l = l[:l.find('#')]
                    l = l.replace(' ', '').replace('\n', '')
                    if l == '': continue
                    if ',' in l:
                        l = l.split(',')
                        for nl in l:
                            if not os.path.isfile(l):
                                prefix = nl
                            else:
                                LoadJsonToSampleName(nl, prefix)
                    else:
                        if not os.path.isfile(l):
                            prefix = l
                        else:
                            LoadJsonToSampleName(l, prefix)

    flist = {};
    for sname in samplesdict.keys():
        redirector = samplesdict[sname]['redirector']
        flist[sname] = [(redirector+f) for f in samplesdict[sname]['files']]
        samplesdict[sname]['year'] = samplesdict[sname]['year']
        samplesdict[sname]['xsec'] = float(samplesdict[sname]['xsec'])
        samplesdict[sname]['nEvents'] = int(samplesdict[sname]['nEvents'])
        samplesdict[sname]['nGenEvents'] = int(samplesdict[sname]['nGenEvents'])
        samplesdict[sname]['nSumOfWeights'] = float(samplesdict[sname]['nSumOfWeights'])

        # Print file info
        is_data = 'YES' if samplesdict[sname]['isData'] else 'NO'
        print(f">> {sname}")
        print(f"   - isData?      : {is_data}")
        print(f"   - year         : {samplesdict[sname]['year']}")
        print(f"   - xsec         : {samplesdict[sname]['xsec']:f}")
        print(f"   - histAxisName : {samplesdict[sname]['histAxisName']}")
        print(f"   - options      : {samplesdict[sname]['options']}")
        print(f"   - tree         : {samplesdict[sname]['treeName']}")
        print(f"   - nEvents      : {samplesdict[sname]['nEvents']:d}")
        print(f"   - nGenEvents   : {samplesdict[sname]['nGenEvents']:d}")
        print(f"   - SumWeights   : {samplesdict[sname]['nSumOfWeights']:f}")
        print(f"   - Prefix       : {samplesdict[sname]['redirector']}")
        print(f"   - nFiles       : {len(samplesdict[sname]['files']):d}")
        for fname in samplesdict[sname]['files']:
            print(f"     {fname}")

    if pretend: 
        print('pretending...')
        exit() 

    # Extract the list of all WCs, as long as we haven't already specified one.
    if len(wc_lst) == 0:
        for k in samplesdict.keys():
            for wc in samplesdict[k]['WCnames']:
                if wc not in wc_lst:
                    wc_lst.append(wc)

    if len(wc_lst) > 0:
        # Yes, why not have the output be in correct English?
        if len(wc_lst) == 1:
            wc_print = wc_lst[0]
        elif len(wc_lst) == 2:
            wc_print = wc_lst[0] + ' and ' + wc_lst[1]
        else:
            wc_print = ', '.join(wc_lst[:-1]) + ', and ' + wc_lst[-1]
        print('Wilson Coefficients: {}.'.format(wc_print))
    else:
        print('No Wilson coefficients specified')
 
    processor_instance = topeft.AnalysisProcessor(samplesdict,
        wc_names_lst = wc_lst,
        hist_lst = hist_lst,
        do_errors = do_errors,
        do_systematics = do_systs,
        split_by_lepton_flavor = split_lep_flavor,
        skip_signal_regions = skip_sr,
        skip_control_regions = skip_cr
    )

    exec_args = {
        "schema": NanoAODSchema,
        "workers": nworkers
    }

    # Run the processor and get the output
    tstart = time.time()
    output = processor.run_uproot_job(flist,
        treename = treename,
        processor_instance = processor_instance,
        executor = processor.futures_executor,
        executor_args = exec_args,
        chunksize = chunksize,
        maxchunks = nchunks
    )
    dt = time.time() - tstart

    nbins = sum(sum(arr.size for arr in h._sumw.values()) for h in output.values() if isinstance(h, hist.Hist))
    nfilled = sum(sum(np.sum(arr > 0) for arr in h._sumw.values()) for h in output.values() if isinstance(h, hist.Hist))
    print(f"Filled {nbins:.0f} bins, nonzero bins: {100*nfilled/nbins:1.1f} %")
    print(f"Processing time: {dt:1.2f} s with {nworkers:d} ({dt*nworkers:.2f} s cpu overall)")

    # Save the output
    if not os.path.isdir(outpath):
        os.system(f"mkdir -p {outpath}")
    out_pkl_file = os.path.join(outpath,f"{outname}.pkl.gz")
    print(f"\nSaving output in {out_pkl_file}...")
    with gzip.open(out_pkl_file, "wb") as fout:
        cloudpickle.dump(output, fout)
    print("Done!")

    # Run the data driven estimation, save the output
    if do_np:
        print("\nDoing the nonprompt estimation...")
        out_pkl_file_np = os.path.join(outpath,f"{outname}_np.pkl.gz")
        ddp = DataDrivenProducer(out_pkl_file,out_pkl_file_np)
        print(f"Saving output in {out_pkl_file_np}...")
        ddp.dumpToPickle()
        print("Done!")
