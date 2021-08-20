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
import six

def process_dir(dir_,proc_name="HLTX",read_nrtot_directly=False):
    files = glob.glob(os.path.join(dir_,"*.root"))
    good_files = []
    bad_files = []
    nr_tot = 0.
    nr_pass = 0.
    for file_ in files:
        root_file = ROOT.TFile.Open(file_,"READ")
        if not root_file or root_file.IsZombie() or root_file.TestBit(ROOT.TFile.kRecovered):
            bad_files.append(str(file_))
        else:
            try:
                
                nr_pass += root_file.Events.GetEntries()
                if not read_nrtot_directly:
                    root_file.Runs.GetEntry(0)
                    nr_tot += getattr(root_file.Runs,"edmMergeableCounter_hltNrInputEvents_nrEventsRun_{proc_name}".format(proc_name=proc_name)).value 
                else:
                    nr_tot = nr_pass

                good_files.append(str(file_))
            except AttributeError:
                bad_files.append(str(file_))

    return {"nr_pass" : nr_pass,"nr_tot" : nr_tot,
            "good_files" : good_files,"bad_files" : bad_files}
    
    
def clean_failed_jobs(files_failed):
    """
    function moves failed jobs in a failed subdir folder
    it deduces if the base_out_dir has a the batch job sub folder or is it
    and then makes a directory failed where it moves all the files

    this assumes all the jobs passed here life in the same directory, ie are 
    from the same batch job
    """

    jobs_failed = []
    failed_jobnrs = [int(re.search('(_)([0-9]+)_EDM.root',x).group(2)) for x in files_failed]
  

    if files_failed:

        src_dir,file_tail = os.path.split(files_failed[0])
        
        if not all(os.path.split(x)[0]==src_dir for x in files_failed):
            print("not all failed files are in the same sub dir {} skipping cleaning files".format(src_dir))
            return

        dest_dir = os.path.join(src_dir,"failed")
        if not os.path.exists(dest_dir):
            os.mkdir(dest_dir)

        if not os.path.isdir(src_dir):
            print("src dir {} does not exist or is not a directory, skipping cleaning files".format(src_dir))
            return
            
        if not os.path.isdir(dest_dir):
            print("dest dir {} does not exist or is not a directory, skipping cleaning files".format(dest_dir))
            return
        
        print("\n\ngoing to copy from {} to {}".format(src_dir,dest_dir))
        print("jobs ",failed_jobnrs)

        prompt = ""
        while prompt!="y" and prompt!="n":
            print("enter y to continue, n to skip")
            prompt = raw_input().lower()
        if prompt=="n":
            print("not cleaning files")
        else:
            print("cleaning files")
            for filename in files_failed:                
                shutil.move(filename,dest_dir)

        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='tries to open every root file in sub dir')
    parser.add_argument('dirs',nargs="+",help='dirs to look for root files')
    parser.add_argument('--clean',action='store_true',help='clean bad files')
    parser.add_argument('--out','-o',default='weights.json',help='output weights json')
    parser.add_argument('--direct','-d',action='store_true',help='read nrtot directly from tree entries')
                             
    args = parser.parse_args()
    
    job_data = {}
    
    for dir_ in args.dirs:
        job_name = dir_.rstrip("/").split("/")[-1]
        job_data[job_name] = {}
        print("processing {}".format(dir_))
        job_data[job_name]['job_stats'] = process_dir(dir_,"HLTX",args.direct)
        #job_data[job_name]['xsec'] = get_xsec(job_name)
        
        
        
    for name,data in six.iteritems(job_data):
        with open("{}.list".format(name),"w") as f:
            for filename in data['job_stats']['good_files']:
                f.write(filename+"\n")
                

    if args.clean:
        for k,v in six.iteritems(job_data):
            clean_failed_jobs(v['job_stats']['bad_files'])
    
    
