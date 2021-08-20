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
from functools import partial

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
import Analysis.HLTAnalyserPy.HistTools as HistTools
import Analysis.HLTAnalyserPy.TrigTools as TrigTools
import Analysis.HLTAnalyserPy.L1Tools as L1Tools
from Analysis.HLTAnalyserPy.CoreTools import UnaryFunc
from Analysis.HLTAnalyserPy.NtupTools import TreeVar
from Analysis.HLTAnalyserPy.EvtWeights import EvtWeights

def get_eg(seed_id,egs):
    for eg in (egs or []):
        if eg.superCluster().seed().seed().rawId()==seed_id:
            return eg
    return None

def combine_scs(*colls):
    seed_ids = {x.superCluster().seed().seed().rawId() for coll in colls if coll for x in coll}
    scs = [[get_eg(seed_id,coll) for coll in colls] for seed_id in seed_ids]
    return scs
    
def get_first_trig_obj_et(evtdata,filtname):
    objs = TrigTools.get_objs_passing_filter_aod(evtdata,filtname)
    if objs:
        return objs[0].et()
    else:
        return -1

class EcalULTree:
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
        self.evtdatavars = [
            TreeVar(self.tree,"metUL/F",UnaryFunc(partial(get_first_trig_obj_et,"hltPFMET120UL"))),
            TreeVar(self.tree,"metRun2/F",UnaryFunc(partial(get_first_trig_obj_et,"hltPFMET120Run2"))), 
            TreeVar(self.tree,"metRun3/F",UnaryFunc(partial(get_first_trig_obj_et,"hltPFMET120Run3"))),        
        ]   

        vars_ = {
            'et/F' : UnaryFunc(partial(ROOT.reco.RecoEcalCandidate.et)),
            'energy/F' : UnaryFunc(partial(ROOT.reco.RecoEcalCandidate.energy)),
            'rawEnergy/F' : UnaryFunc("superCluster().rawEnergy()"),
            'eta/F' : UnaryFunc(partial(ROOT.reco.RecoEcalCandidate.eta)),
            'phi/F' : UnaryFunc(partial(ROOT.reco.RecoEcalCandidate.phi)),
            'seedId/i':UnaryFunc("superCluster().seed().seed().rawId()")
        }
        max_egs=100
        egobjnr_name = "nrEG"
        self.egobj_nr = TreeVar(self.tree,egobjnr_name+"/i",UnaryFunc(partial(len)))
        self.egul_vars = []        
        self.egrun2_vars = []        
        self.egrun3_vars = []        
        for name,func in six.iteritems(vars_):
            self.egul_vars.append(TreeVar(self.tree,"egul_"+name,func,max_egs,egobjnr_name))
            self.egrun2_vars.append(TreeVar(self.tree,"egrun2_"+name,func,max_egs,egobjnr_name))
            self.egrun3_vars.append(TreeVar(self.tree,"egrun3_"+name,func,max_egs,egobjnr_name))
            
        self.eg_vars = [self.egul_vars,self.egrun2_vars,self.egrun3_vars]

        self.initialised = True

    def fill(self):
        if not self.initialised:
            self._init_tree()

        for var_ in self.evtvars:
            var_.fill(self.evtdata.event.object())
        for var_ in self.evtdatavars:
            var_.fill(self.evtdata)
        combined_egs = combine_scs(evtdata.get("ecalcand_ul"),evtdata.get("ecalcand_run2"),evtdata.get("ecalcand_run3"))

        self.egobj_nr.fill(combined_egs)            
        for objnr,objs in enumerate(combined_egs):
            for collnr,varcoll in enumerate(self.eg_vars):
                for var_ in varcoll:
                    if objs[collnr]:
                        var_.fill(objs[collnr],objnr)
                    else:
                        var_.clear()

        self.tree.Fill()
  


if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filenames',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--out','-o',default="output.root",help='output filename')
    args = parser.parse_args()
    std_products = []
   
    add_product(std_products,"ecalcand_ul","vector<reco::RecoEcalCandidate> ","hltEgammaCandidatesULUnseeded")
    add_product(std_products,"ecalcand_run2","vector<reco::RecoEcalCandidate> ","hltEgammaCandidatesRun2Unseeded")
    add_product(std_products,"ecalcand_run3","vector<reco::RecoEcalCandidate> ","hltEgammaCandidatesRun3Unseeded")
    add_product(std_products,"trig_sum","trigger::TriggerEvent","hltTriggerSummaryAOD")
    evtdata = EvtData(std_products,verbose=True)
    
    events = Events(CoreTools.get_filenames(args.in_filenames,args.prefix))
    nrevents = events.size()
    print("number of events",nrevents)    
    out_file = ROOT.TFile.Open(args.out,"RECREATE")
    tree = EcalULTree("ecalULTree",evtdata)
    for eventnr,event in enumerate(events):
        if eventnr%50000==0:
            print("{}/{}".format(eventnr,nrevents))
    
        evtdata.get_handles(event)

        tree.fill()
    out_file.Write()
