from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import ROOT
import json
from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products,add_product

import Analysis.HLTAnalyserPy.CoreTools as CoreTools

def get_nrdups_in_event(pu_sum):
    nr_dup_evts = 0
    nr_uniq_evts = 0
    uniq_pu_evts = {}
    for pu_bx in pu_sum:
        evt_ids = pu_bx.getPU_EventID()
        for evt_id in evt_ids:
            if evt_id.luminosityBlock() not in uniq_pu_evts:
                uniq_pu_evts[evt_id.luminosityBlock()] = set()
                
                if evt_id.event() in uniq_pu_evts[evt_id.luminosityBlock()]:
                    nr_dup_evts += 1
                else:
                    nr_uniq_evts +=1
                    uniq_pu_evts[evt_id.luminosityBlock()].add(evt_id.event())
    return nr_dup_evts


def check_pileup(in_filenames,prefix,maxevents=-1,verbose=False):

    products = []
    add_product(products,"pu_sum","std::vector<PileupSummaryInfo","addPileupInfo")
    evtdata = EvtData(products,verbose=verbose)
    
    in_filenames = CoreTools.get_filenames(in_filenames,prefix)
    events = Events(in_filenames)
    
    uniq_pu_evts = {}
    nr_dup_evts = 0
    nr_uniq_evts = 0
    nr_tot_evts = 0
    expect_uniq_evts = 0
    nr_bad_evts = 0

    uniq_list = []
    dup_list = []

    for eventnr,event in enumerate(events):
        if eventnr%1000==0:
            expect_uniq_evts = eventnr*200*7
            if verbose:
                print("number of events",eventnr,"number of unique PU events",nr_uniq_evts," expected unique events",expect_uniq_evts," number dups ",nr_dup_evts,"number of bad events",nr_bad_evts)

        if maxevents>0 and eventnr>maxevents:
            break

        evtdata.get_handles(event)
        pu_sum  = evtdata.get("pu_sum")

        nr_tot_evts +=1 
        nrdups_evt = get_nrdups_in_event(pu_sum)

        if nrdups_evt >0:
            bad_events+=1
            if verbose:
                print("event with {} duplicated PU events",nrdups_evt)

        for pu_bx in pu_sum:
            evt_ids = pu_bx.getPU_EventID()
            for evt_id in evt_ids:
                if evt_id.luminosityBlock() not in uniq_pu_evts:
                    uniq_pu_evts[evt_id.luminosityBlock()] = set()
                
                if evt_id.event() in uniq_pu_evts[evt_id.luminosityBlock()]:
                    nr_dup_evts += 1                    
                else:
                    nr_uniq_evts +=1
                    uniq_pu_evts[evt_id.luminosityBlock()].add(evt_id.event())
        dup_list.append(nr_dup_evts)
        uniq_list.append(nr_uniq_evts)

    return {"nr_tot" : nr_tot_evts,
            "nr_pu_uniq" : nr_uniq_evts,
            "nr_pu_dup" : nr_dup_evts,
            "nr_bad" : nr_bad_evts,
            "nr_pu_uniq_vs_evt" : uniq_list,
            "nr_pu_dup_vs_evt" : dup_list,
            }


if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filenames',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--maxevents','-n',default=-1,help='max events, <0 is no limit')
    parser.add_argument('--verbose','-v',action='store_true',help='verbose printouts')
    parser.add_argument('--json','-j',action='store_true',help='print res as json')
    args = parser.parse_args()

    res = check_pileup(args.in_filenames,args.prefix,args.maxevents,args.verbose)
    
    if args.json:
        print(json.dumps(res))
    else:
        print("nr tot {r[nr_tot]} nr unique PU {r[nr_pu_uniq]} expected {expected}, nr dup PU {r[nr_pu_dup]} nr bad {r[nr_bad]}".format(r=res,expected=res['nr_tot']*200*7))
          
