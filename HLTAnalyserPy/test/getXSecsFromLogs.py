#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import glob
import re 
import json

def process_log(filename):
    data = {}
    with open(filename,'r') as f:
        for line in f.readlines():
            if line.startswith("Before Filter: total cross section"):
                data['xsec'] = float(line.split()[6])
                data['xsec_err'] = float(line.split()[8])
            if line.startswith("Filter efficiency (event-level)"):
                data['filt_eff'] = float(line.split()[7])
                data['filt_eff_err'] = float(line.split()[9])
            if line.startswith("After filter: final cross section"):
                data['xsec_final'] = float(line.split()[6])
                data['xsec_final_err'] = float(line.split()[8])
    return data

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='gets the cross-sections from gen tools')
    parser.add_argument('xsec_logs',nargs="+",help='xsec logs ')
    parser.add_argument('--out_file','-o',default="output.json",help='output file for json')    
    args = parser.parse_args()

    xsec_data = {}

    for log in args.xsec_logs:
        #format is xsec_<name>.log, we want <name>
        dataset_name = log.split("/")[-1][5:-4]
        xsec_data[dataset_name]  = process_log(log)

    keys_sorted = xsec_data.keys()
    sorted(keys_sorted,key=lambda x:int(re.search(r'(\d+)',x).groups()[0]))
    
    for key in keys_sorted:
        try:
            print("'{}' : {}".format(key,xsec_data[key]['xsec_final']))
        except KeyError:
            pass

    with open(args.out_file,'w') as f:
        json.dump(xsec_data,f)
