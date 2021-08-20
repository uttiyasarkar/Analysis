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
from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products,add_product

import Analysis.HLTAnalyserPy.CoreTools as CoreTools




import threading
class JobThread (threading.Thread):
    def __init__(self, input_file, out_name, job_nr, prefix, max_events):
        threading.Thread.__init__(self)
        self.input_file = input_file
        self.out_name = out_name
        self.job_nr = job_nr
        self.prefix = prefix
        self.max_events = max_events

    def run(self):

        count = 0
        while not os.path.exists("{}_{}_.json".format(self.out_name,self.job_nr)) and count <3:
            cmd = ["python","Analysis/HLTAnalyserPy/test/getPUEvtsForEachEvt.py"]
            cmd.append(self.input_file)
            cmd.extend(["-p",self.prefix,"-n",str(self.max_events)])
            cmd.extend(["-o","{}_{}.json".format(self.out_name,self.job_nr)])
            cmd.extend(["-r","{}_{}.root".format(self.out_name,self.job_nr)])

            out,err = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
            count += 1
        print(out)
        print(err)
                
                
      
      


if __name__ == "__main__":
    
    CoreTools.load_fwlitelibs()

    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_files',help='json with block info')
    parser.add_argument('out_name',help='output file')
    parser.add_argument('--prefix','-p',default='file:',help='file prefix for files')
    parser.add_argument('--maxevents','-n',default=-1,type=int,help='max events for each block, <0 is no limit')
    parser.add_argument('--nr_threads','-t',default=4,type=int,help='number of threads')
    parser.add_argument('--max_jobs','-j',default=4,type=int,help='max jobs')
    
    args = parser.parse_args()

    threads = []
    
    with open(args.in_files,'r') as f:
        filenames = [line.rstrip() for line in f.readlines()]
        
   
   

    for filenr,filename in enumerate(filenames):
        threads.append(JobThread(filename,args.out_name,filenr,args.prefix,args.maxevents))
                    
    
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
                print("thread",active,"done")
                threads_active.remove(active)

                
        while len(threads_active)<args.nr_threads and threads_to_run:
            thread_nr = threads_to_run[0]
            thread = threads[thread_nr]
            print("starting thread",thread_nr,threads_to_run)
            thread.start()            
            threads_active.append(thread_nr)
            threads_to_run.remove(thread_nr)        

        time.sleep(10)
        
          
