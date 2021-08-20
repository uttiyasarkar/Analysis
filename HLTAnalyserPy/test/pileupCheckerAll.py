from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import ROOT
import json
import thread
import os
import random
import time
import shutil
import subprocess
import six
from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products,add_product

import Analysis.HLTAnalyserPy.CoreTools as CoreTools




import threading
class JobThread (threading.Thread):
    def __init__(self, block, dataset_name, nr_evts_dataset, site_name, prefix, max_events):
        threading.Thread.__init__(self)
        self.block = dict(block)
        self.output = {}
        self.output['dataset'] = dataset_name
        self.output['site'] = site_name
        self.output['block'] = block['name']
        self.output['nrevts_bloc'] = block['nrevents']
        self.output['nrevts_dataset'] = nr_evts_dataset
        self.output['results'] = None            
        self.prefix = prefix
        self.max_events = max_events

    def run(self):
        count = 0

        while self.output['results'] == None and count <3:
            try:
                cmd = ["python","Analysis/HLTAnalyserPy/test/pileupChecker.py"]
                cmd.extend(self.block['files'])
                cmd.extend(["-p",self.prefix,"-n",str(self.max_events),"--json"])

                out,err = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
                self.output['results'] = json.loads(out)
#                self.output['results'] = check_pileup(self.block['files'],self.prefix,self.max_events)
            except ValueError:
                count += 1
#                print("trying again",count)

if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_file',help='json with block info')
    parser.add_argument('out_file',help='output file')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix for files')
    parser.add_argument('--maxevents','-n',default=-1,type=int,help='max events for each block, <0 is no limit')
    parser.add_argument('--nr_threads','-t',default=4,type=int,help='number of threads')
    parser.add_argument('--max_jobs','-j',default=4,type=int,help='max jobs')
    
    args = parser.parse_args()
    sites_to_skip = []
    sites_to_skip = ['T1_DE_KIT_Disk','T2_US_Florida']

    with open(args.in_file,"r") as f:
        site_data = json.load(f)
        
    if os.path.exists(args.out_file):
        with open(args.out_file,"r") as f:
            block_results = json.load(f)
    else:
        block_results = {}

    blocks_being_checked = []
    threads = []
    for site_name, site_datasets in six.iteritems(site_data):
        if site_name in sites_to_skip:
            continue
        for dataset_name, dataset_info in six.iteritems(site_datasets):
            for block_info in dataset_info['blocks']:
                if block_info['name'] not in block_results:
                    threads.append(JobThread(block_info,dataset_name,dataset_info['nrevents'],site_name,args.prefix,args.maxevents))
                    
    
    threads_active = []
    threads_to_run = range(0,len(threads))
    random.shuffle(threads_to_run)
    print(threads_to_run)
    if args.max_jobs>0:
        threads_to_run = threads_to_run[:args.max_jobs]
        
    print("running over ",len(threads_to_run))

    while len(threads_to_run)!=0 or len(threads_active)!=0:
        
        for active in threads_active:
            if not threads[active].isAlive():
                thread = threads[active]
                if thread.output['results']:
                    block_results[thread.block['name']] = thread.output
                    print("thread",active,"succeeded")
                    if os.path.exists(args.out_file):
                        shutil.copyfile(args.out_file,args.out_file+"_backup")
                    with open(args.out_file,'w') as f:
                        json.dump(block_results,f)
                else:
                    print("thread",active,"failed")
                    
                threads_active.remove(active)

                
        while len(threads_active)<args.nr_threads and threads_to_run:
            thread_nr = threads_to_run[0]
            thread = threads[thread_nr]
            print("starting thread",thread_nr,threads_to_run)
            thread.start()            
            threads_active.append(thread_nr)
            threads_to_run.remove(thread_nr)        

        time.sleep(10)
        
          
