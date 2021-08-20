from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import ROOT

def get_from_canvas(container,classname,verbose=0):
    result = []
    for obj in container.GetListOfPrimitives():
        if verbose>0:
            print(obj.ClassName())
        if obj.ClassName()==classname:
            result.append(obj)
    if verbose>0:
        print("nr objs ",len(result))
    return result
        

def merge_graphs(graphs):
    points = []
    for graph in graphs:
        for pointnr in range(0,graph.GetN()):
            points.append([graph.GetPointX(pointnr),graph.GetPointY(pointnr)])
    graph = ROOT.TGraph(len(points))
    graph.SetTitle(graphs[0].GetTitle())
    graph.SetName(graphs[0].GetTitle())
    for pointnr,point in enumerate(points):
        graph.SetPoint(pointnr,point[0],point[1])
    return graph

def get_graphs(in_file):
    graphs = []
    for key in in_file.GetListOfKeys():
        graphs.extend(get_from_canvas(key.ReadObj(),"TGraph",1))
    return graphs
   
def convert_to_hist(graph):
    hist = ROOT.TH1D("{}_Hist".format(graph.GetName()),"",25,10,60)
    hist.Sumw2()
    hist.SetDirectory(0)
    histCounts = ROOT.TH1D("{}_Hist".format(graph.GetName()),"",25,10,60)
    histCounts.SetDirectory(0)
    for pointnr in range(0,graph.GetN()):
        hist.Fill(graph.GetPointX(pointnr),graph.GetPointY(pointnr))
        histCounts.Fill(graph.GetPointX(pointnr))
    for binnr in range(0,hist.GetNbinsX()+2):
        if histCounts.GetBinContent(binnr)!=0:
            hist.SetBinContent(binnr,hist.GetBinContent(binnr)/histCounts.GetBinContent(binnr))
            hist.SetBinError(binnr,hist.GetBinError(binnr)/histCounts.GetBinContent(binnr))  
   
    return hist

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='converts rate mon output to friendlier style')
    parser.add_argument('input',nargs="+",help='input files')
    parser.add_argument('--output',"-o",default="output.root",help='output file')
    
    args = parser.parse_args()

    graphs = []
    for in_filename in args.input:
        in_file = ROOT.TFile.Open(in_filename,'READ')
        graphs.append(merge_graphs(get_graphs(in_file)))
        

    out_file = ROOT.TFile.Open(args.output,'RECREATE')
    hists = [convert_to_hist(graph) for graph in graphs]
    map(out_file.WriteTObject, graphs)
    map(lambda h: h.SetDirectory(out_file),hists)
    out_file.Write()
    
        

    
    
