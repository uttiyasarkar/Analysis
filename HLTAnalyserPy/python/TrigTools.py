from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ROOT
import json
import math
import re

def get_trig_indx(selected_name,trig_names):
    """
    returns the index of the trigger (if it exists, otherwise returns the size of trig_names, yes this is a bit c++ like)
    the annoying thing here is we want to match all HLT_Blah_v*
    there are several ways to do it, the quickest is see which starts with HLT_Blah_v
    
    note one can be smarter and cache the result and update when trig_names.parameterSetID() changes 
    """
    for idx,name in enumerate(trig_names.triggerNames()):
        if str(name).startswith(selected_name):
            return idx
    return None

def match_trig_objs(eta,phi,trig_objs,max_dr=0.1):    
    max_dr2 = max_dr*max_dr
    matched_objs = [obj for obj in trig_objs if ROOT.reco.deltaR2(eta,phi,obj.eta(),obj.phi()) < max_dr2]
    return matched_objs

def sep_trig_ver(name):
    match = re.search(r'([\w]+_v)([0-9]+)',name)
    if match:
        return match.group(1),match.group(2)
    else:
        return str(name),None

def get_objs_passing_filter_aod(evtdata,filter_name,trig_sum_name="trig_sum"):
    trig_sum = evtdata.get(trig_sum_name)
    filt_input_tag = ROOT.edm.InputTag(filter_name)
    #no process specified so we guess from the first entry of trig sum
    #they should all have the same process (cant think of a scenario when not)
    if filt_input_tag.process() == "" and trig_sum.sizeFilters():
        hlt_process = trig_sum.filterTag(0).process()
        filt_input_tag = ROOT.edm.InputTag(filter_name,"",hlt_process)
    
    filt_indx = trig_sum.filterIndex(filt_input_tag)
    passing_objs = []
    if filt_indx < trig_sum.sizeFilters():
        keys = trig_sum.filterKeys(filt_indx)
        trig_objs = trig_sum.getObjects()
        passing_objs = [trig_objs[key] for key in keys]
    return passing_objs
        
                                      
class TrigResults:
    """
    class acts as a name cache to allow the trigger results to be accessed
    by trigger name

    it takes as input the list of specific triggers to look for rather than 
    reading all possible triggers
    """
    def __init__(self,trigs,trig_res_name="trig_res"):
        self.trig_res_name = trig_res_name
        self.trig_psetid = None
        self.trig_indices = {x : [] for x in trigs}
        self.trig_res = {x : False for x in trigs}

    def _set_trig_indices(self,trig_names):
        for name in self.trig_indices:
            self.trig_indices[name] = []

        for idx,trig_name in enumerate(trig_names.triggerNames()):
            trig_name_str = str(trig_name)
            for name in self.trig_indices:                
                if trig_name_str.startswith(name):
                    self.trig_indices[name].append(idx)

    def _fill_trig_res(self,trig_res):
        for trig in self.trig_res:            
            self.trig_res[trig] = False # resetting it
            for idx in self.trig_indices[trig]:
                if trig_res[idx].accept():
                    self.trig_res[trig] = True
                    break
        
    def fill(self,evtdata):
        trig_res = evtdata.get(self.trig_res_name)
        trig_names = evtdata.event.object().triggerNames(trig_res)
        if self.trig_psetid != trig_names.parameterSetID():
            self.trig_psetid = trig_names.parameterSetID()
            self._set_trig_indices(trig_names)
        self._fill_trig_res(trig_res)
       
    def result(self,trig):
        if trig in self.trig_res:
            return self.trig_res[trig]
        else:
            return False

class MenuPathRates:
    """
    small class to sum over the rates for a HLT menu for each path
    it assumes only a single menu is present, ie all events passed to 
    it have the same trigger menu
    """
    class TrigData:
        def __init__(self,indx,name):
            self.indx = indx
            self.name = str(name)
            self.counts = 0
            self.weights = 0.
            self.weights_sq = 0.
        
    def __init__(self,trig_res_name="trig_res"):
        self.trigs = []
        self.trig_res_name = "trig_res_hlt"
    def set_trigs(self,evtdata):
        trig_res = evtdata.get(self.trig_res_name)
        trig_names = evtdata.event.object().triggerNames(trig_res)
        for indx,name in enumerate(trig_names.triggerNames()):
            self.trigs.append(MenuPathRates.TrigData(indx,name))
            
    def fill(self,evtdata,weight):
        weight_sq = weight*weight
        if not self.trigs:
            self.set_trigs(evtdata)
        trig_res = evtdata.get(self.trig_res_name)
        for trig in self.trigs:
            if trig_res[trig.indx].accept():
                trig.counts += 1
                trig.weights += weight
                trig.weights_sq += weight_sq
            
    def get_results(self):
        results = {}
        for trig in self.trigs:
            results[trig.name] = {"rate" : trig.weights,
                             "rate_err" : math.sqrt(trig.weights_sq),
                             "raw_counts" : trig.counts}
        return results

