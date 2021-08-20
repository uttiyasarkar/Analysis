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
import Analysis.HLTAnalyserPy.TrigTools as TrigTools
import Analysis.HLTAnalyserPy.L1Tools as L1Tools
from Analysis.HLTAnalyserPy.CoreTools import UnaryFunc
from Analysis.HLTAnalyserPy.NtupTools import TreeVar
from Analysis.HLTAnalyserPy.EvtWeights import EvtWeights


from functools import partial
import itertools

def get_hlt_menu(evtdata,hlt_process="HLT"):
    if not hasattr(ROOT,"getHLTMenu"):
        ROOT.gInterpreter.Declare("""
#include "FWCore/ParameterSet/interface/ParameterSet.h"
std::string getHLTMenu(edm::ParameterSet& pset){
   const auto& cfgVerPSet = pset.getParameterSet("HLTConfigVersion");
   const auto& names = cfgVerPSet.getParameterNames();
   return cfgVerPSet.getParameter<std::string>("tableName");
}
""")
    cfg = ROOT.edm.ProcessConfiguration()  
    proc_hist = evtdata.event.object().processHistory() 
    proc_hist.getConfigurationForProcess(hlt_process,cfg)
    cfg_pset = evtdata.event.object().parameterSet(cfg.parameterSetID())  
    return str(ROOT.getHLTMenu(cfg_pset))

class TSGHLTPathNameTree:
    def __init__(self,tree_name,evtdata,trig_res_name="trig_res"):   
        self.tree = ROOT.TTree(tree_name,'')
        self.evtdata = evtdata
        self.trig_res_name = trig_res_name
        self.initialised = False
        self.last_runnr = -1 #so we can watch for trigger menu changes

    def _init_tree(self):      
        self.hlt_menu = ROOT.std.string("")
        self.tree.Branch("hltMenu",self.hlt_menu)
        self.path_names = ROOT.std.vector("std::string")()
        self.tree.Branch("pathNames",self.path_names)
        self.initialised = True

    def fill(self):
        
        if not self.initialised: 
            self._init_tree()
        
        if self.last_runnr!=evtdata.event.eventAuxiliary().run(): 
            new_hlt_menu = ROOT.std.string(get_hlt_menu(self.evtdata))
            if self.hlt_menu!=new_hlt_menu:
                self.hlt_menu.swap(ROOT.std.string(get_hlt_menu(self.evtdata)))
                trig_res = self.evtdata.get(self.trig_res_name) 
                trig_names = evtdata.event.object().triggerNames(trig_res).triggerNames()
                self.path_names.swap(trig_names)
                self.tree.Fill()
            self.last_runnr=evtdata.event.eventAuxiliary().run()
            
            

class TSGRateTree:
    def __init__(self,tree_name,evtdata,trig_res_name="trig_res"):   
        self.tree = ROOT.TTree(tree_name,'')
        self.evtdata = evtdata
        self.trig_res_name = trig_res_name
        self.initialised = False
        self.last_runnr = -1 #so we can watch for trigger menu changes

    def _init_tree(self):
        self.evtvars = [
            TreeVar(self.tree,"runnr/i",UnaryFunc("eventAuxiliary().run()")),
            TreeVar(self.tree,"lumiSec/i",UnaryFunc("eventAuxiliary().luminosityBlock()")),
            TreeVar(self.tree,"eventnr/i",UnaryFunc("eventAuxiliary().event()")),        
        ]

        self.l1bits_initial = ROOT.TBits();
        self.tree.Branch("l1ResInitial",self.l1bits_initial)
        self.l1bits_final = ROOT.TBits();
        self.tree.Branch("l1ResFinal",self.l1bits_final)
        self.hlt_bits = ROOT.TBits();
        self.tree.Branch("hltRes",self.hlt_bits)
 #       self.hlt_bits = ROOT.std.vector(int)()
 #       self.tree.Branch("hltRes",self.hlt_bits)
        self.hlt_menu = ROOT.std.string("test")
        self.tree.Branch("hltMenu",self.hlt_menu)
        self.l1_menuid = TreeVar(self.tree,"l1MenuID/i",None)
        self.initialised = True
        

    def fill(self):
       
        if not self.initialised: 
            self._init_tree()

        for var_ in self.evtvars:
            var_.fill(self.evtdata.event.object())

        trig_res = self.evtdata.get(self.trig_res_name) 

        if self.last_runnr!=evtdata.event.eventAuxiliary().run(): 
            self.hlt_menu.swap(ROOT.std.string(get_hlt_menu(self.evtdata)))
            self.last_runnr=evtdata.event.eventAuxiliary().run()
            trig_names = evtdata.event.object().triggerNames(trig_res).triggerNames()
  #          self.hlt_bits.resize(trig_names.size())

        l1_algblk = evtdata.get("algblk")
        if l1_algblk:
            l1dec_initial = l1_algblk.at(0,0).getAlgoDecisionInitial()
            l1dec_final = l1_algblk.at(0,0).getAlgoDecisionFinal()
        
            for trig_nr,res in enumerate(l1dec_initial):
                self.l1bits_initial.SetBitNumber(trig_nr,res)
    
            for trig_nr,res in enumerate(l1dec_final):
                self.l1bits_final.SetBitNumber(trig_nr,res)
    
       
        
    #    trig_names = evtdata.event.object().triggerNames(trig_res).triggerNames()
    #    for trig_nr,trig_name in enumerate(trig_names):
    #        print("trig_nr ",trig_nr," ",trig_name)

    
        for trig_nr in range(0,trig_res.size()):
            self.hlt_bits.SetBitNumber(trig_nr,trig_res[trig_nr].accept())
           # self.hlt_bits[trig_nr] = trig_res[trig_nr].accept()
    
        
        
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
    rate_tree = TSGRateTree("tsgRateTree",evtdata)
    path_tree = TSGHLTPathNameTree("hltPathNameTree",evtdata)
    count = 0
    seed = 178
    for eventnr,event in enumerate(events):
        if eventnr%50000==0:
            print("{}/{}".format(eventnr,nrevents))
        
        evtdata.get_handles(event)
        trig_res.fill(evtdata)
       # if trig_res.result("DST_ZeroBias_v"):
        rate_tree.fill()
        path_tree.fill()

        menu = evtdata.get("algblk").at(0,0)
        if menu.getAlgoDecisionFinal()[seed]:
            count+=1
            
      
    out_file.Write()
        
    print("count is ",count)
