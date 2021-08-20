from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from array import array
import argparse
import sys
import ROOT
import json
import re
import math
from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products, add_product,get_objs

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
import Analysis.HLTAnalyserPy.HistTools as HistTools

def fill_evtlut(evtlut,runnr,lumi,eventnr,entrynr):
    
    if runnr not in evtlut:
        evtlut[runnr]={}
    if lumi not in evtlut[runnr]:
        evtlut[runnr][lumi]={}
    if eventnr not in evtlut[runnr][lumi]:
        evtlut[runnr][lumi][eventnr]= []
    evtlut[runnr][lumi][eventnr] = entrynr

def match(evtlut,runnr,lumi,eventnr,eta,phi):
    try:
        evt_entries = evtlut[runnr][lumi][int(eventnr)]
    except KeyError:
        return None
    
    best_dr2 = 0.01*0.01
    obj_data = None 
    for obj in evt_entries:
        dr2 = ROOT.reco.deltaR2(eta,phi,obj['eta'],obj['phi'])
        if dr2 < best_dr2:
            best_dr2 = dr2
            obj_data = obj
    if obj_data:
        return obj_data['entrynr']
    else:
        return None

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
    parser.add_argument('--ref_filename',nargs="+",help='ntup regression tree')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--out','-o',default="output.root",help='output filename')
    args = parser.parse_args()
    add_product(phaseII_products,"countEcalRecHitsEBThres0GeV","int","hltEgammaHLTExtra:countEcalRecHitsEcalRecHitsEBThres0GeV")
    add_product(phaseII_products,"countEcalRecHitsEBThres1GeV","int","hltEgammaHLTExtra:countEcalRecHitsEcalRecHitsEBThres1GeV")
    add_product(phaseII_products,"ecalHitsTest","edm::SortedCollection<EcalRecHit,edm::StrictWeakOrdering<EcalRecHit> >","hltEcalRecHit:EcalRecHitsEB")
    add_product(phaseII_products,"hgcalTest","edm::SortedCollection<HGCRecHit,edm::StrictWeakOrdering<HGCRecHit> >","HGCalRecHit:HGCHEBRecHits")
    add_product(phaseII_products,"countHGCal1GeV","int","hltEgammaHLTPhase2Extra:countHgcalRecHitsHGCHEBRecHitsThres1GeV")
    add_product(phaseII_products,"countHGCal0GeV","int","hltEgammaHLTPhase2Extra:countHgcalRecHitsHGCHEBRecHitsThres0GeV")
    
    add_product(phaseII_products,"scCorr","vector<reco::SuperCluster>","corrHGCALSuperClus")
    add_product(phaseII_products,"scCorrHLT","vector<reco::SuperCluster>","corrHGCALSuperClusHLT")
    add_product(phaseII_products,"scCorrFeatures","vector<vector<float>>","corrHGCALSuperClus:features")
    add_product(phaseII_products,"scCorrFeaturesHLT","vector<vector<float>>","corrHGCALSuperClusHLT:features")
    add_product(phaseII_products,"scCorrFeaturesVM","edm::ValueMap<vector<float>>","corrHGCALSuperClus:features")
    add_product(phaseII_products,"scCorrFeaturesHLTVM","edm::ValueMap<vector<float>>","corrHGCALSuperClusHLT:features")
    
    
    evtdata = EvtData(phaseII_products,verbose=True)
    evtdata_ref = EvtData(phaseII_products,verbose=True)
    in_filenames_with_prefix = ['{}{}'.format(args.prefix,x) for x in args.in_filename]
    events = Events(in_filenames_with_prefix)
    
    ref_filenames_with_prefix = ['{}{}'.format(args.prefix,x) for x in args.ref_filename]
    events_ref =  Events(ref_filenames_with_prefix)

    evt_lut = {}
    for entrynr,event in enumerate(events_ref): 
        runnr = event.eventAuxiliary().run()
        lumi = event.eventAuxiliary().luminosityBlock()
        eventnr = event.eventAuxiliary().event()
        fill_evtlut(evt_lut,runnr,lumi,eventnr,entrynr)
    
      

    print("number of events",events.size())
    for event_nr,event in enumerate(events):  
        evtdata.get_handles(event)
        
        sc_hlt = evtdata.get("scCorrHLT")
        sc_hlt_features = evtdata.get("scCorrFeaturesHLTVM")
        sc_features = evtdata.get("scCorrFeaturesVM")
        runnr = event.eventAuxiliary().run()
        lumi = event.eventAuxiliary().luminosityBlock()
        eventnr = event.eventAuxiliary().event()
        try:
            evt_entries = evt_lut[runnr][lumi][int(eventnr)]
            
            events_ref.to(evt_entries)
            evtdata_ref.get_handles(events_ref) 
            sc_hlt_features_ref = evtdata_ref.get("scCorrFeaturesHLT")
            sc_features_ref = evtdata_ref.get("scCorrFeatures")
        except KeyError:
            evt_entries = None
            
        
        
        if evt_entries==None:
            print("event",event.eventAuxiliary().luminosityBlock(),event.eventAuxiliary().event(),evt_entries!=None)
            continue

        for sc_nr,sc in enumerate(sc_hlt):
            
            for feature_nr,feature in enumerate(sc_hlt_features.begin()[sc_nr]):
                if feature != sc_hlt_features_ref[sc_nr][feature_nr]:
                    print("online feature {} miss match {} vs {}".format(feature_nr,feature,sc_hlt_features_ref[sc_nr][feature_nr]))
                else:
                    print("online feature {} match {} vs {}".format(feature_nr,feature,sc_hlt_features_ref[sc_nr][feature_nr]))
            for feature_nr,feature in enumerate(sc_features.begin()[sc_nr]):
                if feature != sc_features_ref[sc_nr][feature_nr]:
                    print("offline feature {} miss match {} vs {}".format(feature_nr,feature,sc_features_ref[sc_nr][feature_nr]))
 #               else:
  #                  print("offline feature {} match {} vs {}".format(feature_nr,feature,sc_features_ref[sc_nr][feature_nr]))
                
