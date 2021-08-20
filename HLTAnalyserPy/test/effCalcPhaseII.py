#!/usr/bin/env python

import ROOT
import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import argparse
import os
import shutil


    
def gen_html(canvases_to_draw,**kwargs):
    
    html_str="""
<!DOCTYPE html>
<html lang="en">
<head>
    
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
 
<title>E/gamma Phase-II CutFlow</title>
 
<script src="https://root.cern/js/latest/scripts/JSRootCore.js" type="text/javascript"></script>
 
<script type='text/javascript'> 
  var filename = "output.root";
  JSROOT.gStyle.fOptStat = 0
  JSROOT.OpenFile(filename, function(file) {{
    {canvas_draw_js}
  }});
  </script>
</head>
 
<body>

<h1> Introduction </h1>

This is a result of an E/gamma HLT PhaseII set of cuts
It will list the cuts for the barrel and endcap as well as their resulting efficiencies and distributions

This was done with <a href="https://gitlab.cern.ch/sharper/HLTAnalyserPy">HLTAnalyserPy</a> and the script used to generate these plots is <a href="script.py">here</a> although note there is currently an issue with displaying it on a web browser as it has embedded html

{eb_intro}
{ee_intro}
{eb_eff}
{ee_eff}
{eb_dist}
{ee_dist}

</body>
 
</html>
    """
    canvas_pad_str_base = '<div id="{name}" style="width:800px; height:600px"></div>'
    canvas_draw_str_base = """  
    file.ReadObject("{name}", function(obj) {{
       JSROOT.draw("{name}", obj, "");
    }});"""
    
    canvas_draw_str = "".join([canvas_draw_str_base.format(name=c) for c in canvases_to_draw])
    
    
    return html_str.format(canvas_draw_js=canvas_draw_str,**kwargs)
          
def process_histcoll(hists,collname,canvases_to_draw):
   
    html_intro = ["<h2>{} Cut Summary</h2>".format(collname)]
    html_dist_hists = ["<h2>{} Distributions</h2>".format(collname)]
    html_eff_hists = ["<h2>{} Efficiencies</h2>".format(collname)]
    html_toteff_hists = []
    # toc=[] #need to fix
    prev_hists = None
    for cut in hists:
        html_intro.append("<br>{} : {} ".format(cut.cutName(),cut.cutStr().replace("\n","<br>   ")))
        if prev_hists:
            html_eff_hists.append("<h3>{} Cut Efficiency w.r.t Previous Cut</h3>".format(cut.cutName()))
            html_eff_hists.append("sel: {}<br>".format(cut.cutStr().replace("\n","<br>")))
            html_toteff_hists=["<h3>{} Cut Efficiency w.r.t {} Cut</h3>".format(cut.cutName(),hists[0].cutName())]
            
        html_dist_hists.append("<h3>Distributions after Applying {} Cut</h3>".format(cut.cutName()))
        html_dist_hists.append("sel: {}<br>".format(cut.cutStr().replace("\n","<br>")))
        
        for histindx,(varname,hist) in enumerate(cut.hists()):
            hist.SetLineColor(1)
            hist.SetMarkerStyle(8) 
            canvas_name = "{}Canvas".format(hist.GetName())
            c1 = ROOT.TCanvas(canvas_name,"c1",900,600)
            hist.Draw("HISTE")
            c1.Write()
            canvases_to_draw.append(canvas_name)  
            html_dist_hists.append('<div id="{name}" style="width:400px; height:300px; display:inline-block"></div>'.format(name=canvas_name))
            
            if prev_hists:
                
                effhist= hist.Clone("{}IncEff".format(hist.GetName()))
                effhist.Sumw2()
                effhist.SetDirectory(0)
                effhist.Divide(effhist,prev_hists[histindx].second.GetPtr(),1,1,"B")
                effhist.GetYaxis().SetTitle("Efficiency w.r.t Prev Cut")
                canvas_name = "{}Canvas".format(effhist.GetName())
                c1 = ROOT.TCanvas(canvas_name,"c1",900,600)
                effhist.Draw("EP")
                c1.Write()
                canvases_to_draw.append(canvas_name)            
                html_eff_hists.append('<div id="{name}" style="width:400px; height:300px; display:inline-block"></div>'.format(name=canvas_name))

                efftothist= hist.Clone("{}Eff".format(hist.GetName()))
                efftothist.Sumw2()
                efftothist.SetDirectory(0)
                efftothist.Divide(efftothist,hists[0].hists()[histindx].second.GetPtr(),1,1,"B")
                efftothist.GetYaxis().SetTitle("Efficiency w.r.t {}".format(cut.hists()[0].first))
                canvas_name = "{}Canvas".format(efftothist.GetName())
                c1 = ROOT.TCanvas(canvas_name,"c1",900,600)
                efftothist.Draw("EP")
                c1.Write()
                canvases_to_draw.append(canvas_name)  

                html_toteff_hists.append('<div id="{name}" style="width:400px; height:300px; display:inline-block"></div>'.format(name=canvas_name))
        html_eff_hists.extend(html_toteff_hists)
        prev_hists = cut.hists()

    return "\n".join(html_intro),"\n".join(html_eff_hists),"\n".join(html_dist_hists)

def make_webpage_html(hists_eb,hists_ee):
    canvases_to_draw=[]
    eb_intro,eb_eff,eb_dist = process_histcoll(hists_eb,"EB",canvases_to_draw)
    ee_intro,ee_eff,ee_dist = process_histcoll(hists_ee,"EE",canvases_to_draw)
    return gen_html(canvases_to_draw,
                    eb_intro=eb_intro,eb_eff=eb_eff,eb_dist=eb_dist,
                    ee_intro=ee_intro,ee_eff=ee_eff,ee_dist=ee_dist)
    

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='prints E/gamma pat::Electrons/Photons us')
    parser.add_argument('in_filenames',nargs="+",help='input filename')
    parser.add_argument('--outdir','-o',default="./",help='output dir')
    parser.add_argument('--min_et','-m',default=20.,type=float,help='minimum eg et') 
    parser.add_argument('--weights','-w',default=None,help="weights filename")
    parser.add_argument('--report','-r',default=10,type=int,help="report every N events")
    args = parser.parse_args()
    
    #which was rather the point of doing all of this :)
    ROOT.ROOT.EnableImplicitMT()

    filenames = CoreTools.get_filenames_vec(args.in_filenames)
    df = ROOT.RDataFrame("egHLTTree",filenames)
    
    #first we define our CutFlow objects, this is still a work in progress
    #a CutFlow object is a series of cuts with an overal collection name
    #the CutFlow object can also be given histograms which will make for all
    #objects passing the a given cut
    #for example we will want to see et, eta and phi histograms after each cut so we will define 
    #them

    #note there is a syntax where at the end of the variable you put {} which is then internally replaced as approprate. This is for all variables
    
    ebCutFlow = ROOT.FiltFuncs.CutFlow("eb",1) 
    
    ebCutFlow.addHist1D("etHist",";E_{T} [GeV];# events",100,0,100,"eg_et{}")
    ebCutFlow.addHist1D("etaHist",";#eta;# events",60,-3.,3,"eg_eta{}")
    ebCutFlow.addHist1D("phiHist",";#phi [rad];# events",64,-3.2,3.2,"eg_phi{}")

    #now we add the cuts we want the object to pass 
    #this basically will do a df.Define(cutname,prevcut && cutexpres)
    ebCutFlow.addCut("eta","abs(eg_eta{})<1.5")
    ebCutFlow.addCut("sigmaIEtaIEta","eg_sigmaIEtaIEta{}<0.011")
    #sometimes a cut is long so we can defined new variables to simplify things
    #for example by splitting the hadem cut into three lines its much easier to follow
    ebCutFlow.addDef("hadem_loweta","abs(eg_eta{}) <1.0 && eg_hcalHForHoverE{}<0.75+0.03*eg_energy{}")
    ebCutFlow.addDef("hadem_higheta","abs(eg_eta{}) >1.0 && eg_hcalHForHoverE{}<2.25+0.03*eg_energy{}")
    ebCutFlow.addCut("hadem","(eb_hadem_loweta || eb_hadem_higheta)")
    ebCutFlow.addCut("ecalIso","eg_ecalPFIsol_default{}<1.75+0.03*eg_et{}")
    ebCutFlow.addCut("hcalIso","eg_hcalPFIsol_default{}<2.5+0.03*eg_et{}")
    ebCutFlow.addCut("pm","eg_pms2{}<10000000")
    ebCutFlow.addCut("pmS2","eg_pms2{}<70")
    ebCutFlow.addCut("ep","eg_invEInvP{}<0.012")
    ebCutFlow.addCut("dEtaIn","eg_trkDEtaSeed{}<0.004")
    ebCutFlow.addCut("dPhiIn","eg_trkDPhi{}<0.02")
    ebCutFlow.addCut("nLayersIT","eg_nLayerIT{}>=2")
    ebCutFlow.addDef("chi2_loweta","abs(eg_eta{}) < 0.8 && eg_normChi2{}<3")
    ebCutFlow.addDef("chi2_higheta","abs(eg_eta{}) > 0.8 && eg_normChi2{}<50")
    ebCutFlow.addCut("chi2","(eb_chi2_loweta || eb_chi2_higheta)")
    ebCutFlow.addCut("trkIsol","eg_hltisov6{}<5")
    ebCutFlow.addCut("l1TrkIso","eg_l1iso{}<6")

    eeCutFlow = ROOT.FiltFuncs.CutFlow("ee",1)
    eeCutFlow.addHist1D("etHist",";E_{T} [GeV];# events",100,0,100,"eg_et{}")
    eeCutFlow.addHist1D("etaHist",";#eta;# events",60,-3.,3,"eg_eta{}")
    eeCutFlow.addHist1D("phiHist",";#phi [rad];# events",64,-3.2,3.2,"eg_phi{}")
    eeCutFlow.addCut("eta","abs(eg_eta{})>1.5")
    eeCutFlow.addCut("hadem","eg_hgcalHForHoverE{}<5+0.10*eg_energy{}")
    eeCutFlow.addCut("sigma2vv","eg_sigma2vv{}<0.8")
    eeCutFlow.addCut("sigma2ww","eg_sigma2ww{}<81")
    eeCutFlow.addCut("hgcalIso","eg_hgcalPFIsol_default{}<5")
    eeCutFlow.addCut("pm","eg_pms2{}<10000000")
    eeCutFlow.addCut("pmS2","eg_pms2{}<45")
    eeCutFlow.addCut("ep","eg_invEInvP{}<0.011")   
    eeCutFlow.addCut("nrMissHits","eg_trkMissHits{}<=1") 
    eeCutFlow.addCut("dEtaIn","eg_trkDEtaSeed{}<0.005")
    eeCutFlow.addCut("dPhiIn","eg_trkDPhi{}<0.023")
    eeCutFlow.addCut("nLayersIT","eg_nLayerIT{}>=2")
    eeCutFlow.addCut("chi2","eg_normChi2{}<50")
    eeCutFlow.addCut("trkIso","eg_hltisov6{}<5")
    eeCutFlow.addCut("l1TrkIso","eg_l1iso{}<6")
    
    
    #our CutFlow object right now is a series of instructions on 
    #how to define a cut on an df dataframe
    #now we need to define things on the dataframe via the define function
    df = ebCutFlow.define(ROOT.RDF.AsRNode(df))
    df = eeCutFlow.define(ROOT.RDF.AsRNode(df))
    #we can also do other defines, this is us defining a cut where we either
    #pass eb or ee (in the future we will add this functionaly direct to our cutflow objects
    df = df.Define("ebee_l1TrkIso","eb_l1TrkIso || ee_l1TrkIso")
    #in RDataFrame if you want to plot a column (ie variable) passing a selection, you need 
    #to defined it which we do here as an example
    df = df.Define("egcut_et","eg_et[ebee_l1TrkIso]")
    df = df.Define("egcut_eb_et","eg_et[eb_l1TrkIso]")
    df = df.Define("egcut_ee_et","eg_et[ee_l1TrkIso]")
    hist_et = df.Histo1D(("etHist","Et",100,0.,100.),"egcut_et")
    hist_eb_et = df.Histo1D(("etHistEB","Et",100,0.,100.),"egcut_eb_et")
    hist_ee_et = df.Histo1D(("etHistEE","Et",100,0.,100.),"egcut_ee_et")


    #so far we are always running on the entire datafame
    #here we could filter it to only get the entries which have passed our cuts
    df_eb_filter  = ebCutFlow.filter(ROOT.RDF.AsRNode(df))
    df_ee_filter  = eeCutFlow.filter(ROOT.RDF.AsRNode(df))
    df_eb_filter.Report()
    df_ee_filter.Report()

    #now here is how we want to get the et/eta/phi hists of objects passing each cut
    #this is a std::vector<CutHistColl> which then contains the three (or more histograms)
    #we specified for each cut
    hists_eb = ebCutFlow.hists(ROOT.RDF.AsRNode(df))
    hists_ee = eeCutFlow.hists(ROOT.RDF.AsRNode(df))

    #now we should only access the histograms once everything is ready
    #doing an action now means the dataframe loop will run and all histograms will be filled
    print("now drawing")
    hist_et.Draw()
    hist_eb_et.Draw("SAME")
    hist_ee_et.Draw("SAME")

    #now we are making our summary website
    if not os.path.isdir(args.outdir):
        os.mkdir(args.outdir)

    output_root = ROOT.TFile.Open(os.path.join(args.outdir,"output.root"),"RECREATE")
    html_str = make_webpage_html(hists_eb,hists_ee)
    output_root.Write()
    with open(os.path.join(args.outdir,"index.html"),"w") as f:
        f.write(html_str)
    shutil.copyfile(__file__,os.path.join(args.outdir,"script.py"))
    
