from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import ROOT
import json
import pickle
import os

from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products,add_product

import Analysis.HLTAnalyserPy.CoreTools as CoreTools

class PythonObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (list, dict, str, unicode, int, float, bool, type(None))):
            return json.JSONEncoder.default(self, obj)
        return {'_python_object': pickle.dumps(obj)}

def as_python_object(dct):
    if '_python_object' in dct:
        return pickle.loads(str(dct['_python_object']))
    return dct



class PUEventsInBX(object):
    def __init__(self,pu_sum):
        self.evt_ids = {x for x in pu_sum[3].getPU_EventID()}
        
    def overlap(self,rhs):
        return self.evt_ids.intersection(rhs.evt_ids)
        
    def nr_overlap(self,rhs):
        return len(self.overlap(rhs))
        
def read_pileup(in_filenames,prefix,maxevents=-1,verbose=False):

    products = []
    add_product(products,"pu_sum","std::vector<PileupSummaryInfo","addPileupInfo")
    evtdata = EvtData(products,verbose=verbose)
    
    in_filenames = CoreTools.get_filenames(in_filenames,prefix)
    print(in_filenames)
    events = Events(in_filenames)
    
    pu_list = []

    for eventnr,event in enumerate(events):
        if eventnr%1000==0 and verbose:
            print("number of events",eventnr)

        if maxevents>0 and eventnr>maxevents:
            break

        evtdata.get_handles(event)
        pu_sum  = evtdata.get("pu_sum")

#        pu_list.append(PUEventsInBX(pu_sum))
        pu_list.append({(x.event(),x.luminosityBlock()) for x in pu_sum[3].getPU_EventID()})

    return pu_list

if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filenames',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--maxevents','-n',default=-1,help='max events, <0 is no limit')
    parser.add_argument('--verbose','-v',action='store_true',help='verbose printouts')
    parser.add_argument('--out','-o',default='output.json',help='output file')
    parser.add_argument('--out_root','-r',default='output.root',help='output root file')
    args = parser.parse_args()

    if not os.path.exists(args.out):
        print("reading output")
        pu_list = read_pileup(args.in_filenames,args.prefix,args.maxevents,args.verbose)
    
        with open(args.out,'w') as f:
            json.dump(pu_list,f,cls=PythonObjectEncoder)
    
    with open(args.out,'r') as f:
        pu_list = json.load(f,object_hook=as_python_object)
        

    ref_event_nr = 0
    ref_event = pu_list[ref_event_nr]
    pu_list.pop(ref_event_nr)

    root_file = ROOT.TFile(args.out_root,"RECREATE")
    hist = ROOT.TH1D("overlapHist","# in time PU events overlapping with a given event;# overlap PU events;#events",251,-0.5,250.5)

    for event in pu_list:
        nr_overlap = len(ref_event.intersection(event))
        hist.Fill(nr_overlap)
    root_file.Write()


