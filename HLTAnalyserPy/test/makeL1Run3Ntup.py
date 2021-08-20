from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from array import array
import argparse
import sys
import ROOT
import json
import re
import six
from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products, add_product,get_objs

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
import Analysis.HLTAnalyserPy.HistTools as HistTools
import Analysis.HLTAnalyserPy.TrigTools as TrigTools
import Analysis.HLTAnalyserPy.L1Tools as L1Tools
from Analysis.HLTAnalyserPy.CoreTools import UnaryFunc
from Analysis.HLTAnalyserPy.NtupTools import TreeVar
from Analysis.HLTAnalyserPy.EvtWeights import EvtWeights


from functools import partial
import itertools

class L1Tree:
    def __init__(self,tree_name,evtdata):   
        self.tree = ROOT.TTree(tree_name,'')
        self.evtdata = evtdata
        self.initialised = False
    def _init_tree(self):
        self.evtvars = [
            TreeVar(self.tree,"runnr/i",UnaryFunc("eventAuxiliary().run()")),
            TreeVar(self.tree,"lumiSec/i",UnaryFunc("eventAuxiliary().luminosityBlock()")),
            TreeVar(self.tree,"eventnr/i",UnaryFunc("eventAuxiliary().event()")),        
        ]
 
        scales_params = L1Tools.make_egscale_dict()
        l1_vars_names = {
            'pt/F' : UnaryFunc("pt()"),
            'eta/F' : UnaryFunc("eta()"),
            'phi/F' : UnaryFunc("phi()"),
            'hwQual/F' : UnaryFunc("hwQual()"),          
            }
        max_l1egs = 2000
        max_l1mus = 2000
        nregs_name = "nrEGs"
        nrmus_name = "nrMuons"
        self.l1eg_nr = TreeVar(self.tree,nregs_name+"/i",UnaryFunc(partial(len)))
        self.l1eg_vars = []
        for name,func in six.iteritems(l1_vars_names):
            self.l1eg_vars.append(TreeVar(self.tree,"l1eg_"+name,func,max_l1egs,nregs_name)) 

        self.l1mu_nr = TreeVar(self.tree,nrmus_name+"/i",UnaryFunc(partial(len)))
        self.l1mu_vars = []  
        for name,func in six.iteritems(l1_vars_names):
            self.l1mu_vars.append(TreeVar(self.tree,"l1mu_"+name,func,max_l1mus,nrmus_name))   
       
        self.initialised = True

    def fill(self):
        if not self.initialised:
            self._init_tree()

        for var_ in self.evtvars:
            var_.fill(self.evtdata.event.object())

        l1egs_allbx  = self.evtdata.get("egamma")
        l1egs = [l1egs_allbx.at(0,egnr) for egnr in range(0,l1egs_allbx.size(0))]
        self.l1eg_nr.fill(l1egs)
        for objnr,l1eg_obj in enumerate(l1egs):
            for var_ in self.l1eg_vars:
                var_.fill(l1eg_obj,objnr)

        l1mus_allbx  = self.evtdata.get("muon")
        l1mus = [l1mus_allbx.at(0,munr) for munr in range(0,l1mus_allbx.size(0))]
        self.l1mu_nr.fill(l1mus)
        for objnr,l1mu_obj in enumerate(l1mus):
            for var_ in self.l1mu_vars:
                var_.fill(l1mu_obj,objnr)

        self.tree.Fill()

if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filenames',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--out','-o',default="output.root",help='output filename')
    args = parser.parse_args()
    std_products = []
    add_product(std_products,"algblk","BXVector<GlobalAlgBlk>","hltGtStage2Digis")
    add_product(std_products,"extblk","BXVector<GlobalExtBlk>","hltGtStage2Digis")
    add_product(std_products,"egamma","BXVector<l1t::EGamma>","hltGtStage2Digis:EGamma")
    add_product(std_products,"etsum","BXVector<l1t::EtSum>","hltGtStage2Digis:EtSum")
    add_product(std_products,"jet","BXVector<l1t::Jet>","hltGtStage2Digis:Jet")
    add_product(std_products,"muon","BXVector<l1t::Muon>","hltGtStage2Digis:Muon")
    add_product(std_products,"tau","BXVector<l1t::Tau>","hltGtStage2Digis:Tau")
    add_product(std_products,"trig_res","edm::TriggerResults","TriggerResults")

    evtdata = EvtData(std_products,verbose=True)
    
    events = Events(CoreTools.get_filenames(args.in_filenames,args.prefix))
    nrevents = events.size()
    print("number of events",nrevents)
    trig_res = TrigTools.TrigResults(["DST_ZeroBias_v"])
    out_file = ROOT.TFile.Open(args.out,"RECREATE")
    tree = L1Tree("l1Tree",evtdata)
    for eventnr,event in enumerate(events):
        if eventnr%50000==0:
            print("{}/{}".format(eventnr,nrevents))
    
        evtdata.get_handles(event)
        trig_res.fill(evtdata)
        if trig_res.result("DST_ZeroBias_v"):
            tree.fill()
    out_file.Write()
        
