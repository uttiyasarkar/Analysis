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
        
        

if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filenames',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--maxevents','-n',default=-1,type=int,help='max events, <0 is no limit')
    parser.add_argument('--verbose','-v',action='store_true',help='verbose printouts')
    parser.add_argument('--out_file','-o',default="output.root",help='output filename')
 #   parser.add_argument('--weights','-w',default=None,help='weights filename')
    args = parser.parse_args()
    
    products = []
    #add_product(products,"pu_sum","std::vector<PileupSummaryInfo>","addPileupInfo")
    #add_product(products,"pu_sum","std::vector<PileupSummaryInfo>","slimmedAddPileupInfo")
    add_product(products,"geninfo","GenEventInfoProduct","generator")
   # add_product(products,"pu_weight","double","stitchingWeight")
#    add_product(products,"trig_res","edm::TriggerResults","TriggerResults::RateSkim")
#    add_product(products,"trig_res","edm::TriggerResults","TriggerResults::HLTX")

    evtdata = EvtData(products,verbose=args.verbose)
    
    in_filenames = CoreTools.get_filenames(args.in_filenames,args.prefix)
    events = Events(in_filenames,maxEvents=args.maxevents)
    print("setup events")
    out_file = ROOT.TFile(args.out_file,"RECREATE")
    hists = []
    for histnr in range(0,100):
        hists.append(ROOT.TH1D("maxPtHat{}".format(histnr),"maxPtHat{}".format(histnr),200,0.,200.))

    hist_sample = ROOT.TH1D("randPtHat","randPtHat",200,0.,200)

    putree = ROOT.TTree("puTree","")
    tree_hard_pt_hat = array("f",[0])

    putree.Branch("hardPtHat",tree_hard_pt_hat,"hardPtHat/F")

    
    start_time = time.time()
    
    for eventnr,event in enumerate(events):
        if eventnr%10000==0:
            elapsed_time = time.time()-start_time
            est_finish = "n/a"
            if eventnr!=0 or elapsed_time==0:
                remaining = float(events.size()-eventnr)/eventnr*elapsed_time 
                est_finish = time.ctime(remaining+start_time+elapsed_time)
            print("{} / {} time: {:.1f}s, est finish {}".format(eventnr,events.size(),elapsed_time,est_finish))

        if args.maxevents>0 and eventnr>args.maxevents:
            break

        evtdata.get_handles(event)
        geninfo = evtdata.get("geninfo")
        tree_hard_pt_hat[0] = geninfo.qScale()
        
        
        putree.Fill()
        
       
       


    out_file.Write()
