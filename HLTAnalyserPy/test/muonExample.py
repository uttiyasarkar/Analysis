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
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles, add_product,get_objs

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
import Analysis.HLTAnalyserPy.HistTools as HistTools


    
if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filename',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--out','-o',default="output.root",help='output filename')
    args = parser.parse_args()

    #we use a helper class EvtData which allows us to more easily access the products
    #products tells it what to read
    #note its a lazy evaulation, it only get the product on demand so other than startup, no
    #performance loss to having products registered you dont use
    #std_products is just a list with each entry having
    #    name : name to access it with
    #    type : c++ type, eg std::vector<reco::GenParticle>
    #    tag : InputTag but as a string so ":" seperates name:instance:process 
    products=[]
    add_product(products,"muons_nofilt_no_vtx","std::vector<reco::RecoChargedCandidate>","hltL3NoFiltersNoVtxMuonCandidates")
    add_product(products,"beamspot","reco::BeamSpot","hltOnlineBeamSpot")
    add_product(products,"trig_sum","std::vector< trigger::TriggerEvent  >","hltTriggerSummaryAOD::HLTX")
    evtdata = EvtData(products,verbose=True)
    
    in_filenames_with_prefix = ['{}{}'.format(args.prefix,x) for x in args.in_filename]
    events = Events(in_filenames_with_prefix)
    
    print("number of events",events.size())
    
    for eventnr,event in enumerate(events):
        #we need to initialise the handles, must be called first for every event
        evtdata.get_handles(events)
        beamspot = evtdata.get("beamspot")
        muons = evtdata.get("muons_nofilt_no_vtx")
        #unlike reco, muons will not be produced for every event so we need to check it exists
        #muons will be None type if this is the case
        if muons:
            print("nr muons ",muons.size())
            for muon in muons:
                dxy = muon.track().dxy(beamspot.position())
                
                print("muon pt {} eta {} phi {} dxy {}".format(muon.pt(),muon.eta(),muon.phi(),dxy)) 

                
