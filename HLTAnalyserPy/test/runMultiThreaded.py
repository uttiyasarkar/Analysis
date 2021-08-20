from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import ROOT
import thread
import os
import time
import subprocess
import threading
import numpy as np

import Analysis.HLTAnalyserPy.CoreTools as CoreTools

class JobThread (threading.Thread):
    def __init__(self, cmd, input_files, out_name):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.input_files = input_files
        self.out_name = out_name
        
    def run(self):

        count = 0

        cmd = self.cmd.split()
        cmd.extend(self.input_files)
        cmd.extend(["-o",self.out_name])
        #easier just to have it all just print whenever it wants
        #might update to properly manage this but in a rush
        subprocess.Popen(cmd).communicate()
        
        
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='runs a command which takes input as first argument and output as -o in multiple threads, splitting the input files')
    parser.add_argument('in_files',nargs="+",help='input file names')
    parser.add_argument('--out_name','-o',default="output.root",help='output file')
    parser.add_argument('--nr_threads','-t',default=8,type=int,help='number of threads')
    parser.add_argument('--nr_jobs','-j',default=8,type=int,help='number of jobs to split into')
    parser.add_argument('--hadd','-a',action='store_true',help="runs hadd at the end")
    parser.add_argument('--cmd','-c',required=True,help="cmd to run")
    args = parser.parse_args()
    
    threads = []
        
    in_files = CoreTools.get_filenames(args.in_files)
    in_files_per_job = np.array_split(in_files,args.nr_jobs)

    if args.out_name.find(".root")!=-1:
        out_name_base = args.out_name.replace(".root","_{}.root")
    else:
        out_name_base = args.out_name+"_{}"

    job_outfiles = []
    for jobnr,job_infile in enumerate(in_files_per_job):
        job_outfile = out_name_base.format(jobnr)
        threads.append(JobThread(args.cmd,job_infile,job_outfile))
        job_outfiles.append(job_outfile)

    print("job will delete:")
    for job_outfile in job_outfiles:
        print("   ",job_outfile)
    print("in 10 seconds, ctrl-c to abort")
    time.sleep(10)
    for job_outfile in job_outfiles:
        if os.path.exists(job_outfile):
            os.remove(job_outfile)


    threads_active = []
    threads_to_run = range(0,len(threads))
        
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
            print(thread.cmd)
            thread.start()            
            threads_active.append(thread_nr)
            threads_to_run.remove(thread_nr)        

        time.sleep(10)
        
    print("all jobs completed")
    if args.hadd:
        print("hadding")
        if os.path.exists(args.out_name):
            os.remove(args.out_name)
        hadd_cmd = ["hadd"]
        hadd_cmd.append(args.out_name)
        hadd_cmd.extend(job_outfiles)
        subprocess.Popen(hadd_cmd).communicate()
        #safer not to clean up the temporary files incase of hadd problem
        #but will do it here for convence reasons
        for job_outfile in job_outfiles:
            if os.path.exists(job_outfile):
                os.remove(job_outfile)
        print("hadd finished")
          
