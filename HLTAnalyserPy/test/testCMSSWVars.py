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
import Analysis.HLTAnalyserPy.IsolTools as IsolTools

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

def compare_l1_trk_iso(eg,evtdata):
    l1isol = IsolTools.get_l1_iso(eg,evtdata)
    l1isol_cmssw = eg.var("hltEgammaEleL1TrkIsoUnseeded",0)
    if abs(l1isol-l1isol_cmssw)>0.01 and l1isol<=9999.:
        print("l1 iso mis match {} {} {} : {} vs {}".format(eg.et(),eg.eta(),eg.phi(),l1isol,l1isol_cmssw))
        print("event: {} {} {}".format(events.eventAuxiliary().run(),events.eventAuxiliary().luminosityBlock(),events.eventAuxiliary().event()))

        for gsftrk in eg.gsfTracks():
            print("  gsf trk {} {} {} {}".format(gsftrk.pt(),gsftrk.eta(),gsftrk.phi(),gsftrk.vz()))
        l1trks = evtdata.get("l1trks")
        for l1trk_extra in l1trks:
            l1trk = l1trk_extra.ttTrk()
            print("  l1trk {} {} {} {}".format(l1trk.momentum().perp(),l1trk.eta(),l1trk.phi(),l1trk.z0()))
        
        


if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filename',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--out','-o',default="output.root",help='output filename')
    parser.add_argument('--report','-r',default=100,type=int,help='report interval')
    args = parser.parse_args()

    evtdata = EvtData(phaseII_products,verbose=True)
    
    in_filenames_with_prefix = ['{}{}'.format(args.prefix,x) for x in args.in_filename]
    events = Events(in_filenames_with_prefix)
    
    nr_events = events.size()
    print("number of events",events.size())

    for event_nr,event in enumerate(events):
        if event_nr%args.report==0:
            print("processing event {} / {}".format(event_nr,nr_events))
        evtdata.get_handles(event)
        
        egobjs = evtdata.get("egtrigobjs")
        for eg in egobjs: 
            compare_l1_trk_iso(eg,evtdata)
    
    
