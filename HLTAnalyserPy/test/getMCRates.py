from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import ROOT
import json
import random
import time
from array import array
from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products,add_product
from Analysis.HLTAnalyserPy.EvtWeights import EvtWeights

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.TrigTools as TrigTools
from Analysis.HLTAnalyserPy.Trees import HLTRateTree
        
        

if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filenames',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--maxevents','-n',default=-1,type=int,help='max events, <0 is no limit')
    parser.add_argument('--verbose','-v',action='store_true',help='verbose printouts')
    parser.add_argument('--out_file','-o',default="output.root",help='output filename')
    parser.add_argument('--weights','-w',default=None,help='weights filename')
    args = parser.parse_args()

    weight_calc = EvtWeights(args.weights)

    start_time = time.time()
    rates =  TrigTools.MenuPathRates(trig_res_name="trig_res_hlt")

    products = []
#    add_product(products,"pu_sum","std::vector<PileupSummaryInfo>","addPileupInfo")
    add_product(products,"pu_sum","std::vector<PileupSummaryInfo>","slimmedAddPileupInfo")
    add_product(products,"geninfo","GenEventInfoProduct","generator")
    add_product(products,"trig_res","edm::TriggerResults","TriggerResults::RateSkim")
#    add_product(products,"trig_res","edm::TriggerResults","TriggerResults::HLT")
    add_product(products,"trig_res_hlt","edm::TriggerResults","TriggerResults::HLT")

    evtdata = EvtData(products,verbose=args.verbose)
    
    in_filenames = CoreTools.get_filenames(args.in_filenames,args.prefix)
    events = Events(in_filenames,maxEvents=args.maxevents)

    out_file = ROOT.TFile(args.out_file,"RECREATE")
    rate_tree = HLTRateTree("rateTree",args.weights,"trig_res_hlt")

    for eventnr,event in enumerate(events):
        if eventnr%10000==0:
            elapsed_time = time.time()-start_time
            est_finish = "n/a"
            if eventnr!=0 or elapsed_time==0:
                remaining = float(events.size()-eventnr)/eventnr*elapsed_time 
                est_finish = time.ctime(remaining+start_time+elapsed_time)
            print("{} / {} time: {:.1f}s, est finish {}".format(eventnr,events.size(),elapsed_time,est_finish))
        
        evtdata.get_handles(event)
        pusum_intime = [x for x in evtdata.get("pu_sum") if x.getBunchCrossing()==0]
        
        weight = weight_calc.weight(evtdata, nr_expt_pu=pusum_intime[0].getTrueNumInteractions())
#        weight = 1.0
        rates.fill(evtdata,weight)
        rate_tree.fill(evtdata)
    
    out_file.Write()
    with open("test.json",'w') as f:
        json.dump(rates.get_results(),f)

