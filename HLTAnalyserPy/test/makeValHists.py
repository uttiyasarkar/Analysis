from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from array import array
import argparse
import sys
import ROOT
import json
import re
import os
from collections import OrderedDict

from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
import Analysis.HLTAnalyserPy.HistTools as HistTools

def make_val_hists(in_filenames,out_name,label):
    evtdata = EvtData(phaseII_products,verbose=True)

    events = Events(in_filenames)
    nr_events = events.size()

    out_file = ROOT.TFile(out_name,"RECREATE")

    weight = 1.

    cutbins = [HistTools.CutBin("et()","Et",[20,100]),
               HistTools.CutBin("eta()","AbsEta",[0,1.4442,None,1.57,2.5,3.0],do_abs=True)]

    hist_meta_data = OrderedDict()
    desc = "Gen Matched Electrons"
    hists_genmatch = HistTools.create_histcoll(tag="GenMatch",cutbins=cutbins,desc=desc,norm_val=nr_events,meta_data=hist_meta_data)
    desc = "Gen Matched Electrons with Pixel Match"
    hists_genmatch_seed = HistTools.create_histcoll(tag="GenMatchSeed",cutbins=cutbins,desc=desc,norm_val=nr_events,meta_data=hist_meta_data)
    desc = "Gen Matched Electrons with GsfTrack"
    hists_genmatch_trk = HistTools.create_histcoll(add_gsf=True,tag="GenMatchTrk",cutbins=cutbins,desc=desc,norm_val=nr_events,meta_data=hist_meta_data)

    desc = "Non Gen Matched Electrons"
    hists_nogenmatch = HistTools.create_histcoll(tag="NoGenMatch",cutbins=cutbins,desc=desc,norm_val=nr_events,meta_data=hist_meta_data)
    desc = "Non Gen Matched Electrons with Pixel Match"
    hists_nogenmatch_seed = HistTools.create_histcoll(tag="NoGenMatchSeed",cutbins=cutbins,desc=desc,norm_val=nr_events,meta_data=hist_meta_data)
    desc = "Non Gen Matched Electrons with GsfTrack"
    hists_nogenmatch_trk = HistTools.create_histcoll(add_gsf=True,tag="NoGenMatchTrk",cutbins=cutbins,desc=desc,norm_val=nr_events,meta_data=hist_meta_data)

    
    for event_nr,event in enumerate(events):
        if event_nr%500==0:
            print("processing event {} / {}".format(event_nr,nr_events))
     
        evtdata.get_handles(event)

        gen_eles = GenTools.get_genparts(evtdata.get("genparts"),pid=11,antipart=True,
                                         status=GenTools.PartStatus.PREFSR)
        
        for egobj in evtdata.get("egtrigobjs"):
            egobj.et_gen = -1
            gen_match = CoreTools.get_best_dr_match(egobj,gen_eles,0.1)
            if gen_match:
                egobj.et_gen = gen_match.pt()
                hists_genmatch.fill(egobj,weight)
                if not egobj.seeds().empty():
                    hists_genmatch_seed.fill(egobj,weight)
                if not egobj.gsfTracks().empty():                    
                    hists_genmatch_trk.fill(egobj,weight)
            else:
                egobj.et_gen = -999
                hists_nogenmatch.fill(egobj,weight)
                if not egobj.seeds().empty():
                    hists_nogenmatch_seed.fill(egobj,weight)
                if not egobj.gsfTracks().empty():                    
                    hists_nogenmatch_trk.fill(egobj,weight)

    
    out_file.cd()
    eff_hists = []


    desc = "GsfTrack Match w.r.t Gen Efficiency"
    HistTools.make_effhists_fromcoll(numer=hists_genmatch_trk,denom=hists_genmatch,tag="Trk",dir_=out_file,out_hists = eff_hists,desc=desc,meta_data=hist_meta_data)                
    desc = "Pixel Match w.r.t Gen Efficiency"
    HistTools.make_effhists_fromcoll(numer=hists_genmatch_seed,denom=hists_genmatch,tag="Seed",dir_=out_file,out_hists = eff_hists,desc=desc,meta_data=hist_meta_data)

    hist_md_str = json.dumps(hist_meta_data)
    ROOT.gInterpreter.Declare("""
    void writeStr(TFile* file,std::string str,const std::string& name){
       file->WriteObjectAny(&str,"std::string",name.c_str());
    }""")
    ROOT.writeStr(out_file,hist_md_str,"meta_data")
    ROOT.writeStr(out_file,label,"label")
    out_file.Write()
#    with open(out_name.replace(".root",".json"),'w') as f:
 #       json.dump(hist_meta_data,f)

            

if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_names',nargs="+",help='input filenames')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix')
    parser.add_argument('--out_name','-o',required=True,help='output filename')
    parser.add_argument('--label','-l',default="",help="label for leg")
    args = parser.parse_args()

    in_filenames = CoreTools.get_filenames(args.in_names,args.prefix)
    
    if os.path.isdir(args.out_name):
        if args.in_names.find(".")!=-1:
            args.out_name = os.path.join(args.out_name,".".join(in_names[0].split(".")[:-1])+"_valhists.root")
        else:
            args.out_name = os.path.join(args.out_name,in_names[0]+"_valhists.root")
        print("auto renaming output to ".format(args.out_name))

    make_val_hists(in_filenames,args.out_name,args.label)
