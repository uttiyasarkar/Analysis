#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import json
import random
import re
import subprocess

def process_log(log_txt):
    data = {}

    for line in log_txt.split("\n"):
        if line.startswith("Before Filter: total cross section"):
            data['xsec'] = float(line.split()[6])
            data['xsec_err'] = float(line.split()[8])
        if line.startswith("Filter efficiency (event-level)"):
            data['filt_eff'] = float(line.split()[7])
            data['filt_eff_err']  = float(line.split()[9])
        if line.startswith("After filter: final cross section"):
            data['xsec_final'] = float(line.split()[6])
            data['xsec_final_err'] = float(line.split()[8])
    return data

def process_dataset(dataset,xsec_data):
    
    files_txt = subprocess.Popen(['dasgoclient','--query','file dataset={}'.format(dataset),'--limit','-1'],stdout=subprocess.PIPE).communicate()[0]
    files = files_txt.split("\n")
    file_name  = ",".join(files[4:8])
    cmssw_cfg = "genXSec.py"
    cmssw_cmd = ["cmsRun",cmssw_cfg,"inputFiles={}".format(file_name)]
    
    cmssw_log = subprocess.Popen(cmssw_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()[1]
  
    
    dataset_name = dataset.split("/")[1]
    xsec_data[dataset_name] = process_log(cmssw_log)
    print(xsec_data)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='runs over specificed datasets to get their xsec')
    parser.add_argument('--query','-q',required=True,help='das query')
    parser.add_argument('--out_file','-o',default="output.json",help='output file for json')    
    args = parser.parse_args()

    query_results_txt = subprocess.Popen(['dasgoclient','--query',args.query,'--format','json'],stdout=subprocess.PIPE).communicate()[0]
    query_results = json.loads(query_results_txt)
    print("nr datasets: {nresults}".format(**query_results))
    datasets = []
    for result in query_results['data']:
        dataset = result['dataset'][0]['name']
        datasets.append(dataset)
        print("  {}".format(dataset))

    xsec_data = {}

    for dataset in datasets:
        process_dataset(dataset,xsec_data)
        with open(args.out_file,'w') as f:
            json.dump(xsec_data,f)

    keys_sorted = xsec_data.keys()
    sorted(keys_sorted,key=lambda x:int(re.search(r'(\d+)',x).groups()[0]))
    
    for key in keys_sorted:
        try:
            print("'{}' : {}".format(key,xsec_data[key]['xsec_final']))
        except KeyError:
            pass

   
