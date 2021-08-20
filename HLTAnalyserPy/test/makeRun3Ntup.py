import argparse
import sys
from DataFormats.FWLite import Events, Handle
import ROOT
from functools import partial
import math

from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles, std_products,add_product
from Analysis.HLTAnalyserPy.EvtWeights import EvtWeights
import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
import Analysis.HLTAnalyserPy.HistTools as HistTools
import Analysis.HLTAnalyserPy.TrigTools as TrigTools
import Analysis.HLTAnalyserPy.GsfTools as GsfTools
import Analysis.HLTAnalyserPy.IsolTools as IsolTools
import Analysis.HLTAnalyserPy.PixelMatchTools as PixelMatchTools
from Analysis.HLTAnalyserPy.EgHLTRun3Tree import EgHLTRun3Tree


def main():
    
    CoreTools.load_fwlitelibs();

    parser = argparse.ArgumentParser(description='prints E/gamma pat::Electrons/Photons us')
    parser.add_argument('in_filenames',nargs="+",help='input filename')
    parser.add_argument('--out_filename','-o',default="output.root",help='output filename')
    parser.add_argument('--min_et','-m',default=10.,type=float,help='minimum eg et') 
    parser.add_argument('--weights','-w',default=None,help="weights filename")
    parser.add_argument('--report','-r',default=10,type=int,help="report every N events")
    parser.add_argument('--prefix','-p',default="",help='prefix to append to input files')
    args = parser.parse_args()
        
    evtdata = EvtData(std_products,verbose=True)
    weights = EvtWeights(args.weights) if args.weights else None
    

    out_file = ROOT.TFile(args.out_filename,"RECREATE")

    eghlt_tree = EgHLTRun3Tree('egHLTRun3Tree',evtdata,args.min_et,weights)
    eghlt_tree.add_eg_vars({})
    

    events = Events(CoreTools.get_filenames(args.in_filenames,args.prefix))
    nr_events = events.size()
    for event_nr,event in enumerate(events):
        if event_nr%args.report==0:
            print("processing event {} / {}".format(event_nr,nr_events))
        evtdata.get_handles(event)
        eghlt_tree.fill()

    out_file.Write()

if __name__ == "__main__":
    main()
