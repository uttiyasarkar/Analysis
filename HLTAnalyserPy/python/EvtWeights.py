from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import numpy
from enum import Enum
from Analysis.HLTAnalyserPy.EvtData import EvtData
from Analysis.HLTAnalyserPy.GenTools import MCSampleGetter,MCSample
import Analysis.HLTAnalyserPy.TrigTools as TrigTools

class PtBinnedSample:

    def __init__(self,min_pt,max_pt,xsec,nr_inclusive,nr_em,em_filt_eff,nr_mu,mu_filt_eff,em_mu_filt_eff,mu_em_filt_eff):
        self.min_pt = min_pt
        self.max_pt = max_pt
        self.xsec = xsec
        self.nr_inclusive = nr_inclusive
        self.nr_em = nr_em
        self.em_filt_eff = em_filt_eff
        self.em_mu_filt_eff = em_mu_filt_eff
        self.nr_mu = nr_mu
        self.mu_filt_eff = mu_filt_eff
        self.mu_em_filt_eff = mu_em_filt_eff
        
        self.nr_emnomu_expect = 0.
        self.nr_emnomu_actual = 0.
        self.nr_munoem_expect = 0.
        self.nr_munoem_actual = 0.
        self.nr_emmu_expect = 0.
        self.nr_emmu_actual = 0.
        
        print("{}-{} {} {}".format(min_pt,max_pt,xsec,nr_inclusive)) 

    def _get_incl_expect(self,nr_mb_tot,mb_xsec,filt_eff):
        """
        gets the number of events (inclusive + mb) expected
        for a given filter efficiency
        """
        nr_mb = nr_mb_tot*filt_eff*self.xsec/mb_xsec
        nr_incl = self.nr_inclusive*filt_eff
        return nr_mb+nr_incl

    def set_enriched_counts(self,nr_minbias,minbias_xsec):
        
        self.nr_emnomu_expect = self._get_incl_expect(nr_minbias,minbias_xsec,
                                                      self.em_filt_eff*(1-self.em_mu_filt_eff))
        self.nr_munoem_expect = self._get_incl_expect(nr_minbias,minbias_xsec,
                                                      self.mu_filt_eff*(1-self.mu_em_filt_eff))
        self.nr_emmu_expect = self._get_incl_expect(nr_minbias,minbias_xsec,
                                                    self.em_filt_eff*self.em_mu_filt_eff)
        
        self.nr_emnomu_actual = (self.nr_emnomu_expect + 
                                 self.nr_em*(1-self.em_mu_filt_eff))
         
        self.nr_munoem_actual = (self.nr_munoem_expect + 
                                 self.nr_mu*(1-self.mu_em_filt_eff))
        self.nr_emmu_actual = (self.nr_emmu_expect + 
                               self.nr_em*self.em_mu_filt_eff + 
                               self.nr_mu*self.mu_em_filt_eff)

class QCDWeightCalc:
    """ 
    translation of Christian Veelken's mcStiching
    https://github.com/veelken/mcStitching
    """
    def __init__(self,ptbinned_samples,bx_freq=30000000.0):
        self.bx_freq = bx_freq
        self.bins = [PtBinnedSample(**x) for x in ptbinned_samples]
        self.bins.sort(key=lambda x: x.min_pt)
        self.bin_lowedges = [x.min_pt for x in self.bins]
        self.bin_lowedges.append(self.bins[-1].max_pt)
        self.gen_filters = TrigTools.TrigResults(["Gen_QCDMuGenFilter",
                                                  "Gen_QCDBCToEFilter",
                                                  "Gen_QCDEmEnrichingFilter",
                                                  "Gen_QCDEmEnrichingNoBCToEFilter"])
        #now we get the number of EM events (skip bin 0 which is  minbias)
        min_bias = self.bins[0]
        for bin_ in self.bins[1:]:
            bin_.set_enriched_counts(min_bias.nr_inclusive,min_bias.xsec)

    def weight(self,evtdata,disable_enriched=False):
        pusum_intime = [x for x in evtdata.get("pu_sum") if x.getBunchCrossing()==0]
        bin_counts = [0]*(len(self.bins)+1)
        tot_count= pusum_intime[0].getPU_pT_hats().size()
        for pu_pt_hat in pusum_intime[0].getPU_pT_hats():
            bin_nr = numpy.searchsorted(self.bin_lowedges,pu_pt_hat,'right')
            #overflow means we fill bin 1 which is the inclusive min bias bin
            try:
                bin_counts[bin_nr]+=1
            except IndexError:
                bin_counts[1]+=1
       
        geninfo = evtdata.get("geninfo")
        tot_count +=1
        #again like for PU, overflow means we fill bin 1 which is the inclusive min bias bin
        try:            
            bin_counts[numpy.searchsorted(self.bin_lowedges,geninfo.qScale(),'right')]+=1
        except IndexError:
            bin_counts[1]+=1
        
        min_bias_xsec = self.bins[0].xsec

        expect_events_mc = 0
        for bin_nr,sample_bin in enumerate(self.bins):
            bin_frac = float(bin_counts[bin_nr+1])/float(tot_count)
            theory_frac =  float(sample_bin.xsec) / float(min_bias_xsec)
            #dont correct inclusively generated sample
            prob_corr = bin_frac / theory_frac if bin_nr!=0 else 1.
            expect_events_mc += sample_bin.nr_inclusive * prob_corr
            
        weight = float(self.bx_freq) / float(expect_events_mc)
        if not disable_enriched:
            weight *= self.enriched_weight(evtdata)
        return weight

    def enriched_weight(self,evtdata):
        self.gen_filters.fill(evtdata)
        pass_em = self.gen_filters.result("Gen_QCDEmEnrichingNoBCToEFilter")
        pass_mu = self.gen_filters.result("Gen_QCDMuGenFilter")
        if  pass_em or pass_mu:
            geninfo = evtdata.get("geninfo")
            #should never be -1 as we should never hit the underflow 
            #and if so there is a problem
            sample_nr = numpy.searchsorted(self.bin_lowedges,geninfo.qScale(),'right')-1
            sample_nr = sample_nr if sample_nr < len(self.bins) else 0
            bin_ = self.bins[sample_nr]    
            div_with_check = lambda a,b :  a/b if b!=0 else 1.
            if pass_em and pass_mu:
                return div_with_check(bin_.nr_emmu_expect,bin_.nr_emmu_actual)
            elif pass_em and not pass_mu:
                return div_with_check(bin_.nr_emnomu_expect,bin_.nr_emnomu_actual)
            elif not pass_em and pass_mu:
                return div_with_check(bin_.nr_munoem_expect,bin_.nr_munoem_actual)
        else:
            return 1.

class EvtWeights:
    
    class WeightType(Enum):
        V2 = 2
        V2NoEnrich = 3

    def __init__(self,input_filename=None,input_dict=None,bx_freq=30.0E6,nr_expt_pu=200,mb_xsec = 80.0E9):
        if input_filename: 
            with open(input_filename,'r') as f:
                self.data = json.load(f)
        elif input_dict:
            self.data = dict(input_dict)
        else:            
            self.data = {}
            
        self.mcsample_getter = MCSampleGetter()
        self.lumi = bx_freq * nr_expt_pu / mb_xsec
        self.bx_freq = bx_freq
        self.mb_xsec = mb_xsec
        if self.data:
            self.qcd_weights = QCDWeightCalc(self.data['v2']['qcd'],bx_freq)
            
    
    def weight(self,evtdata,weight_type=WeightType.V2,nr_expt_pu=None,get_pu_from_evt=True):     
        mcsample = self.mcsample_getter.get(evtdata)        
        if mcsample.proc_type == MCSample.ProcType.QCD or mcsample.proc_type == MCSample.ProcType.MB:
            disable_enriched = weight_type==EvtWeights.WeightType.V2NoEnrich
            return self.qcd_weights.weight(evtdata,disable_enriched=disable_enriched)
        else:         
            key = ""
            if mcsample.proc_type == MCSample.ProcType.DY: key = "dy"
            if mcsample.proc_type == MCSample.ProcType.WJets: key = "wjets"
            try:
                if nr_expt_pu==None and get_pu_from_evt:
                    pusum_intime = [x for x in evtdata.get("pu_sum") if x.getBunchCrossing()==0]
                    nr_expt_pu = pusum_intime[0].getTrueNumInteractions()
                    
                lumi  = self.lumi if nr_expt_pu==None else (self.bx_freq*nr_expt_pu+1)/self.mb_xsec
                return self.data['v2'][key][0]['xsec']/self.data['v2'][key][0]['nrtot']*lumi
            except KeyError:
                return 1.
    
 
    def filtweight(self,evtdata): 
        mcsample = self.mcsample_getter.get(evtdata)  
        if mcsample.proc_type == MCSample.ProcType.QCD or mcsample.proc_type == MCSample.ProcType.MB:
            return self.qcd_weights.enriched_weight(evtdata)
        else:
            return 1.
