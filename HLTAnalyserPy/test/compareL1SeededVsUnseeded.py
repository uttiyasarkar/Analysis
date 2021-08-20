from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from array import array
import argparse
import sys
import ROOT
import json
import re
from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products, add_product,get_objs

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
import Analysis.HLTAnalyserPy.HistTools as HistTools

def match_tkeg_index(egidx,trkegs):
    for trkeg in trkegs:
        if trkeg.EGRef().key()==egidx:
            return trkeg
    return None


def print_l1_region(evtdata,suffix):
    l1egs = evtdata.get("l1egs{}".format(suffix))
    l1tkphos = evtdata.get("l1tkphos{}".format(suffix))
    l1tkeles = evtdata.get("l1tkeles{}".format(suffix))
    
    for egidx,eg in enumerate(l1egs):
        tkpho = match_tkeg_index(egidx,l1tkphos)
        tkele = match_tkeg_index(egidx,l1tkeles)
        print_str = "  {indx} {et} {eta} {phi}".format(indx=egidx,et=eg.et(),
                                                       eta=eg.eta(),phi=eg.phi())
        if tkpho:
            print_str+=" tkpho {et} {isol} {isolPV}".format(et = tkpho.et(),
                                                             isol = tkpho.trkIsol(),
                                                             isolPV = tkpho.trkIsolPV())
        if tkele:
            print_str+=" tkele {et} {isol} {isolPV} {zvtx}".format(
                et = tkele.et(),isol = tkele.trkIsol(),isolPV = tkele.trkIsolPV(),
                zvtx = tkele.trkzVtx())
        print(print_str)

    
def print_l1(evtdata,events,index):
    events.to(index)
    evtdata.get_handles(events)
    print("barrel:")
    print_l1_region(evtdata,"_eb")
    print("encap:")
    print_l1_region(evtdata,"_hgcal")


def match_eg(eg,egs_to_comb):
    for comb_eg in egs_to_comb:
        if eg.superCluster().seed().seed().rawId()==comb_eg.superCluster().seed().seed().rawId():
            return comb_eg
    return None

def diff(lhs,rhs,varname):
    var_lhs = getattr(lhs,varname)()
    var_rhs = getattr(rhs,varname)()
    if abs(var_lhs-var_rhs)>0.001:
        print("var {} differs  {} vs {}".format(varname,var_lhs,var_rhs))

def diff_uservar(lhs,rhs,varname_lhs,varname_rhs):
    var_lhs = lhs.var(varname_lhs,False)
    var_rhs = rhs.var(varname_rhs,False)
    if abs(var_lhs-var_rhs)>0.001:
        print("var {} differs  {} vs {}".format(varname_lhs,var_lhs,var_rhs))

def compare(evtdata,egs_unseeded,egs_l1seeded):
    print("unseeded",egs_unseeded.size(),"vs",egs_l1seeded.size())
    for eg_l1seeded in egs_l1seeded:
        eg_unseeded = match_eg(eg_l1seeded,egs_unseeded)
        if not eg_unseeded:
            print("l1seeded {} {} {} has no match".format(eg_l1seeded.pt(),eg_l1seeded.eta(),eg_l1seeded.phi()))
            continue

        varnames = ["et","eta","phi"]
        for varname in varnames:
            diff(eg_l1seeded,eg_unseeded,varname)
        uservars_l1 = eg_l1seeded.varNames()
        uservars_un = eg_unseeded.varNames()
      #  if uservars_l1 != uservars_un:
        #    print("missing vars {}  {}".format(uservars_l1,uservars_un))
       # 
        for uservar in uservars_l1:
            diff_uservar(eg_l1seeded,eg_unseeded,uservar,uservar.replace("L1Seeded","Unseeded"))
    

        

if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filename',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--out','-o',default="output.root",help='output filename')
    args = parser.parse_args()
    add_product(phaseII_products,"trig_sum","trigger::TriggerEvent","hltTriggerSummaryAOD::HLTX")
    add_product(phaseII_products,"egtrigobjs_l1seeded","std::vector<trigger::EgammaObject>","hltEgammaHLTExtra:L1Seeded")
    evtdata = EvtData(phaseII_products,verbose=True)
    
    in_filenames_with_prefix = ['{}{}'.format(args.prefix,x) for x in args.in_filename]
    events = Events(in_filenames_with_prefix)
    
    print("number of events",events.size())

    for event in events:
        evtdata.get_handles(event)
        egs_unseeded = evtdata.get("egtrigobjs")
        egs_l1seeded = evtdata.get("egtrigobjs_l1seeded")
        
        compare(evtdata,egs_unseeded,egs_l1seeded)

        

#    with open("weights_test_qcd.json") as f:
#       import json
#       weights = json.load(f)

#    weighter = QCDWeightCalc(weights["v2"]["qcd"])
#    events.to(3)
#    evtdata.get_handles(events)
#    weighter.weight(evtdata)
