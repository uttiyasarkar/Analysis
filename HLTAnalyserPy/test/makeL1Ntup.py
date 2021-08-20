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

import Analysis.HLTAnalyserPy.L1Tools as L1Tools
from Analysis.HLTAnalyserPy.CoreTools import UnaryFunc
from Analysis.HLTAnalyserPy.NtupTools import TreeVar
from Analysis.HLTAnalyserPy.EvtWeights import EvtWeights
from functools import partial
import itertools
from array import array
import six

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

class L1Tree:
    def __init__(self,tree_name,evtdata,weights=None):
        self.tree = ROOT.TTree(tree_name,'')
        self.evtdata = evtdata
        self.weights = weights
        self.initialised = False
    def _init_tree(self):
        self.evtvars = [
            TreeVar(self.tree,"runnr/i",UnaryFunc("eventAuxiliary().run()")),
            TreeVar(self.tree,"lumiSec/i",UnaryFunc("eventAuxiliary().luminosityBlock()")),
            TreeVar(self.tree,"eventnr/i",UnaryFunc("eventAuxiliary().event()")),        
        ]
        self.evtdatavars = []
        if self.weights:
            self.evtdatavars.append(TreeVar(self.tree,"weight/F",self.weights.weight)),
            self.evtdatavars.append(TreeVar(self.tree,"filtweight/F",self.weights.filtweight))
      #  self.evtdatavars.append(TreeVar(self.tree,"genPtHat/F",UnaryFunc('get("geninfo").qScale()')))            
      #  max_pthats = 400
      #  self.nr_pthats = TreeVar(self.tree,"nrPtHats/i",UnaryFunc(partial(len)))
      #   self.pthats = TreeVar(self.tree,"ptHats/F",None,maxsize=max_pthats,sizevar="nrPtHats")


        scales_params = L1Tools.make_egscale_dict()
        l1pho_vars_names = {
            'et/F' : UnaryFunc("et()"),
            'eta/F' : UnaryFunc("eta()"),
            'phi/F' : UnaryFunc("phi()"),
            'hwQual/F' : UnaryFunc("EGRef().hwQual()"),
            'trkIsol/F' : UnaryFunc('trkIsol()'),
            'trkIsolPV/F' : UnaryFunc('trkIsolPV()'),
            'passQual/b' : L1Tools.pass_eg_qual,
            'passIsol/b' : L1Tools.pass_eg_isol,
            
            'etThresIso/F' : UnaryFunc(partial(L1Tools.eg_thres,scales_params,use_iso=True)),
            'etThresNonIso/F' : UnaryFunc(partial(L1Tools.eg_thres,scales_params,use_noniso=True)),
            'etThres/F' : UnaryFunc(partial(L1Tools.eg_thres,scales_params))            
            }
        max_l1egs = 2000
        nrpho_name = "nrL1EGs"
        nrele_name = "nrL1Eles"
        self.l1pho_nr = TreeVar(self.tree,nrpho_name+"/i",UnaryFunc(partial(len)))
       # self.l1ele_nr = TreeVar(self.tree,nrele_name+"/i",UnaryFunc(partial(len)))
        self.l1pho_vars = []
        for name,func in six.iteritems(l1pho_vars_names):
            self.l1pho_vars.append(TreeVar(self.tree,"eg_l1pho_"+name,func,max_l1egs,nrpho_name))   
        l1ele_vars_names = dict(l1pho_vars_names)
        l1ele_vars_names.update({
            'vz/F' : UnaryFunc('trkzVtx()'),
            'trkCurve/F' : UnaryFunc('trackCurvature()')        
        })
        self.initialised = True

    def fill(self):
        if not self.initialised:
            self._init_tree()

        for var_ in self.evtvars:
            var_.fill(self.evtdata.event.object())
        for var_ in self.evtdatavars:
            var_.fill(self.evtdata)

        
        l1phos_eb  = self.evtdata.get("l1tkphos_eb")
        l1phos_hgcal = self.evtdata.get("l1tkphos_hgcal") 
        l1phos = [eg for eg in itertools.chain(l1phos_eb,l1phos_hgcal)]
       # l1eles_eb  = self.evtdata.get("l1tkeles_eb")
       # l1eles_hgcal = self.evtdata.get("l1tkeles_hgcal") 
       # l1eles = [eg for eg in itertools.chain(l1eles_eb,l1eles_hgcal)]
#        self.l1ele_nr.fill(l1eles)
        self.l1pho_nr.fill(l1phos)

        for objnr,l1pho_obj in enumerate(l1phos):
            for var_ in self.l1pho_vars:
                var_.fill(l1pho_obj,objnr)
     #   for var_ in self.l1ele_vars:
       #     var_.fill(l1ele_obj,objnr)
        self.tree.Fill()

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
    
    out_file = ROOT.TFile.Open(args.out,"RECREATE")
    tree = L1Tree("l1Tree",evtdata)
    for event in events:
        evtdata.get_handles(event)
        tree.fill()
    out_file.Write()
        
