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


class CPUVsGPUTree:
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
        self.initialised = True
        self.ecalHTCPU = TreeVar(self.tree,"ecalHTCPU/F",None)
        self.hcalHTCPU = TreeVar(self.tree,"hcalHTCPU/F",None)
        self.ecalHT = TreeVar(self.tree,"ecalHT/F",None)
        self.hcalHT = TreeVar(self.tree,"hcalHT/F",None)

    def fill(self):
        if not self.initialised:
            self._init_tree()

        for var_ in self.evtvars:
            var_.fill(self.evtdata.event.object())
            
        self.ecalHTCPU.fill(TrigTools.get_objs_passing_filter_aod(evtdata,"hltHTEcal1CPU")[0].et())
        self.hcalHTCPU.fill(TrigTools.get_objs_passing_filter_aod(evtdata,"hltHTHcal1CPU")[0].et())
        self.ecalHT.fill(TrigTools.get_objs_passing_filter_aod(evtdata,"hltHTEcal1")[0].et())
        self.hcalHT.fill(TrigTools.get_objs_passing_filter_aod(evtdata,"hltHTHcal1")[0].et())

        self.tree.Fill()
  


if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filenames',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--out','-o',default="output.root",help='output filename')
    args = parser.parse_args()
    std_products = []
   
    add_product(std_products,"trig_sum","trigger::TriggerEvent","hltTriggerSummaryAOD")
    evtdata = EvtData(std_products,verbose=True)
    
    events = Events(CoreTools.get_filenames(args.in_filenames,args.prefix))
    nrevents = events.size()
    print("number of events",nrevents)    
    out_file = ROOT.TFile.Open(args.out,"RECREATE")
    tree = CPUVsGPUTree("cpuGPUTree",evtdata)
    for eventnr,event in enumerate(events):
        if eventnr%50000==0:
            print("{}/{}".format(eventnr,nrevents))
    
        evtdata.get_handles(event)

        tree.fill()
    out_file.Write()
