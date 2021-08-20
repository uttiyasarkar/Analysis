from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import sys
import ROOT
import json
import re

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
from collections import OrderedDict

def strip_path_version(name):
    return re.sub(r'_v[0-9]+\Z',r'_v',name)

def parse_l1_logical_express(express):
    """
    only handles the case of ORed seeds for now
    returns empty vec if is AND or NOT
    also returns empty vec if its L1GlobalDecision
    """
    if express.find(" AND ")!=-1 or express.find(" NOT")!=-1 or express.find("NOT ")!=-1 or express == "L1GlobalDecision":
        return []

    return express.split(" OR ")

def get_l1_seeds(process,path):
    """
    looks for a HLTL1TSeed module to determine the L1 seeds
    for now doesnt handle multiple HLTL1TSeed modules nor ignored ones
    we hack in the ignored ones because they all use L1GlobalInputTag = cms.InputTag( "hltGtStage2ObjectMap" )
    but we should do a proper walk of the modules in order
    """
    for modname in path.moduleNames():
        mod = getattr(process,modname)
        if mod.type_() == "HLTL1TSeed" and mod.L1GlobalInputTag.value()!="hltGtStage2ObjectMap":
            return parse_l1_logical_express(mod.L1SeedsLogicalExpression.value())
        
def get_datasets(process,path):
    """
    this parses the "datasets" pset to figure out the datasets the path belongs to
    datasets pset consists of cms.vstrings with the name of the param being the dataset
    and the contents of the cms.vstring being the paths of that dataset
    """
    datasets = []
    if hasattr(process,"datasets"):
        for dataset_name in process.datasets.parameterNames_():
            dataset_paths = getattr(process.datasets,dataset_name)
            if path.label() in dataset_paths:
                datasets.append(dataset_name)
    return datasets

def get_prescales(process,path):
    """
    this parses the prescale service to determine the prescales of the path
    it does not handle multiple prescale services (which would be an error regardless)
    a path has all 1s for prescales if its not found
    """
    prescale_service = [val for name,val in process.services_().items() if val.type_()=="PrescaleService"]
    if prescale_service:
        for para in prescale_service[0].prescaleTable:
            if para.pathName.value()==path.label():
                return para.prescales.value()
        return [1]*max(len(prescale_service[0].lvl1Labels),1)
    else:
        return [1]

def get_group(group_data,path):
    """
    auto groups triggers which differ only by thresholds together
    it does this by stripping numbers out of the name, a better solution could be found
    """
    path_name = path.label()
    group_name = re.sub(r'[0-9]+','',path_name)
    if group_name not in group_data:
        group_data[group_name] = len(group_data.keys())
    return group_data[group_name]
                
def get_physics_datasets(process,physics_streams):
    datasets = []
    if hasattr(process,"streams"):
        for physics_stream in physics_streams:
            if process.streams.hasParameter(physics_stream):
                datasets.extend(process.streams.getParameter(physics_stream).value())
        datasets = list(set(datasets))
    return datasets

def get_path_data(process,path,group_data,physics_datasets):
    data = OrderedDict()
    data['datasets'] = get_datasets(process,path)
    data['group'] = get_group(group_data,path)
    data['pags'] = []
    data['l1_seeds'] = get_l1_seeds(process,path)
    data['prescales'] = get_prescales(process,path)
    data['disable'] = 0
    data['physics'] = any(dataset in physics_datasets for dataset in data['datasets']) if physics_datasets else 1
    return data

def adjust_ps_cols(pathname,input_ps):
    """
    this is a rather specific custom function which depends on the menu
    it assumes the main column is column 1
    [0] = column 1
    [1] = all triggers at ps==1 set to 0
    [2] = all triggers at ps!=1 set to 0
    [3] = all triggers at ps!=1 x2
    [4] = all triggers at ps!=1 x2 + paths disabled

    """
    
    disable_trigs = ["HLT_Ele28_WPTight_Gsf_v","HLT_Ele30_WPTight_Gsf_v","HLT_DoubleEle25_CaloIdL_MW_v","HLT_DiEle27_WPTightCaloOnly_L1DoubleEG_v","HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_v","HLT_Ele35_WPTight_Gsf_L1EGMT_v","HLT_Ele115_CaloIdVT_GsfTrkIdT_v","HLT_DoublePhoton70_v",
                     "HLT_TriplePhoton_35_35_5_CaloIdLV2_R9IdVL_v","HLT_TriplePhoton_30_30_10_CaloIdLV2_v","HLT_TriplePhoton_20_20_20_CaloIdLV2_v"
    ]

    disable_trigs.extend(["HLT_Mu50_v"])

    disable_trigs.extend(["HLT_AK8PFJet330_TrimMass30_PFAK8BoostedDoubleB_np2_v",
                          "HLT_AK8PFJet330_TrimMass30_PFAK8BoostedDoubleB_np4_v",
                          "HLT_AK8PFJet400_TrimMass30_v","HLT_AK8PFJet420_TrimMass30_v",
                          "HLT_CaloJet500_NoJetID_v","HLT_PFJet500_v","HLT_AK8PFJet500_v"])
                          
    
    disable_trigs.extend(["HLT_PFMETNoMu120_PFMHTNoMu120_IDTight_v","HLT_PFMET120_PFMHT120_IDTight_v",
                          "HLT_PFMETNoMu120_PFMHTNoMu120_IDTight_PFHT60_v","HLT_PFMET120_PFMHT120_IDTight_PFHT60_v","HLT_MonoCentralPFJet80_PFMETNoMu120_PFMHTNoMu120_IDTight_v","HLT_DiJet110_35_Mjj650_PFMET110_v","HLT_DiJet110_35_Mjj650_PFMET120_v"])

    disable_trigs.extend(["HLT_DoubleMediumChargedIsoPFTau35_Trk1_eta2p1_Reg_v",
                          "HLT_DoubleMediumChargedIsoPFTau35_Trk1_TightID_eta2p1_Reg_v",
                          "HLT_DoubleMediumChargedIsoPFTauHPS35_Trk1_eta2p1_Reg_v",
                          "HLT_DoubleMediumChargedIsoPFTauHPS35_Trk1_TightID_eta2p1_Reg_v",
                          "HLT_DoubleMediumChargedIsoPFTauHPS40_Trk1_eta2p1_Reg_v",
                          "HLT_DoubleMediumChargedIsoPFTauHPS40_Trk1_TightID_eta2p1_Reg_v",
                          "HLT_DoubleTightChargedIsoPFTau35_Trk1_eta2p1_Reg_v",
                          "HLT_DoubleTightChargedIsoPFTau35_Trk1_TightID_eta2p1_Reg_v"])

    #for p in disable_trigs:
    #    print(p)

    prescale_by_10 = ["HLT_BTagMu_AK4DiJet20_Mu5_noalgo_v","HLT_BTagMu_AK4DiJet20_Mu5_v",
                      "HLT_BTagMu_AK4DiJet40_Mu5_noalgo_v","HLT_BTagMu_AK4DiJet40_Mu5_v",
                      "HLT_BTagMu_AK4DiJet70_Mu5_noalgo_v","HLT_BTagMu_AK4DiJet70_Mu5_v",
                      "HLT_BTagMu_AK4DiJet110_Mu5_noalgo_v","HLT_BTagMu_AK4DiJet110_Mu5_v",
                      "HLT_BTagMu_AK4DiJet170_Mu5_noalgo_v","HLT_BTagMu_AK4DiJet170_Mu5_v",
                      "HLT_BTagMu_AK8DiJet170_Mu5_noalgo_v","HLT_BTagMu_AK8DiJet170_Mu5_v",
                      ]
#    disable_trigs.extend(prescale_by_10)

    l1psedpath = ['HLT_Mu3_PFJet40_v', 'HLT_Mu7p5_L2Mu2_Jpsi_v', 'HLT_Mu7p5_L2Mu2_Upsilon_v', 'HLT_Mu7p5_Track2_Jpsi_v', 'HLT_Mu7p5_Track3p5_Jpsi_v', 'HLT_Mu7p5_Track7_Jpsi_v', 'HLT_Mu7p5_Track2_Upsilon_v', 'HLT_Mu7p5_Track3p5_Upsilon_v', 'HLT_Mu7p5_Track7_Upsilon_v', 'HLT_IsoMu20_v', 'HLT_UncorrectedJetE30_NoBPTX_v', 'HLT_UncorrectedJetE30_NoBPTX3BX_v', 'HLT_L1SingleMuCosmics_v', 'HLT_L2Mu10_NoVertex_NoBPTX_v', 'HLT_DiPFJetAve80_v', 'HLT_DiPFJetAve140_v', 'HLT_DiPFJetAve200_v', 'HLT_DiPFJetAve60_HFJEC_v', 'HLT_DiPFJetAve100_HFJEC_v', 'HLT_DiPFJetAve160_HFJEC_v', 'HLT_AK8PFJet140_v', 'HLT_AK8PFJet200_v', 'HLT_PFJet60_v', 'HLT_PFJet80_v', 'HLT_PFJet140_v', 'HLT_PFJet200_v', 'HLT_PFJetFwd60_v', 'HLT_PFJetFwd140_v', 'HLT_PFJetFwd200_v', 'HLT_AK8PFJetFwd60_v', 'HLT_AK8PFJetFwd200_v', 'HLT_PFHT180_v', 'HLT_PFHT250_v', 'HLT_PFHT370_v', 'HLT_PFHT430_v', 'HLT_Mu12_DoublePFJets40_CaloBTagDeepCSV_p71_v', 'HLT_Mu12_DoublePFJets100_CaloBTagDeepCSV_p71_v', 'HLT_Mu12_DoublePFJets200_CaloBTagDeepCSV_p71_v', 'HLT_Mu12_DoublePFJets350_CaloBTagDeepCSV_p71_v', 'HLT_DoublePFJets40_CaloBTagDeepCSV_p71_v', 'HLT_DoublePFJets200_CaloBTagDeepCSV_p71_v', 'HLT_DoublePFJets350_CaloBTagDeepCSV_p71_v', 'HLT_Mu17_TrkIsoVVL_v', 'HLT_Mu19_TrkIsoVVL_v', 'HLT_BTagMu_AK4DiJet40_Mu5_v', 'HLT_BTagMu_AK4DiJet70_Mu5_v', 'HLT_BTagMu_AK4DiJet110_Mu5_v', 'HLT_BTagMu_AK4DiJet170_Mu5_v', 'HLT_BTagMu_AK8DiJet170_Mu5_v', 'HLT_BTagMu_AK4DiJet40_Mu5_noalgo_v', 'HLT_BTagMu_AK4DiJet70_Mu5_noalgo_v', 'HLT_BTagMu_AK4DiJet110_Mu5_noalgo_v', 'HLT_BTagMu_AK4DiJet170_Mu5_noalgo_v', 'HLT_BTagMu_AK8DiJet170_Mu5_noalgo_v', 'HLT_Dimuon0_Jpsi_L1_NoOS_v', 'HLT_Dimuon0_Jpsi_NoVertexing_NoOS_v', 'HLT_Dimuon0_Jpsi_NoVertexing_v', 'HLT_Dimuon0_Upsilon_L1_4p5_v', 'HLT_Dimuon0_Upsilon_L1_4p5er2p0_v', 'HLT_Dimuon0_LowMass_L1_0er1p5_v', 'HLT_Dimuon0_LowMass_L1_4_v', 'HLT_Dimuon0_Upsilon_Muon_NoL1Mass_v', 'HLT_DoubleMu3_Trk_Tau3mu_NoL1Mass_v', 'HLT_Mu17_v', 'HLT_Mu19_v', 'HLT_Ele8_CaloIdL_TrackIdL_IsoVL_PFJet30_v', 'HLT_Ele12_CaloIdL_TrackIdL_IsoVL_PFJet30_v', 'HLT_Ele23_CaloIdL_TrackIdL_IsoVL_PFJet30_v', 'HLT_Ele8_CaloIdM_TrackIdM_PFJet30_v', 'HLT_Ele17_CaloIdM_TrackIdM_PFJet30_v', 'HLT_Ele23_CaloIdM_TrackIdM_PFJet30_v', 'HLT_Photon30_HoverELoose_v', 'HLT_CDC_L2cosmic_10_er1p0_v', 'HLT_HcalIsolatedbunch_v', 'HLT_ZeroBias_FirstCollisionAfterAbortGap_v', 'HLT_ZeroBias_LastCollisionInTrain_v', 'HLT_ZeroBias_FirstBXAfterTrain_v', 'HLT_MediumChargedIsoPFTau50_Trk30_eta2p1_1pr_v']


    prescale = input_ps[1]
    prescales = [prescale]
    
    unprescaled_path = prescale==1 and not pathname in l1psedpath
    if pathname in prescale_by_10:
        prescale = prescale*5
    

    prescales.append(prescale if not unprescaled_path else 0)
    prescales.append(prescale if unprescaled_path else 0)
    prescales.append(prescale if unprescaled_path else prescale*2)
    prescales.append(prescales[-1] if pathname not in disable_trigs else 0)
    return prescales
    

if __name__ == "__main__":
    

    parser = argparse.ArgumentParser(description='generates a rate ntup config from HLT file')
    parser.add_argument('cfg',help='input config')
    parser.add_argument('--out','-o',default="output.json",help="output file")
    args = parser.parse_args()
  
    process = CoreTools.load_cmssw_cfg(args.cfg)
    cfg_dict = OrderedDict()
    group_data = {}

    physics_streams = {"PhysicsMuons","PhysicsHadronsTaus","PhysicsEGamma","PhysicsCommissioning"}
    physics_datasets = get_physics_datasets(process,physics_streams)

    print(physics_datasets)

    for name,path in process.paths_().items():
        name_novers = strip_path_version(name)
        cfg_dict[name_novers] = get_path_data(process,path,group_data,physics_datasets)
        cfg_dict[name_novers]['prescales'] =  adjust_ps_cols(name_novers,cfg_dict[name_novers]['prescales'])
        
        

    with open(args.out,'w') as f:
        json.dump(cfg_dict,f,indent=0)
