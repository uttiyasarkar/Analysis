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
import six
from collections import OrderedDict

from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products

import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
import Analysis.HLTAnalyserPy.HistTools as HistTools


def set_style_att(hist,color=None,line_width=None,marker_style=None,line_style=None,marker_size=None):
    if color!=None:
        hist.SetLineColor(color)
        hist.SetMarkerColor(color)
    if line_width!=None:
        hist.SetLineWidth(line_width)
    if line_style!=None:
        hist.SetLineWidth(line_style)
    if marker_style!=None:
        hist.SetMarkerStyle(marker_style)
    if marker_size!=None:
        hist.SetMarkerSize(marker_size)


def adjust_yaxis_dist(hist1,hist2):
    max_val = max(hist1.GetMaximum(),hist2.GetMaximum())
    hist1.GetYaxis().SetRangeUser(0.1,max_val*1.3)
    
def adjust_yaxis_eff(hist1,hist2):
    max_val = max(hist1.GetMaximum(),hist2.GetMaximum())
    min_val = min(hist1.GetMinimum(),hist2.GetMinimum())
    print(min_val,max_val)

    if min_val>0.95:
        y_min = 0.9
        y_max = 1.05
    elif min_val>0.85:
        y_min = 0.8
        y_max = 1.1
    elif min_val>0.75:
        y_min = 0.7
        y_max = 1.2
    elif min_val>0.6:
        y_min = 0.5
        y_max = 1.2
    else:
        y_min = 0
        y_max = 1.3
    hist1.GetYaxis().SetRangeUser(y_min,y_max)
    
def adjust_yaxis(hist1,hist2,is_eff=False):
    if is_eff:
        adjust_yaxis_eff(hist1,hist2)
    else:
        adjust_yaxis_dist(hist1,hist2)

def set_label_attr(label,text_size=0.657895):
    label.SetFillStyle(0)
    label.SetBorderSize(0)
    label.SetTextFont(42)
    label.SetTextAlign(12)
    label.SetTextSize(text_size)
            
def plot_with_ratio(numer,numer_label,denom,denom_label,div_opt="",hist_data={}):

    set_style_att(numer,color=2,marker_style=4)
    set_style_att(denom,color=4,marker_style=8)

    ROOT.gStyle.SetOptStat(0)
    c1 = ROOT.TCanvas("c1","c1",900,750)
    c1.cd()
    spectrum_pad = ROOT.TPad("spectrumPad","newpad",0.01,0.30,0.99,0.99)
    spectrum_pad.Draw() 
    spectrum_pad.cd()
    xaxis_title = denom.GetXaxis().GetTitle()
    denom.GetXaxis().SetTitle()
    denom.Draw("EP")
    numer.Draw("EP SAME")
    leg = ROOT.TLegend(0.115,0.766,0.415,0.888)
    leg.AddEntry(numer,numer_label,"LP")
    leg.AddEntry(denom,denom_label,"LP")
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.Draw()

    labels = []    
    for cut_nr,cut_label in enumerate(hist_data['cut_labels']):
        y_max = 0.882-0.06*cut_nr
        y_min = 0.882-0.06*(cut_nr+1)
        label = ROOT.TPaveLabel(0.681,y_min,0.894,y_max,cut_label,"brNDC")
        label.SetFillStyle(0)
        label.SetBorderSize(0)
        label.SetTextFont(42)
        label.SetTextAlign(12)
        label.SetTextSize(0.657895)
        label.Draw()
        labels.append(label)

    
    c1.cd()
    ratio_pad = ROOT.TPad("ratioPad", "newpad",0.01,0.01,0.99,0.33)
    ratio_pad.Draw()
    ratio_pad.cd()
    ratio_pad.SetGridy()
    ratio_pad.SetTopMargin(0.05)
    ratio_pad.SetBottomMargin(0.3)
    ratio_pad.SetFillStyle(0)
    ratio_hist = numer.Clone("ratioHist")
    ratio_hist.SetDirectory(0)
    ratio_hist.Sumw2()
    ratio_hist.Divide(numer,denom,1,1,div_opt)

    set_style_att(ratio_hist,color=1,marker_style=8)
#    AnaFuncs::setHistAttributes(ratio_hist,1,1,8,1)
    ratio_hist.SetTitle("")
    #  ratio_hist.GetXaxis().SetLabelSize(ratio_hist.GetXaxis().GetLabelSize()*(0.99-0.33)/0.33)
    ratio_hist.GetXaxis().SetLabelSize(0.1)
    ratio_hist.GetXaxis().SetTitleSize(0.1)
    ratio_hist.GetXaxis().SetTitle(xaxis_title)
    ratio_hist.GetYaxis().SetLabelSize(0.1)
    ratio_hist.GetYaxis().SetTitleSize(0.1)
    ratio_hist.GetYaxis().SetTitleOffset(0.3) 
    ratio_hist.GetYaxis().SetTitle("ratio")   
    ratio_hist.GetYaxis().SetRangeUser(0.5,1.5)
    ratio_hist.GetYaxis().SetNdivisions(505)
    ratio_hist.Fit("pol0")
    fit_func = ratio_hist.GetFunction("pol0")
    ratio_hist.Draw("EP")
    warning_box = None
    bad_match = False
    if fit_func:
        chi2 = fit_func.GetChisquare()
        ndof = fit_func.GetNDF()
        prob = fit_func.GetProb()
        p0 = fit_func.GetParameter(0)
        p0_err = fit_func.GetParError(0)
        chi2_str = "#chi^{{2}} / ndof = {chi2:.1f}/{ndof}".format(chi2=chi2,ndof=ndof)
        fit_str = "p0 = {p0:2.3f} #pm {p0_err:2.3f}".format(p0=p0,p0_err=p0_err)
        chi2_label = ROOT.TPaveLabel(0.640,0.705,0.901,0.903,chi2_str,"brNDC")
        fit_label = ROOT.TPaveLabel(0.640,0.322,0.901,0.520,fit_str,"brNDC")
        set_label_attr(chi2_label,0.434789)
        set_label_attr(fit_label,0.434789)
        chi2_label.Draw()
        fit_label.Draw()
        labels.extend([fit_label,chi2_label])
        if ndof!=0 and (prob<0.05 or abs((p0-1)/p0_err)>2):
            print(denom.GetName(),"is bad")
            c1.cd()
            warning_box = ROOT.TBox(c1.GetX1(),c1.GetY1(),c1.GetX2(),c1.GetY2());
            warning_box.SetFillStyle(0);
            warning_box.SetLineWidth(4);            
            warning_box.SetLineColor(ROOT.kRed);
            warning_box.Draw();
            bad_match = True

    spectrum_pad.cd()
    return c1,bad_match,spectrum_pad,ratio_pad,ratio_hist,leg,labels,fit_func,warning_box

def gen_html(canvases_to_draw,html_body=None):
    
    html_str="""
<!DOCTYPE html>
<html lang="en">
<head>
    
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
 
<title>E/gamma Validation</title>
 
<script src="https://root.cern/js/5.9.1/scripts/JSRootCore.js" type="text/javascript"></script>
 
<script type='text/javascript'> 
  var filename = "output.root";
  JSROOT.gStyle.fOptStat = 0
  JSROOT.OpenFile(filename, function(file) {{
    {canvas_draw_js}
  }});
  </script>
</head>
 
<body>

{canvas_pads}
  
</body>
 
</html>
    """

    canvas_pad_str_base = '<div id="{name}" style="width:800px; height:600px"></div>'
    canvas_draw_str_base = """  
    file.ReadObject("{name}", function(obj) {{
       JSROOT.draw("{name}", obj, "");
    }});"""
    
    canvas_draw_str = "".join([canvas_draw_str_base.format(name=c) for c in canvases_to_draw])
    
    if html_body==None:
        canvas_pad_str = "".join([canvas_pad_str_base.format(name=c) for c in canvases_to_draw])
    else:
       # canvas_pad_str = "\n".join(html_body)
        canvas_pad_str = str(html_body)
    
    
    return html_str.format(canvas_draw_js=canvas_draw_str,canvas_pads=canvas_pad_str)


def compare_hists(ref_filename,tar_filename,tar_label="target",ref_label="reference",out_dir="./"):
    
    tar_file = ROOT.TFile.Open(tar_filename)
    ref_file = ROOT.TFile.Open(ref_filename)

    out_file = ROOT.TFile.Open(os.path.join(out_dir,"output.root"),"RECREATE")
    canvases_to_draw=[]

    for key in tar_file.GetListOfKeys():
        tar_hist = tar_file.Get(key.GetName())
        ref_hist = ref_file.Get(key.GetName())
        if ref_hist:

    
            tar_hist.SetLineColor(2)
            tar_hist.SetMarkerStyle(4)
            tar_hist.SetMarkerColor(2)

            ref_hist.SetLineColor(4)
            ref_hist.SetMarkerStyle(8)
            ref_hist.SetMarkerColor(4)
            res = plot_with_ratio(tar_hist,tar_label,ref_hist,ref_label,"")
            c1 = res[0]
            c1.Update()
            canvas_name = "{}Canvas".format(key.GetName())
            c1.Write(canvas_name)
            canvases_to_draw.append(canvas_name)
            
            for suffex in [".C",".png"]:
                c1.Print(os.path.join(out_dir,"{}{}".format(key.GetName(),suffex)))
             
        else:
            print("ref hist",key.GetName(),"not found")

    html_str = gen_html(canvases_to_draw)
    with open(os.path.join(out_dir,"index.html"),'w') as f:
        f.write(html_str)

def compare_hists_indx(ref_filename,tar_filename,tar_label="target",ref_label="reference",out_dir="./"):
    
    tar_file = ROOT.TFile.Open(tar_filename)
    ref_file = ROOT.TFile.Open(ref_filename)

    tar_index = json.loads(str(tar_file.meta_data),object_pairs_hook=OrderedDict)
    ref_index = json.loads(str(ref_file.meta_data),object_pairs_hook=OrderedDict)
    
    if tar_label==None:
        tar_label = str(tar_file.label)
    if ref_label==None:
        ref_label = str(ref_file.label)

    out_file = ROOT.TFile.Open(os.path.join(out_dir,"output.root"),"RECREATE")
    canvases_to_draw=[]
    toc_str_base = '<br><a href="#{coll}{hist}"><font color={colour}>{coll} : {hist}</font></a>&nbsp;'
    toc = []
    html_body = ["<h1>Egamma Validation page</h1>Note this is an interactive webpage and will take a few moments to load<br><br>"]
    html_body.append("""
Failing comparisons are indicated in red in the table of contents. The criteria for failing is currently a pol0 fit that either has Prob(chi2,ndof)<0.05 or fits to a p0 more than 2 sigma away from 1.0<br><br>{toc}
""")
    for collname,coll in six.iteritems(tar_index):
        html_body.append("<h2>{}</h2>".format(coll['desc']))
        for histbin_name,histbin_data in six.iteritems(coll['hists']):
            html_body.append('<h3 id="{coll}{hist}">{coll} : {hist}</h3>'.format(coll=coll['desc'],hist=histbin_name))
            failing_comp = False
            hists_sorted = sorted(histbin_data,key=lambda k: k['name'])
            for hist_data in hists_sorted:
                #unicode strings fun...hence the str()
                hist_name = str(hist_data['name'])

                tar_hist = tar_file.Get(hist_name)
                ref_hist = ref_file.Get(hist_name)
                if ref_hist:
                    if coll['is_normable']:
                        try:
                            tar_weight = ref_index[collname]['norm_val']/coll['norm_val']
                        except:
                            tar_weight = 1.
                        tar_hist.Scale(tar_weight)
                    
                    adjust_yaxis(ref_hist,tar_hist,coll['is_effhist'])
                    res = plot_with_ratio(tar_hist,tar_label,ref_hist,ref_label,"",hist_data)
                    if res[1]:
                        failing_comp = True

                    c1 = res[0]
                    c1.Update()
                    canvas_name = "{}Canvas".format(hist_name)
                    c1.Write(canvas_name)
                    canvases_to_draw.append(canvas_name)
                    html_body.append('<div id="{name}" style="width:800px; height:600px; display:inline-block"></div>'.format(name=canvas_name))
                    for suffex in [".C",".png"]:
                        c1.Print(os.path.join(out_dir,"{}{}".format(hist_name,suffex)))
             
                else:
                    print("ref hist",hist_name,"not found")
            toc_colour = "red" if failing_comp else "grey"
            toc.append(toc_str_base.format(coll=coll['desc'],hist=histbin_name,colour=toc_colour))
            html_body.append("<br><br>")
    
    html_body_str = "\n".join(html_body).format(toc=''.join(toc))
    html_str = gen_html(canvases_to_draw,html_body_str)
    with open(os.path.join(out_dir,"index.html"),'w') as f:
        f.write(html_str)

            
def get_filenames(input_filenames,prefix=""):
    output_filenames = []
    for filename in input_filenames:
        if not filename.endswith(".root"):
            with open(filename) as f:
                output_filenames.extend(['{}{}'.format(prefix,l.rstrip()) for l in f])
        else:
            output_filenames.append('{}{}'.format(prefix,filename))
    return output_filenames

if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('--ref',required=True,help='reference filename')
    parser.add_argument('--tar',required=True,help='target filename')
    parser.add_argument('--out_dir','-o',default="./",help='output dir')
    parser.add_argument('--tar_label',default=None,help="target label for leg")
    parser.add_argument('--ref_label',default=None,help="reference label for leg")
    args = parser.parse_args()

    ROOT.gROOT.SetBatch()

    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)


    compare_hists_indx(tar_filename=args.tar,ref_filename=args.ref,
                       tar_label=args.tar_label,ref_label=args.ref_label,
                       out_dir=args.out_dir)
