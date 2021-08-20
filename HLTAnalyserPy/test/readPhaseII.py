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

if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filename',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--out','-o',default="output.root",help='output filename')
    args = parser.parse_args()
    add_product(phaseII_products,"countEcalRecHitsEBThres0GeV","int","hltEgammaHLTExtra:countEcalRecHitsEcalRecHitsEBThres0GeV")
    add_product(phaseII_products,"countEcalRecHitsEBThres1GeV","int","hltEgammaHLTExtra:countEcalRecHitsEcalRecHitsEBThres1GeV")
    add_product(phaseII_products,"ecalHitsTest","edm::SortedCollection<EcalRecHit,edm::StrictWeakOrdering<EcalRecHit> >","hltEcalRecHit:EcalRecHitsEB")
    add_product(phaseII_products,"hgcalTest","edm::SortedCollection<HGCRecHit,edm::StrictWeakOrdering<HGCRecHit> >","HGCalRecHit:HGCHEBRecHits")
    add_product(phaseII_products,"countHGCal1GeV","int","hltEgammaHLTPhase2Extra:countHgcalRecHitsHGCHEBRecHitsThres1GeV")
    add_product(phaseII_products,"countHGCal0GeV","int","hltEgammaHLTPhase2Extra:countHgcalRecHitsHGCHEBRecHitsThres0GeV")
    add_product(phaseII_products,"trig_sum","trigger::TriggerEvent","hltTriggerSummaryAOD::HLTX")
    
    evtdata = EvtData(phaseII_products,verbose=True)
    
    in_filenames_with_prefix = ['{}{}'.format(args.prefix,x) for x in args.in_filename]
    events = Events(in_filenames_with_prefix)
    
    print("number of events",events.size())

    
#    with open("weights_test_qcd.json") as f:
#       import json
#       weights = json.load(f)

#    weighter = QCDWeightCalc(weights["v2"]["qcd"])
#    events.to(3)
#    evtdata.get_handles(events)
#    weighter.weight(evtdata)
