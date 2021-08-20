from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import re
import ROOT
import os
import itertools

class TimingFileFormatError(Exception):
    pass


def get_timing_dir(in_file):
    dqmdir = in_file.GetDirectory("DQMData")
    dqmdir_keys = [key for key in dqmdir.GetListOfKeys() if key.IsFolder()]
    if len(dqmdir_keys)!=1:
        raise TimingFileFormatError
    
    return dqmdir.GetDirectory("{}/HLT/Run summary/TimerService".format(dqmdir_keys[0].GetName()))
        
def get_mods_dir(timing_dir):
    keys = [key for key in timing_dir.GetListOfKeys() if key.IsFolder() and re.match(r'process [\w]* modules',key.GetName())]
    if len(keys)!=1:
        raise TimingFileFormatError
    
    return timing_dir.GetDirectory(keys[0].GetName())

def get_paths_dir(timing_dir):
    keys = [key for key in timing_dir.GetListOfKeys() if key.IsFolder() and re.match(r'process [\w]* paths',key.GetName())]
    if len(keys)!=1:
        raise TimingFileFormatError
    
    return timing_dir.GetDirectory(keys[0].GetName())


    
class TimingHists:
    def __init__(self,in_file):
        self.in_file = in_file
        self.timing_dir = get_timing_dir(self.in_file)
        self.mods_dir = get_mods_dir(self.timing_dir)
        self.paths_dir = get_paths_dir(self.timing_dir)

    def hist(self,hist_name):
        """ 
        returns the requested histogram
        """
        return self.timing_dir.Get(hist_name)
    

    def path_hists(self,hist_name):
        """
        returns a generator of the histogram "hist_name" for all paths defined
        return path_name,hist
        """
        
        for key in self.paths_dir.GetListOfKeys():
            if key.GetName().startswith("path "):
                hist = self.paths_dir.Get("{}/{}".format(key.GetName(),hist_name))
                yield key.GetName()[5:],hist

    def mod_hists(self,hist_name):
        """
        returns a generator of the histogram "hist_name" for all modules defined
        return mod_name,hist
        note: this is more a placeholder, hasnt been tested yet
        """
        for key in self.mods_dir.GetListOfKeys():
            hist = self.mods_dir.Get("{}/{}".format(key.GetName(),hist_name))
            yield key.GetName(),hist
                
    
def add_plot(canvas,canvas_name,html_body,canvases_to_draw):
    c1.Write(canvas_name)
    html_body.append('<div id="{name}" style="width:800px; height:600px; display:inline-block"></div>'.format(name=canvas_name))
    canvases_to_draw.append(canvas_name)


def gen_html(canvases_to_draw,html_body=None):
    
    html_str="""
<!DOCTYPE html>
<html lang="en">
<head>
    
<meta charset="UTF-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
 
<title>TSG Timing Results</title>
 
<script src="https://root.cern/js/5.9.1/scripts/JSRootCore.js" type="text/javascript"></script>
 
<script type='text/javascript'> 
  var filename = "output.root";
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
        canvas_pad_str = str(html_body)
    
    
    return html_str.format(canvas_draw_js=canvas_draw_str,canvas_pads=canvas_pad_str)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_name',help='input filenames')
    parser.add_argument('--out_dir','-o',required=True,help='output filename')
    args = parser.parse_args()

    
    in_file = ROOT.TFile.Open(args.in_name,"READ")
    timing_hists = TimingHists(in_file)

    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)
    
    out_file = ROOT.TFile.Open(os.path.join(args.out_dir,"output.root"),"RECREATE")

    
    hists_path_time = timing_hists.path_hists("path time_real")
    hists_path_modules = timing_hists.path_hists("module_time_real_average")
    hist_sum = timing_hists.hist("event time_real")
    
    
    html_body = ["<h1>Timing Results page</h1>Note this is an interactive webpage and will take a few moments to load<br><br>"]
    toc_str_base = '<br><a href="#{path}"><font>{path}</font></a>&nbsp;'
    toc = []

    canvases_to_draw = []
    c1 = ROOT.gROOT.FindObject("c1")
    if not c1:
        c1 = ROOT.TCanvas("c1","c1",800,600)
        c1.SetLogy()
        c1.cd()

    html_body.append("<h2>Summary</h2>")
    hist_sum.Draw()
    add_plot(c1,"eventTimeRealCanvas",html_body,canvases_to_draw)
    html_body.append("<br><br>{toc}")
    for path_time,mod_time in itertools.izip(hists_path_time,hists_path_modules):
        html_body.append("<h2 id={path}>{path}</h2>".format(path=path_time[0]))
        toc.append(toc_str_base.format(path=path_time[0]))
        path_time[1].Draw()
        canvas_name = "{}{}Canvas".format(path_time[0],str(path_time[1].GetName()))
        #sooo there are characters that jsroot doesnt like, here we remove them
        #it doesnt tell you it doesnt like them, it just mysteriously fails...
        canvas_name = canvas_name.replace("_","")
        canvas_name = canvas_name.replace(" ","")

        add_plot(c1,canvas_name,html_body,canvases_to_draw)

        mod_time[1].Draw()
        #path_time[0] and mod_time[0] should be the same
        canvas_name = "{}{}Canvas".format(path_time[0],str(mod_time[1].GetName()))
        canvas_name = canvas_name.replace("_","")
        canvas_name = canvas_name.replace(" ","")

        add_plot(c1,canvas_name,html_body,canvases_to_draw)
        

    html_body.append("<br><br>")
    
    html_body_str = "\n".join(html_body).format(toc=''.join(toc))
    html_str = gen_html(canvases_to_draw,html_body_str)
    with open(os.path.join(args.out_dir,"index.html"),'w') as f:
        f.write(html_str)

    out_file.Write()
    
