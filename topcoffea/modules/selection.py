'''
 selection.py

 This script contains several functions that implement the some event selection. 
 The functinos defined here can be used to define a selection, signal/control region, etc.
 The functions are called with (jagged)arrays as imputs plus some custom paramenters and return a boolean mask.

'''

import numpy as np
import awkward as ak

from topcoffea.modules.corrections import fakeRateWeight2l, fakeRateWeight3l


# The datasets we are using, and the triggers in them
dataset_dict = {

    "2016" : {
        "SingleMuon" : [
            "IsoMu24",
            "IsoMu27",
        ],
        "SingleElectron" : [
            'Ele27_WPTight_Gsf'
        ],
        "DoubleMuon" : [
            "Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ",
            "TripleMu_12_10_5",
        ],
        "DoubleEG" : [
            "Ele23_Ele12_CaloIdL_TrackIdL_IsoVL",
            "Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ",
            "Ele16_Ele12_Ele8_CaloIdL_TrackIdL",
        ],
        "MuonEG" : [
            "Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL",
            "Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ",
            "Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ",
            "Mu8_DiEle12_CaloIdL_TrackIdL",
            "DiMu9_Ele9_CaloIdL_TrackIdL",
        ]
    },

    "2017" : {
        "SingleMuon" : [
            "IsoMu24",
            "IsoMu27",
        ],
        "SingleElectron" : [
            "Ele32_WPTight_Gsf",
            "Ele35_WPTight_Gsf",
        ],
        "DoubleMuon" : [
            "Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ",
            "Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8",
            "TripleMu_12_10_5",
        ],
        "DoubleEG" : [
            "Ele23_Ele12_CaloIdL_TrackIdL_IsoVL",
            "Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ",
            "Ele16_Ele12_Ele8_CaloIdL_TrackIdL",
        ],
        "MuonEG" : [
            "Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL",
            "Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ",
            "Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ",
            "Mu8_DiEle12_CaloIdL_TrackIdL",
            "Mu8_DiEle12_CaloIdL_TrackIdL_DZ", # Note: Listed in Andrew's thesis, but not TOP-19-001 AN
            "DiMu9_Ele9_CaloIdL_TrackIdL_DZ",
        ]
    },

    "2018" : {
        "SingleMuon" : [
            "IsoMu24",
            "IsoMu27",
        ],
        "EGamma" : [
            "Ele32_WPTight_Gsf",
            "Ele35_WPTight_Gsf",
        ],
        "DoubleMuon" : [
            "Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ",
            "Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8",
            "TripleMu_12_10_5",
        ],
        "DoubleEG" : [
            "Ele23_Ele12_CaloIdL_TrackIdL_IsoVL",
            "Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ",
            "Ele16_Ele12_Ele8_CaloIdL_TrackIdL",
        ],
        "MuonEG" : [
            "Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL",
            "Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ",
            "Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ",
            "Mu8_DiEle12_CaloIdL_TrackIdL",
            "Mu8_DiEle12_CaloIdL_TrackIdL_DZ",
            "DiMu9_Ele9_CaloIdL_TrackIdL_DZ",
        ]
    }

}


# Hard coded dictionary for figuring out overlap...
#   - No unique way to do this
#   - Note: In order for this to work properly, you should be processing all of the datastes to be used in the analysis
#   - Otherwise, you may be removing events that show up in other datasets you're not using
exclude_dict = {
    "2016": {
        "DoubleMuon"     : [],
        "DoubleEG"       : dataset_dict["2016"]["DoubleMuon"],
        "MuonEG"         : dataset_dict["2016"]["DoubleMuon"] + dataset_dict["2016"]["DoubleEG"],
        "SingleMuon"     : dataset_dict["2016"]["DoubleMuon"] + dataset_dict["2016"]["DoubleEG"] + dataset_dict["2016"]["MuonEG"],
        "SingleElectron" : dataset_dict["2016"]["DoubleMuon"] + dataset_dict["2016"]["DoubleEG"] + dataset_dict["2016"]["MuonEG"] + dataset_dict["2016"]["SingleMuon"],
    },
    "2017": {
        "DoubleMuon"     : [],
        "DoubleEG"       : dataset_dict["2017"]["DoubleMuon"],
        "MuonEG"         : dataset_dict["2017"]["DoubleMuon"] + dataset_dict["2017"]["DoubleEG"],
        "SingleMuon"     : dataset_dict["2017"]["DoubleMuon"] + dataset_dict["2017"]["DoubleEG"] + dataset_dict["2017"]["MuonEG"],
        "SingleElectron" : dataset_dict["2017"]["DoubleMuon"] + dataset_dict["2017"]["DoubleEG"] + dataset_dict["2017"]["MuonEG"] + dataset_dict["2017"]["SingleMuon"],
    },
    "2018": {
        "DoubleMuon"     : [],
        "EGamma"         : dataset_dict["2018"]["DoubleMuon"],
        "MuonEG"         : dataset_dict["2018"]["DoubleMuon"] + dataset_dict["2018"]["EGamma"],
        "SingleMuon"     : dataset_dict["2018"]["DoubleMuon"] + dataset_dict["2018"]["EGamma"] + dataset_dict["2018"]["MuonEG"],
    },
}


# This is a helper function called by trgPassNoOverlap
#   - Takes events objects, and a lits of triggers
#   - Returns an array the same length as events, elements are true if the event passed at least one of the triggers and false otherwise
def passesTrgInLst(events,trg_name_lst):
    tpass = np.zeros_like(np.array(events.MET.pt), dtype=np.bool)
    trg_info_dict = events.HLT

    # "fields" should be list of all triggers in the dataset
    common_triggers = set(trg_info_dict.fields) & set(trg_name_lst)

    # Check to make sure that at least one of our specified triggers is present in the dataset
    if len(common_triggers) == 0 and len(trg_name_lst):
        raise Exception("No triggers from the sample matched to the ones used in the analysis.")

    for trg_name in common_triggers:
        tpass = tpass | trg_info_dict[trg_name]
    return tpass

# This is what we call from the processor
#   - Returns an array the len of events
#   - Elements are false if they do not pass any of the triggers defined in dataset_dict
#   - In the case of data, events are also false if they overlap with another dataset
def trgPassNoOverlap(events,is_data,dataset,year):
    
    # The trigger for 2016 and 2016APV are the same
    if year == "2016APV":
        year = "2016"

    # Initialize ararys and lists, get trg pass info from events
    trg_passes    = np.zeros_like(np.array(events.MET.pt), dtype=np.bool) # Array of False the len of events
    trg_overlaps  = np.zeros_like(np.array(events.MET.pt), dtype=np.bool) # Array of False the len of events
    trg_info_dict = events.HLT
    full_trg_lst  = []

    # Get the full list of triggers in all datasets
    for dataset_name in dataset_dict[year].keys():
        full_trg_lst = full_trg_lst + dataset_dict[year][dataset_name]

    # Check if events pass any of the triggers
    trg_passes = passesTrgInLst(events,full_trg_lst)

    # In case of data, check if events overlap with other datasets
    if is_data:
        trg_passes = passesTrgInLst(events,dataset_dict[year][dataset])
        trg_overlaps = passesTrgInLst(events, exclude_dict[year][dataset])

    # Return true if passes trg and does not overlap
    return (trg_passes & ~trg_overlaps)


# 2l selection (we do not make the ss requirement here)
def add2lMaskAndSFs(events, year, isData, sampleType):

    # FOs and padded FOs
    FOs = events.l_fo_conept_sorted
    padded_FOs = ak.pad_none(FOs,2)

    # Filters and cleanups
    filter_flags = events.Flag
    filters = filter_flags.goodVertices & filter_flags.globalSuperTightHalo2016Filter & filter_flags.HBHENoiseFilter & filter_flags.HBHENoiseIsoFilter & filter_flags.EcalDeadCellTriggerPrimitiveFilter & filter_flags.BadPFMuonFilter & ((year == "2016") | filter_flags.ecalBadCalibFilter) & (isData | filter_flags.eeBadScFilter)
    cleanup = events.minMllAFAS > 12
    muTightCharge = ((abs(padded_FOs[:,0].pdgId)!=13) | (padded_FOs[:,0].tightCharge>=1)) & ((abs(padded_FOs[:,1].pdgId)!=13) | (padded_FOs[:,1].tightCharge>=1))

    # Zee veto
    Zee_veto = (abs(padded_FOs[:,0].pdgId) != 11) | (abs(padded_FOs[:,1].pdgId) != 11) | ( abs ( (padded_FOs[:,0]+padded_FOs[:,1]).mass -91.2) > 10)

    # IDs
    eleID1 = (abs(padded_FOs[:,0].pdgId)!=11) | ((padded_FOs[:,0].convVeto != 0) & (padded_FOs[:,0].lostHits==0) & (padded_FOs[:,0].tightCharge>=2))
    eleID2 = (abs(padded_FOs[:,1].pdgId)!=11) | ((padded_FOs[:,1].convVeto != 0) & (padded_FOs[:,1].lostHits==0) & (padded_FOs[:,1].tightCharge>=2))

    # 2l requirements:
    exclusive = ak.num( FOs[FOs.isTightLep],axis=-1)<3
    dilep = (ak.num(FOs)) >= 2
    pt2515 = (ak.any(FOs[:,0:1].conept > 25.0, axis=1) & ak.any(FOs[:,1:2].conept > 15.0, axis=1))
    mask = (filters & cleanup & dilep & pt2515 & exclusive & Zee_veto & eleID1 & eleID2 & muTightCharge)
    
    # MC matching requirement (already passed for data)
    if sampleType == 'prompt':
        lep1_match=((padded_FOs[:,0].genPartFlav==1) | (padded_FOs[:,0].genPartFlav == 15))    
        lep2_match=((padded_FOs[:,1].genPartFlav==1) | (padded_FOs[:,1].genPartFlav == 15))
        mask = mask & lep1_match & lep2_match
    elif sampleType =='conversions':
        lep1_match=(padded_FOs[:,0].genPartFlav==22)
        lep2_match=(padded_FOs[:,1].genPartFlav==22)
        mask = mask & ( lep1_match | lep2_match ) 
    elif sampleType == 'nonprompt':
        lep1_match=((padded_FOs[:,0].genPartFlav!=1) & (padded_FOs[:,0].genPartFlav != 15) & (padded_FOs[:,0].genPartFlav != 22))
        lep2_match=((padded_FOs[:,1].genPartFlav!=1) & (padded_FOs[:,1].genPartFlav != 15) & (padded_FOs[:,1].genPartFlav != 22))
        mask = mask & ( lep1_match | lep2_match ) 
    elif sampleType == "data":
        pass
    else:
        raise Exception(f"Error: Unknown sampleType {sampleType}.")

    events['is2l'] = ak.fill_none(mask,False)

    # SFs
    events['sf_2l'] = padded_FOs[:,0].sf_nom*padded_FOs[:,1].sf_nom
    events['sf_2l_hi'] = padded_FOs[:,0].sf_hi*padded_FOs[:,1].sf_hi
    events['sf_2l_lo'] = padded_FOs[:,0].sf_lo*padded_FOs[:,1].sf_lo

    # SR:
    events['is2l_SR'] = (padded_FOs[:,0].isTightLep) & (padded_FOs[:,1].isTightLep)
    events['is2l_SR'] = ak.fill_none(events['is2l_SR'],False)

    # FF:
    fakeRateWeight2l(events, padded_FOs[:,0], padded_FOs[:,1])


# 3l selection
def add3lMaskAndSFs(events, year, isData, sampleType):

    # FOs and padded FOs
    FOs = events.l_fo_conept_sorted
    padded_FOs = ak.pad_none(FOs,3)

    # Filters and cleanups
    filter_flags = events.Flag
    filters = filter_flags.goodVertices & filter_flags.globalSuperTightHalo2016Filter & filter_flags.HBHENoiseFilter & filter_flags.HBHENoiseIsoFilter & filter_flags.EcalDeadCellTriggerPrimitiveFilter & filter_flags.BadPFMuonFilter & ((year == "2016") | filter_flags.ecalBadCalibFilter) & (isData | filter_flags.eeBadScFilter)
    cleanup=events.minMllAFAS > 12

    # IDs
    eleID1=(abs(padded_FOs[:,0].pdgId)!=11) | ((padded_FOs[:,0].convVeto != 0) & (padded_FOs[:,0].lostHits==0))
    eleID2=(abs(padded_FOs[:,1].pdgId)!=11) | ((padded_FOs[:,1].convVeto != 0) & (padded_FOs[:,1].lostHits==0))
    eleID3=(abs(padded_FOs[:,2].pdgId)!=11) | ((padded_FOs[:,2].convVeto != 0) & (padded_FOs[:,2].lostHits==0))

    # Pt requirements for 3rd lepton (different for e and m)
    pt3lmask = ak.any(ak.where(abs(FOs[:,2:3].pdgId)==11,FOs[:,2:3].conept>15.0,FOs[:,2:3].conept>10.0),axis=1)

    # 3l requirements:
    trilep = (ak.num(FOs)) >=3
    pt251510 = (ak.any(FOs[:,0:1].conept > 25.0, axis=1) & ak.any(FOs[:,1:2].conept > 15.0, axis=1) & pt3lmask)
    exclusive = ak.num( FOs[FOs.isTightLep],axis=-1)<4
    mask = (filters & cleanup & trilep & pt251510 & exclusive & eleID1 & eleID2 & eleID3 )

    # MC matching requirement (already passed for data)
    if sampleType == 'prompt':
        lep1_match=((padded_FOs[:,0].genPartFlav==1) | (padded_FOs[:,0].genPartFlav == 15))    
        lep2_match=((padded_FOs[:,1].genPartFlav==1) | (padded_FOs[:,1].genPartFlav == 15))
        lep3_match=((padded_FOs[:,2].genPartFlav==1) | (padded_FOs[:,2].genPartFlav == 15))
        mask = mask & lep1_match & lep2_match & lep3_match
    elif sampleType =='conversions':
        lep1_match=(padded_FOs[:,0].genPartFlav==22)
        lep2_match=(padded_FOs[:,1].genPartFlav==22)
        lep3_match=(padded_FOs[:,2].genPartFlav==22)
        mask = mask & ( lep1_match | lep2_match | lep3_match ) 
    elif sampleType == 'nonprompt':
        lep1_match=((padded_FOs[:,0].genPartFlav!=1) & (padded_FOs[:,0].genPartFlav != 15) & (padded_FOs[:,0].genPartFlav != 22))
        lep2_match=((padded_FOs[:,1].genPartFlav!=1) & (padded_FOs[:,1].genPartFlav != 15) & (padded_FOs[:,1].genPartFlav != 22))
        lep3_match=((padded_FOs[:,2].genPartFlav!=1) & (padded_FOs[:,2].genPartFlav != 15) & (padded_FOs[:,2].genPartFlav != 22))
        mask = mask & ( lep1_match | lep2_match | lep3_match ) 
    elif sampleType == "data":
        pass
    else:
        raise Exception(f"Error: Unknown sampleType {sampleType}.")

    events['is3l'] = ak.fill_none(mask,False)

    # SFs
    events['sf_3l'] = padded_FOs[:,0].sf_nom*padded_FOs[:,1].sf_nom*padded_FOs[:,2].sf_nom
    events['sf_3l_hi'] = padded_FOs[:,0].sf_hi*padded_FOs[:,1].sf_hi*padded_FOs[:,2].sf_hi
    events['sf_3l_lo'] = padded_FOs[:,0].sf_lo*padded_FOs[:,1].sf_lo*padded_FOs[:,2].sf_lo

    # SR:
    events['is3l_SR'] = (padded_FOs[:,0].isTightLep)  & (padded_FOs[:,1].isTightLep) & (padded_FOs[:,2].isTightLep)
    events['is3l_SR'] = ak.fill_none(events['is3l_SR'],False)

    # FF:
    fakeRateWeight3l(events, padded_FOs[:,0], padded_FOs[:,1], padded_FOs[:,2])


# 4l selection
def add4lMaskAndSFs(events, year, isData):

    # FOs and padded FOs
    FOs = events.l_fo_conept_sorted
    padded_FOs = ak.pad_none(FOs,4)

    # Filters and cleanups
    filter_flags = events.Flag
    filters = filter_flags.goodVertices & filter_flags.globalSuperTightHalo2016Filter & filter_flags.HBHENoiseFilter & filter_flags.HBHENoiseIsoFilter & filter_flags.EcalDeadCellTriggerPrimitiveFilter & filter_flags.BadPFMuonFilter & ((year == "2016") | filter_flags.ecalBadCalibFilter) & (isData | filter_flags.eeBadScFilter)
    cleanup = events.minMllAFAS > 12

    # IDs
    eleID1 = ((abs(padded_FOs[:,0].pdgId)!=11) | ((padded_FOs[:,0].convVeto != 0) & (padded_FOs[:,0].lostHits==0)))
    eleID2 = ((abs(padded_FOs[:,1].pdgId)!=11) | ((padded_FOs[:,1].convVeto != 0) & (padded_FOs[:,1].lostHits==0)))
    eleID3 = ((abs(padded_FOs[:,2].pdgId)!=11) | ((padded_FOs[:,2].convVeto != 0) & (padded_FOs[:,2].lostHits==0)))
    eleID4 = ((abs(padded_FOs[:,3].pdgId)!=11) | ((padded_FOs[:,3].convVeto != 0) & (padded_FOs[:,3].lostHits==0)))

    # Pt requirements for 3rd and 4th leptons (different for e and m)
    pt3lmask = ak.any(ak.where(abs(FOs[:,2:3].pdgId)==11,FOs[:,2:3].conept>15.0,FOs[:,2:3].conept>10.0),axis=1)
    pt4lmask = ak.any(ak.where(abs(FOs[:,3:4].pdgId)==11,FOs[:,3:4].conept>15.0,FOs[:,3:4].conept>10.0),axis=1)

    # 4l requirements:
    fourlep  = (ak.num(FOs)) >= 4
    pt25151510 = (ak.any(FOs[:,0:1].conept > 25.0, axis=1) & ak.any(FOs[:,1:2].conept > 15.0, axis=1) & pt3lmask & pt4lmask)
    tightleps = ((padded_FOs[:,0].isTightLep) & (padded_FOs[:,1].isTightLep) & (padded_FOs[:,2].isTightLep) & (padded_FOs[:,3].isTightLep))
    mask = (filters & cleanup & fourlep & pt25151510 & tightleps & eleID1 & eleID2 & eleID3 & eleID4)
    events['is4l'] = ak.fill_none(mask,False)

    # SFs:
    events['sf_4l'] = padded_FOs[:,0].sf_nom*padded_FOs[:,1].sf_nom*padded_FOs[:,2].sf_nom*padded_FOs[:,3].sf_nom
    events['sf_4l_hi'] = padded_FOs[:,0].sf_hi*padded_FOs[:,1].sf_hi*padded_FOs[:,2].sf_hi*padded_FOs[:,3].sf_hi
    events['sf_4l_lo'] = padded_FOs[:,0].sf_lo*padded_FOs[:,1].sf_lo*padded_FOs[:,2].sf_lo*padded_FOs[:,3].sf_lo

    # SR: Don't really need this for 4l, but define it so we can treat 4l category similar to 2lss and 3l
    events['is4l_SR'] = tightleps
    events['is4l_SR'] = ak.fill_none(events['is4l_SR'],False)


def addLepCatMasks(events):

    # FOs and padded FOs
    fo = events.l_fo_conept_sorted
    padded_fo = ak.pad_none(fo,4)
    padded_fo_id = padded_fo.pdgId

    # Find the numbers of e and m in the event
    is_e_mask = (abs(padded_fo_id)==11)
    is_m_mask = (abs(padded_fo_id)==13)
    n_e_2l = ak.sum(is_e_mask[:,0:2],axis=-1) # Make sure we only look at first two leps
    n_m_2l = ak.sum(is_m_mask[:,0:2],axis=-1) # Make sure we only look at first two leps
    n_e_3l = ak.sum(is_e_mask[:,0:3],axis=-1) # Make sure we only look at first three leps
    n_m_3l = ak.sum(is_m_mask[:,0:3],axis=-1) # Make sure we only look at first three leps
    n_e_4l = ak.sum(is_e_mask,axis=-1)        # Look at all the leps
    n_m_4l = ak.sum(is_m_mask,axis=-1)        # Look at all the leps

    # 2l masks
    events['is_ee'] = ((n_e_2l==2) & (n_m_2l==0)) 
    events['is_em'] = ((n_e_2l==1) & (n_m_2l==1)) 
    events['is_mm'] = ((n_e_2l==0) & (n_m_2l==2)) 

    # 3l masks
    events['is_eee'] = ((n_e_3l==3) & (n_m_3l==0)) 
    events['is_eem'] = ((n_e_3l==2) & (n_m_3l==1)) 
    events['is_emm'] = ((n_e_3l==1) & (n_m_3l==2)) 
    events['is_mmm'] = ((n_e_3l==0) & (n_m_3l==3)) 

    # 4l masks
    events['is_eeee'] = ((n_e_4l==4) & (n_m_4l==0))
    events['is_eeem'] = ((n_e_4l==3) & (n_m_4l==1))
    events['is_eemm'] = ((n_e_4l==2) & (n_m_4l==2))
    events['is_emmm'] = ((n_e_4l==1) & (n_m_4l==3))
    events['is_mmmm'] = ((n_e_4l==0) & (n_m_4l==4))
    events['is_gr4l'] = ((n_e_4l+n_m_4l)>4)


# Returns a mask for events with a same flavor opposite sign pair close to the Z
# Mask will be True if any combination of 2 leptons from within the given collection satisfies the requirement
def get_Z_peak_mask(lep_collection,pt_window):
    ll_pairs = ak.combinations(lep_collection, 2, fields=["l0","l1"])
    zpeak_mask = (abs((ll_pairs.l0+ll_pairs.l1).mass - 91.2)<pt_window)
    sfos_mask = (ll_pairs.l0.pdgId == -ll_pairs.l1.pdgId)
    sfosz_mask = ak.flatten(ak.any((zpeak_mask & sfos_mask),axis=1,keepdims=True)) # Use flatten here because it is too nested (i.e. it looks like this [[T],[F],[T],...], and want this [T,F,T,...]))
    return sfosz_mask

# Testing out some hadronic top stuff
def get_hadt_mass(jet_collection,btagwpl,pt_window=10):

    jjj_triplets = ak.combinations(jet_collection, 3, fields=["i0","i1","i2"])
    triplets_with_1b_mask  = ((ak.values_astype(jjj_triplets.i0.btagDeepFlavB>btagwpl,int)+ak.values_astype(jjj_triplets.i1.btagDeepFlavB>btagwpl,np.int32)+ak.values_astype(jjj_triplets.i2.btagDeepFlavB>btagwpl,np.int32))==1)

    jjb_triplets = jjj_triplets[triplets_with_1b_mask]

    jjb_mass = (jjb_triplets.i0+jjb_triplets.i1+jjb_triplets.i2).mass
    jjb_pt = (jjb_triplets.i0+jjb_triplets.i1+jjb_triplets.i2).pt

    jj_mass = ak.where( jjb_triplets.i0.btagDeepFlavB>btagwpl,(jjb_triplets.i1+jjb_triplets.i2).mass,( ak.where( jjb_triplets.i1.btagDeepFlavB>btagwpl,(jjb_triplets.i0+jjb_triplets.i2).mass, (jjb_triplets.i0+jjb_triplets.i1).mass)))

    # Some placeholders for now
    t_mass = 165.0
    w_mass = 70.0
    t_width = 10.0
    w_width = 10.0
    chisq_threhsold = 1000000000.0
    #chisq_threhsold = 40.0
    #chisq_threhsold = 100.0

    chi_sq = (((jjb_mass-t_mass)*(jjb_mass-t_mass)/((t_width)*(t_width))) + ((jj_mass-w_mass)*(jj_mass-w_mass)/((w_width)*(w_width))))
    chi_sq_min_idx = ak.argmin(chi_sq,keepdims=True,axis=1)
    jjb_mass_best = jjb_mass[chi_sq_min_idx]
    jjb_pt_best = jjb_pt[chi_sq_min_idx]
    jj_mass_best = jj_mass[chi_sq_min_idx]

    has_hatd_candidate_mask = ak.fill_none(ak.any((chi_sq<chisq_threhsold),axis=1),False)

    return has_hatd_candidate_mask,ak.flatten(chi_sq[chi_sq_min_idx]),ak.flatten(jjb_mass_best),ak.flatten(jjb_pt_best),ak.flatten(jj_mass_best),jjb_mass,jj_mass
