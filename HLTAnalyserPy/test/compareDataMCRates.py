from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import ROOT
import six
import re

from Analysis.HLTAnalyserPy.HistTools import get_from_canvas,get_from_file,dump_graphic_coord

nr_bunches_mc = 2666 #30MHz collision rate


def associate_hists(mc_hists,data_hists,qcd_hists=[],ewk_hists=[]):
    hists = {}
    for mc_hist_name,mc_hist in six.iteritems(mc_hists):
        path_name = re.match('([\w]+)(HLT_[\w]+)_v',mc_hist_name).group(2)
        hists[path_name] = {'mc' : mc_hist}
        if path_name+"_Hist" in data_hists:
            hists[path_name]["data"] = data_hists[path_name+"_Hist"]
        elif mc_hist_name in data_hists:
            hists[path_name]["data"] = data_hists[mc_hist_name]
            
        ewk_name = "rate_ewk_{}_v".format(path_name)
        qcd_name = "rate_qcd_{}_v".format(path_name)
        if ewk_name in ewk_hists:
            hists[path_name]["ewk"] = ewk_hists[ewk_name]
        if qcd_name in qcd_hists:
            hists[path_name]["qcd"] = qcd_hists[qcd_name]
            
        #matches = [hist for hist in data_hists if hist.GetName()==path_name]
#
            
    return hists
    

def make_data_mc_comp(data_hist,mc_hist):
   
    ROOT.AnaFuncs.setHistAttributes(mc_hist,ROOT.kAzure+8,2,8,ROOT.kAzure+8);
#    ROOT.AnaFuncs.setHistAttributes(mc_hist,ROOT.kBlue+2,2,8,ROOT.kBlue+2);
    ROOT.AnaFuncs.setHistAttributes(data_hist,ROOT.kOrange+7,2,22,ROOT.kOrange+7);
 
    ROOT.gStyle.SetOptStat(0)
    hist = ROOT.HistFuncs.plotWithRatio(
        ROOT.HistFuncs.HistOpts(data_hist,"Data (Fill 7065, 2544b)","LP"),
        ROOT.HistFuncs.HistOpts(mc_hist,"Monte Carlo (Fall18)","LP"),
        "")

    pads = get_from_canvas(ROOT.gROOT.FindObject("c1"),"TPad")
    pads[1].SetGridx()
    pads[1].SetGridy() 
    pads[0].SetGridy()
    hists = get_from_canvas(pads[0],"TH1D")
    hists[0].GetXaxis().SetLabelSize(0.047)
    hists[0].GetYaxis().SetLabelSize(0.047)
    hists[0].GetYaxis().SetTitleOffset(1.1)
    hists[0].GetYaxis().SetTitleSize(0.047)
    hists[0].GetYaxis().SetTitle("rate per bunch (Hz)")
    hists[0].GetYaxis().SetMaxDigits(4)
    ratio_hist = get_from_canvas(pads[1],"TH1D")[0]
    ratio_hist.GetXaxis().SetTitle("expected number of interactions")
    ratio_hist.GetYaxis().SetTitleOffset(0.55)
    ratio_hist.GetYaxis().SetTitle("data/mc")
    ratio_hist.GetYaxis().SetNdivisions(505)
    path_name = re.match('([\w]+)(HLT_[\w]+)_v',hists[0].GetName()).group(2)
    pads[0].Update()
    leg = get_from_canvas(pads[0],"TLegend")[0]
    ROOT.HistFuncs.XYCoord(0.130,0.669,0.517,0.781).setNDC(leg);
    pads[0].Update()
    ROOT.gROOT.FindObject("c1").Update()
    hlt_label = ROOT.HistFuncs.makeLabel(path_name,0.141,0.793,0.395,0.859)
    hlt_label.Draw()
    ROOT.gROOT.FindObject("c1").Update()
    
def make_mc_process_comp(tot_hist,qcd_hist,ewk_hist):
    ROOT.AnaFuncs.setHistAttributes(tot_hist,ROOT.kBlue+2,2,8,ROOT.kBlue+2);
    ROOT.AnaFuncs.setHistAttributes(qcd_hist,ROOT.kAzure+8,2,23,ROOT.kAzure+8);
    ROOT.AnaFuncs.setHistAttributes(ewk_hist,ROOT.kOrange+7,2,22,ROOT.kOrange+7);
 
    ROOT.gStyle.SetOptStat(0)
   
    numer_hists = ROOT.std.vector("HistFuncs::HistOpts")()
    numer_hists.push_back(ROOT.HistFuncs.HistOpts(qcd_hist,"QCD","LP"))
    numer_hists.push_back(ROOT.HistFuncs.HistOpts(ewk_hist,"W/Z","LP"))
    hist = ROOT.HistFuncs.plotWithRatio(
        numer_hists,
        ROOT.HistFuncs.HistOpts(tot_hist,"Total","LP"),
        "")
    pads = get_from_canvas(ROOT.gROOT.FindObject("c1"),"TPad")
    pads[1].SetGridx()
    pads[1].SetGridy()

    hists = get_from_canvas(pads[0],"TH1D")
    hists[0].GetXaxis().SetLabelSize(0.047)
    hists[0].GetYaxis().SetLabelSize(0.047)
    hists[0].GetYaxis().SetTitleOffset(1.1)
    hists[0].GetYaxis().SetTitleSize(0.047)
    hists[0].GetYaxis().SetTitle("rate per bunch (Hz)") 
    hists[0].GetYaxis().SetMaxDigits(4)
    ratio_hist = get_from_canvas(pads[1],"TH1D")[0]
    ratio_hist.GetXaxis().SetTitle("expected number of interactions")
#    ratio_hist.GetYaxis().SetTitleOffset(0.4)
    ratio_hist.GetYaxis().SetTitleOffset(0.55)
    ratio_hist.GetYaxis().SetRangeUser(0,1.1)
    ratio_hist.GetYaxis().SetTitle("rate fraction")
    path_name = re.match('([\w]+)(HLT_[\w]+)_v',hists[0].GetName()).group(2)
    pads[0].Update()
    leg = get_from_canvas(pads[0],"TLegend")[0]
    ROOT.HistFuncs.XYCoord(0.130,0.605,0.516,0.783).setNDC(leg);
    pads[0].Update()
    ROOT.gROOT.FindObject("c1").Update()
    hlt_label = ROOT.HistFuncs.makeLabel(path_name,0.141,0.793,0.395,0.859)
    hlt_label.Draw()
    ROOT.gROOT.FindObject("c1").Update()

def dict_iteration(hists,function,keys):
    for name,hist_pair in six.iteritems(hists):
        args = [hist_pair[key] for key in keys]
        yield function(*args)
        
def print_canvas(c1,out_name,types=[".gif",".C",".pdf",".png",".root"]):
    for ext in types:
        c1.Print(out_name+ext)
    


def plot_and_print(hists,function,keys,out_name):
    for name,hist_pair in six.iteritems(hists):
        args = [hist_pair[key] for key in keys]
        yield function(*args)
        yield print_canvas(ROOT.gROOT.FindObject("c1"),out_name.format(name))


if __name__ == "__main__":
    
  

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('--mc_input',required=True,help='mc input files')
    parser.add_argument('--data_input',required=True,help='data input file')
    args = parser.parse_args()

            
    
    mc_file = ROOT.TFile.Open(args.mc_input,'READ')
    data_file = ROOT.TFile.Open(args.data_input,'READ')

    mc_tot_hists = get_from_file(mc_file,starts_with="rate_HLT")
    mc_qcd_hists = get_from_file(mc_file,starts_with="rate_qcd_HLT")
    mc_ewk_hists = get_from_file(mc_file,starts_with="rate_ewk_HLT")
    [h.Scale(1./nr_bunches_mc) for n,h in six.iteritems(mc_tot_hists)]
    [h.Scale(1./nr_bunches_mc) for n,h in six.iteritems(mc_qcd_hists)]
    [h.Scale(1./nr_bunches_mc) for n,h in six.iteritems(mc_ewk_hists)]
    data_hists = get_from_file(data_file)   
    hists = associate_hists(mc_tot_hists,data_hists,qcd_hists = mc_qcd_hists,ewk_hists = mc_ewk_hists)

    for name,hist_pair in six.iteritems(hists):
     #   make_data_mc_comp(hist_pair['data'],hist_pair['mc'])
        make_mc_process_comp(hist_pair['mc'],hist_pair['qcd'],hist_pair['ewk'])


    
