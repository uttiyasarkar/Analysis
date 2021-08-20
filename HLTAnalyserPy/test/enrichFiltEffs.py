from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import ROOT
import json
import random
import re
import math
from array import array
from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products,add_product

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.TrigTools as TrigTools
        
def get_eff_str(nr_pass,nr_tot):
    nr_fail = nr_tot - nr_pass
    eff = float(nr_pass)/nr_tot
    eff_err = math.sqrt(float(nr_fail**2*nr_pass + nr_pass**2*nr_fail))/(nr_tot**2)
    return "{:0.6f} +/- {:0.6f}".format(eff,eff_err)


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
    
    products = []
    add_product(products,"pu_sum","std::vector<PileupSummaryInfo>","addPileupInfo")
    add_product(products,"geninfo","GenEventInfoProduct","generator")
    add_product(products,"pu_weight","double","stitchingWeight")
    add_product(products,"trig_res","edm::TriggerResults","TriggerResults::RateSkim")

    evtdata = EvtData(products,verbose=args.verbose)
    
    in_filenames = CoreTools.get_filenames(args.in_filenames,args.prefix)
    events = Events(in_filenames)                                
    gen_filters = TrigTools.TrigResults(["Gen_QCDMuGenFilter",
                                         "Gen_QCDBCToEFilter",
                                         "Gen_QCDEmEnrichingFilter",
                                         "Gen_QCDEmEnrichingNoBCToEFilter"])
    dataset_name = re.search(r'(.+)(_\d+_EDM.root)',in_filenames[0].split("/")[-1]).groups()[0]
    nr_tot = 0.
    nr_pass_em = 0.
    nr_pass_mu = 0.
    nr_pass_emmu = 0.
    for eventnr,event in enumerate(events):
        if eventnr%10000==0 and False:
            print("{} / {}".format(eventnr,events.size()))

        if args.maxevents>0 and eventnr>args.maxevents:
            break

        evtdata.get_handles(event)
        gen_filters.fill(evtdata)
        
        pass_em = gen_filters.result("Gen_QCDEmEnrichingNoBCToEFilter")
        pass_mu = gen_filters.result("Gen_QCDMuGenFilter")
        
        nr_tot +=1
        if pass_em:
            nr_pass_em +=1
        if pass_mu:
            nr_pass_mu +=1
        if pass_em and pass_mu:
            nr_pass_emmu +=1

    em_eff_str = get_eff_str(nr_pass_em,nr_tot)
    mu_eff_str = get_eff_str(nr_pass_mu,nr_tot)
    emmu_eff_str = get_eff_str(nr_pass_emmu,nr_tot)
    


    print("{:105} {:6d} {:6d} {:6d} {:5d} {} {} {}".format(dataset_name,int(nr_tot),int(nr_pass_em),int(nr_pass_mu),int(nr_pass_emmu),em_eff_str,mu_eff_str,emmu_eff_str))

