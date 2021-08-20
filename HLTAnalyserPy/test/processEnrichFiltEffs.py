from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import ROOT
import glob
import os
import argparse
import shutil
import json
import re

def get_pthat_range(name):
    if name.startswith("QCD_"):
        match = re.search(r'Pt[_-]([0-9]+)[to]+([a-zA-Z0-9]+)',name)
        sample_min_pt_hat = float(match.group(1) )
        sample_max_pt_hat = 9999. if match.group(2)=="Inf" else float(match.group(2))
    else:
        #min bias
        sample_min_pt_hat = 0.
        sample_max_pt_hat = 9999.
    return sample_min_pt_hat,sample_max_pt_hat

def process_line(line,out_dict):
    name = line.split()[0]
    em_eff = float(line.split()[5])
    mu_eff = float(line.split()[8])
    emmu_eff = float(line.split()[11])
    
    pt_hat_min,pt_hat_max = get_pthat_range(name)
    pt_hat = "{:.0f}to{:.0f}".format(pt_hat_min,pt_hat_max)
    if pt_hat not in out_dict:
        out_dict[pt_hat] = {}
    
    is_em = name.find("EMEnriched")!=-1
    is_mu = name.find("MuEnriched")!=-1
    
    if is_em:
        out_dict[pt_hat]["em_mu_filt_eff"] = emmu_eff
    elif is_mu:
        out_dict[pt_hat]["mu_em_filt_eff"] = emmu_eff
    else:
        out_dict[pt_hat]["em_filt_eff"] = em_eff
        out_dict[pt_hat]["mu_filt_eff"] = mu_eff


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='tries to open every root file in sub dir')
    parser.add_argument('input_file',help='input file')
    args = parser.parse_args()
    
    out_dict = {}
    with open(args.input_file) as f:
        for line in f.readlines():
            process_line(line,out_dict)
    
    print(json.dumps(out_dict))
