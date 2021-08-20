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
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,std_products

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
import Analysis.HLTAnalyserPy.HistTools as HistTools

if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filename',nargs="+",help='input filename')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--out','-o',default="output.root",help='output filename')
    args = parser.parse_args()

    evtdata = EvtData(std_products,verbose=True)
    
    in_filenames_with_prefix = ['{}{}'.format(args.prefix,x) for x in args.in_filename]
    events = Events(in_filenames_with_prefix)

    out_file = ROOT.TFile(args.out,"RECREATE")

    hists_eb_genmatch = HistTools.create_histcoll(is_barrel=True,tag="EBGenMatch")
    hists_ee_genmatch = HistTools.create_histcoll(is_barrel=False,tag="EEGenMatch")
    
    hists_eb_genmatch_seed = HistTools.create_histcoll(is_barrel=True,tag="EBGenMatchSeed")
    hists_ee_genmatch_seed = HistTools.create_histcoll(is_barrel=False,tag="EEGenMatchSeed")
    hists_eb_genmatch_trk = HistTools.create_histcoll(is_barrel=True,add_gsf=True,tag="EBGenMatchTrk")
    hists_ee_genmatch_trk = HistTools.create_histcoll(is_barrel=False,add_gsf=True,tag="EEGenMatchTrk")
    
    for event_nr,event in enumerate(events):
        evtdata.get_handles(event)
        for egobj in evtdata.get("egtrigobjs"):
            if egobj.gsfTracks().size()!=0:
                gen_match = GenTools.match_to_gen(egobj.eta(),egobj.phi(),evtdata.handles.genparts.product(),pid=11)[0]
                if gen_match:
                    gen_pt = gen_match.pt()
                    hists_eb_genmatch.fill(egobj)
                    hists_ee_genmatch.fill(egobj)
                    
                    if not egobj.seeds().empty():
                        hists_eb_genmatch_seed.fill(egobj)
                        hists_ee_genmatch_seed.fill(egobj)
                    if not egobj.gsfTracks().empty():                    
                        hists_eb_genmatch_trk.fill(egobj)
                        hists_ee_genmatch_trk.fill(egobj)

                else:
                    gen_pt = -1

        gen_eles = GenTools.get_genparts(evtdata.get("genparts"))
        if len(gen_eles)!=2:
            print("event missing electrons",event_nr)
    
    out_file.cd()
    eff_hists = []
    HistTools.make_effhists_fromcoll(numer=hists_eb_genmatch_trk,denom=hists_eb_genmatch,tag="EBTrk",dir_=out_file,out_hists = eff_hists)
    HistTools.make_effhists_fromcoll(numer=hists_ee_genmatch_trk,denom=hists_ee_genmatch,tag="EETrk",dir_=out_file,out_hists = eff_hists)
    HistTools.make_effhists_fromcoll(numer=hists_eb_genmatch_seed,denom=hists_eb_genmatch,tag="EBSeed",dir_=out_file,out_hists = eff_hists)
    HistTools.make_effhists_fromcoll(numer=hists_ee_genmatch_seed,denom=hists_ee_genmatch,tag="EESeed",dir_=out_file,out_hists = eff_hists)
    out_file.Write()
            
         #   print(GenTools.genparts_to_str(evtdata.get("genparts"),-1))
            #for genpart in evtdata.get("genparts"):
                #for mo in range(0,genpart.numberOfMothers()):
                    #ref = genpart.motherRef(0)
                    #print("sucess {}".format(ref.pt()))
              #  print("{} {} {} {} {}".format(genpart.pdgId(),
                #print("{} {} {} {} {}".format(egobj.pt(),egobj.eta(),egobj.phi(),egobj.gsfTracks()[0].pt(),gen_pt))
        
