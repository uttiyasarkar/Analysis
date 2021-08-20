from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import ROOT
import glob
import os
import argparse
import shutil
import json
import re
from enum import IntEnum

from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles, add_product
import Analysis.HLTAnalyserPy.CoreTools as CoreTools
from Analysis.HLTAnalyserPy.GenTools import MCSample,MCSampleGetter


def get_xsec(mcdata):
    if mcdata.com_energy==14000.:
        if mcdata.proc_type == MCSample.ProcType.DY: return 5795.0
        if mcdata.proc_type == MCSample.ProcType.WJets: return 56990.0
        if mcdata.proc_type == MCSample.ProcType.MB: return 80.0E9
        if mcdata.proc_type == MCSample.ProcType.QCD: return get_qcd_xsec(mcdata.min_pthat,mcdata.max_pthat,mcdata.com_energy)
    elif mcdata.com_energy==13000.:
        if mcdata.proc_type == MCSample.ProcType.DY: return 6077.22
        if mcdata.proc_type == MCSample.ProcType.WJets: return 20508.9*3
        if mcdata.proc_type == MCSample.ProcType.MB: return 80.0E9
        if mcdata.proc_type == MCSample.ProcType.QCD: return get_qcd_xsec(mcdata.min_pthat,mcdata.max_pthat,mcdata.com_energy)
    else:
        raise ValueError("com energy {} is unrecognised, should be 13000 or 14000".format(com_energy))
 
    return 1.


def get_qcd_filt_effs(min_pt,max_pt,com_energy):
    
    filt_effs_13tev = {
        "80to120": {
            "mu_filt_eff": 0.0219,
            "mu_em_filt_eff": 0.1367,
            "em_filt_eff": 0.1563,
            "em_mu_filt_eff": 0.0177
        },
        "170to300": {
            "mu_filt_eff": 0.0358,
            "mu_em_filt_eff": 0.1426,
            "em_filt_eff": 0.1595,
            "em_mu_filt_eff": 0.0316
        },
        "50to80": {
            "mu_filt_eff": 0.0146,
            "mu_em_filt_eff": 0.1096,
            "em_filt_eff": 0.1259,
            "em_mu_filt_eff": 0.0108
        },
        "30to50": {
            "mu_filt_eff": 0.0082,
            "mu_em_filt_eff": 0.0491,
            "em_filt_eff": 0.0593,
            "em_mu_filt_eff": 0.0059
        },
        "15to30": {
            "mu_em_filt_eff": 0.0012,
            "em_mu_filt_eff": 0.0015,
            "em_filt_eff" : 0.001569,
            "mu_filt_eff" : 0.00328
        },
        "120to170": {
            "mu_filt_eff": 0.0292,
            "mu_em_filt_eff": 0.1417,
            "em_filt_eff": 0.1635,
            "em_mu_filt_eff": 0.0245
        },
        "300to9999": {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        },
        "0to9999": {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        },
        "300to470": {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        },
        "470to600": {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        },
        "600to9999": {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        }
    }
    filt_effs_14tev = {
        "80to120": {
            "mu_filt_eff": 0.0219,
            "mu_em_filt_eff": 0.1367,
            "em_filt_eff": 0.1563,
            "em_mu_filt_eff": 0.0177
        },
        "170to300": {
            "mu_filt_eff": 0.0358,
            "mu_em_filt_eff": 0.1426,
            "em_filt_eff": 0.1595,
            "em_mu_filt_eff": 0.0316
        },
        "50to80": {
            "mu_filt_eff": 0.0146,
            "mu_em_filt_eff": 0.1096,
            "em_filt_eff": 0.1259,
            "em_mu_filt_eff": 0.0108
        },
        "30to50": {
            "mu_filt_eff": 0.0082,
            "mu_em_filt_eff": 0.0491,
            "em_filt_eff": 0.0593,
            "em_mu_filt_eff": 0.0059
        },
        "15to20": {
            "mu_em_filt_eff": 0.0012,
            "em_mu_filt_eff": 0.0015,
            "em_filt_eff" : 0.001569,
            "mu_filt_eff" : 0.00328
        },
        "20to30": {
            "mu_filt_eff": 0.0043,
            "mu_em_filt_eff": 0.01,
            "em_filt_eff": 0.0122,
            "em_mu_filt_eff": 0.0031
        },
        "120to170": {
            "mu_filt_eff": 0.0292,
            "mu_em_filt_eff": 0.1417,
            "em_filt_eff": 0.1635,
            "em_mu_filt_eff": 0.0245
        },
        "300to9999": {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        },
        "0to9999": {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        },
        "300to470": {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        },
        "470to600": {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        },
        "600to9999": {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        }
    }
    
    if com_energy==13000.:
        filt_effs = filt_effs_13tev
    elif com_energy==14000.:
        filt_effs = filt_effs_14tev
    else:
        raise ValueError("com energy {} is unrecognised, should be 13000 or 14000".format(com_energy))


    key = "{:.0f}to{:.0f}".format(min_pt,max_pt)
    try:
        return filt_effs[key]
    except KeyError:
        print("{} not found".format(key))
        return {            
            "mu_filt_eff": 0.,
            "mu_em_filt_eff": 0.,
            "em_filt_eff": 0.,
            "em_mu_filt_eff": 0.
        }   
        
        

def get_qcd_xsec(min_pt,max_pt,com_energy):
    xsecs_13tev = {
        "0to9999" : 80.0E9, #update
        "15to30" : 1247000000.0,
        "30to50" : 107100000.0,
        "50to80" : 15760000.0,
        "80to120" : 2344000.0,
        "120to170" : 408000.0,
        "170to300" : 103800.0,
        "300to470" : 6838.0,
        "470to600" : 551.7,
        "600to9999" : 164.85,
        "300to9999" : 6838.0 + 551.7 + 164.85,
    } 
    xsecs_14tev = {
        "0to9999" : 80.0E9,
        "15to20" : 923300000.0,
        "20to30" : 436000000.0,
        "30to50" : 118400000.0,
        "50to80" : 17650000.0,
        "80to120" : 2671000.0,
        "120to170" : 469700.0,
        "170to300" : 121700.0,
        "300to470" : 8251.0,
        "470to600" : 686.4,
        "600to9999" : 244.8,
        "300to9999" : 8251.0 + 686.4 + 244.8
    } 
    if com_energy==13000.:
        xsecs = xsecs_13tev
    elif com_energy==14000.:
        xsecs = xsecs_14tev
    else:
        raise ValueError("com energy {} is unrecognised, should be 13000 or 14000".format(com_energy))


    key = "{:.0f}to{:.0f}".format(min_pt,max_pt)
    try:
        return xsecs[key]
    except KeyError:
        print("{} not found".format(key))
        return 0.
    

def qcd_weights_v2(output_data,nrevents,mcdata):
    output_entry = None
    min_pt,max_pt = mcdata.min_pthat,mcdata.max_pthat
    com_energy = mcdata.com_energy
    for entry in output_data:
        if min_pt == entry['min_pt']:
            output_entry  = entry
            break
    if not output_entry:
        output_entry = {
            'min_pt' : min_pt,'max_pt' : max_pt, 'xsec' : get_qcd_xsec(min_pt,max_pt,com_energy),
            'nr_inclusive' : 0, 'nr_em' : 0, 'nr_mu' : 0
        }
        output_entry.update(get_qcd_filt_effs(min_pt,max_pt,com_energy))
        
        output_data.append(output_entry)
    
    if mcdata.filt_type==MCSample.FiltType.Em:
        output_entry['nr_em'] += nrevents
    elif mcdata.filt_type==MCSample.FiltType.Mu:
        output_entry['nr_mu'] += nrevents
    else:
        output_entry['nr_inclusive'] += nrevents

def fill_weights_dict_v2(weights_dict,nrevents,mcdata):
    if mcdata.proc_type == MCSample.ProcType.QCD or mcdata.proc_type == MCSample.ProcType.MB:
        qcd_weights_v2(weights_dict['qcd'],nrevents,mcdata)
    else:
        key = ""
        if mcdata.proc_type == MCSample.ProcType.DY: key = "dy"
        elif mcdata.proc_type == MCSample.ProcType.WJets: key = "wjets"
        
        if key in weights_dict:
            if not weights_dict[key]:
                weights_dict[key].append({"nrtot": 0, "xsec": get_xsec(mcdata)})
            weights_dict[key][0]["nrtot"]+=nrevents
        
    return weights_dict
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='tries to open every root file in sub dir')
    parser.add_argument('in_filenames',nargs="+",help='input files')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--out','-o',default='weights.json',help='output weights json')
    parser.add_argument('--direct','-d',action='store_true',help='read nrtot directly from tree entries')
    parser.add_argument('--hlt_proc',default='HLTX',help='HLTX process, needed if not direct')
    args = parser.parse_args()
    
    products = []
    add_product(products,"geninfo","GenEventInfoProduct","generator")
    
    evtdata = EvtData(products)
    
    in_filenames = CoreTools.get_filenames(args.in_filenames,args.prefix)

    weights_dict = {"v2" : { "dy" : [], "qcd": [], "wjets" : [] } }
    mc_type_getter = MCSampleGetter()
    for in_filename in in_filenames:        
        events = Events(in_filename)          
        if events.size()==0:      
            print("file {}".format(in_filename),)
            mcinfo = mc_type_getter.get(evtdata=None)
        else:
            events.to(0)
            evtdata.get_handles(events)
            mcinfo = mc_type_getter.get(evtdata)
        com_energy = mcinfo.com_energy
        if args.direct:
            fill_weights_dict_v2(weights_dict["v2"],events.size(),mcinfo)
        else:
            
            root_file = ROOT.TFile.Open(in_filename)#events.object().event().getTFile() 
            root_file.Runs.GetEntry(0)
            nr_events = getattr(root_file.Runs,"edmMergeableCounter_hltNrInputEvents_nrEventsRun_{proc_name}".format(proc_name=args.hlt_proc)).value 
            fill_weights_dict_v2(weights_dict["v2"],nr_events,mcinfo)
    #we always need a MB entry so force it to be created  
    #will do nothing if already created
    fill_weights_dict_v2(weights_dict['v2'],0.,MCSample(MCSample.ProcType.MB,com_energy=com_energy))
    weights_dict['v2']['qcd'].sort(key=lambda x : x['min_pt'])
    with open(args.out,'w') as f:
        json.dump(weights_dict,f,indent=4)
    
