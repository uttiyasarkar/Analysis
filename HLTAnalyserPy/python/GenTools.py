from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ROOT
from enum import Enum
from enum import IntEnum
import json
import re

class PartStatus(Enum):
    INITIAL = 1
    PREFSR = 2
    FINAL = 3 

def genpart_to_str(genpart,index=None):
    """converts a genparticle to a string, optionally taking an index to put in front"""
    mo1,mo2 = -1,-1
    nrMos = genpart.numberOfMothers()
    if nrMos >0:
        mo1 = genpart.motherRef(0).index()
        mo2 = genpart.motherRef(nrMos-1).index()
    da1,da2 = -1,-1
    nrDas = genpart.numberOfDaughters()
    if nrDas >0:
        da1 = genpart.daughterRef(0).index()
        da2 = genpart.daughterRef(nrDas-1).index()
    
    genpart_dict = {'mo1' : mo1 , 'mo2': mo2, 'da1' : da1 , 'da2' : da2}
    prefix=""
    if index!=None: prefix = "{:5d} ".format(index)

    for prop in ['pdgId','status','pt','eta','phi','mass','vx','vy','vz']:
        genpart_dict[prop] = getattr(genpart,prop)()
        
    return "{prefix}{pdgId:5d} {status:5d} {mo1:5d} {mo2:5d} {da1:5d} {da2:5d} {pt:7.2f} {eta: 8.1f} {phi: 4.2f} {mass: 7.1f} {vx: 3.2f} {vy: 3.2f} {vz: 4.2f}".format(prefix=prefix,**genpart_dict)

def genparts_to_str(genparts,max_to_print=20):
    index_max = min(genparts.size(),max_to_print)
    if max_to_print<0: index_max = genparts.size()
    ret_str = 'printing {} out of {} particles\n{{parts}}'.format(index_max,genparts.size())
    part_strs = ['index   pid  status  mo1  mo2   da1   da2      pt      eta   phi    mass    vx    vy    vz']

    for index in range(0,index_max):
        part_strs.append(genpart_to_str(genparts[index],index))
    return ret_str.format(parts='\n'.join(part_strs))
                  

def get_lastcopy_prefsr(part):
    daughters = part.daughterRefVector()
    if daughters.size()==1 and daughters[0].pdgId()==part.pdgId():
        return get_lastcopy_prefsr(daughters[0].get())
    else:
        return part
    
def get_lastcopy(part):
    for daughter in part.daughterRefVector():
        if daughter.pdgId() == part.pdgId():
            return get_lastcopy(daughter.get())
    return part

def get_genparts(genparts,pid=11,antipart=True,status=PartStatus.PREFSR):
    """
    returns a list of the gen particles matching the given criteria from hard process
    might not work for all generators as depends on isHardProcess()
    """

    selected = []
    if genparts==None:
        return selected

    for part in genparts:
        pdg_id = part.pdgId()
        if pdg_id == pid or (antipart and abs(pdg_id) == abs(pid)):
            if part.isHardProcess():
                if status == PartStatus.INITIAL:
                    selected.append(part)
                elif status == PartStatus.PREFSR:
                    selected.append(get_lastcopy_prefsr(part))
                elif status == PartStatus.FINAL:
                    selected.append(get_lastcopy(part))
                else:
                    raise RuntimeError("error status {} not implimented".format(status))
            else:
                #now we do the case where its particle gun and thus there is no hard process
                #however in this case it will have no mothers so we can detect it that way
                if part.numberOfMothers()==0:
                    selected.append(part)
    return selected

def match_to_gen(eta,phi,genparts,pid=11,antipart=True,max_dr=0.1,status=PartStatus.PREFSR):
    """
    Matches an eta,phi to gen level particle from the hard process
    might not work for all generaters as depends on isHardProcess()
    """

    best_match = None
    best_dr2 = max_dr*max_dr
    selected_parts = get_genparts(genparts,pid,antipart,status)
    for part in selected_parts:
        dr2 = ROOT.reco.deltaR2(eta,phi,part.eta(),part.phi())
        if dr2 < best_dr2:
            best_match = part
            best_dr2 = dr2
    return best_match,best_dr2


class MCSample:
    class ProcType(IntEnum):
        Unknown=0
        MB = 1
        QCD = 2
        DY = 3
        WJets = 4
    class FiltType(IntEnum):
        Incl=0
        Em = 1
        Mu = 2

    def __init__(self,proc_type=ProcType.Unknown,
                 filt_type=FiltType.Incl,
                 min_pthat=0,max_pthat=9999,
                 com_energy=0):
        self.proc_type = proc_type
        self.filt_type = filt_type
        self.min_pthat = min_pthat
        self.max_pthat = max_pthat
        self.com_energy = com_energy
        
    def __str__(self):
        return "ProcType {s.proc_type} FiltType {s.filt_type}  min pthat {s.min_pthat} max pthat {s.max_pthat}".format(s=self)

        
class MCSampleGetter:
    def __init__(self):
        self.last_type = MCSample()
        self.last_file = None
        self.getval_re = re.compile(r'[= ]([0-9.]+)')


    def get(self,evtdata=None):
        """
        this is keyed to the TSG samples which are all pythia except WJets
        it also assumes a given file will only contain a given process
        """
        if not evtdata:
#            print("warning no event data, assigning to {}".format(self.last_type))
            return self.last_type

        if self.last_file==evtdata.event.object().getTFile().GetName():            
            return self.last_type

        self.last_file=evtdata.event.object().getTFile().GetName()
        
        sig_id = evtdata.get("geninfo").signalProcessID()
        if not hasattr(ROOT,"getCOMEnergy"):
            ROOT.gInterpreter.Declare("""
#include "FWCore/ParameterSet/interface/ParameterSet.h"
double getCOMEnergy(edm::ParameterSet& pset){
   const auto& genPSet = pset.getParameterSet("generator");
   if(genPSet.exists("comEnergy")){
     return genPSet.getParameter<double>("comEnergy");
   }else{
     return -1.;
   }
}
                """)
        cfg = ROOT.edm.ProcessConfiguration()  
        proc_hist = evtdata.event.object().processHistory() 
        proc_hist.getConfigurationForProcess("SIM",cfg) 
        cfg_pset = evtdata.event.object().parameterSet(cfg.parameterSetID())  
        com_energy = ROOT.getCOMEnergy(cfg_pset)
        if com_energy<0:
            com_energy= 14000
        if sig_id >=101 and sig_id<=106:
            self.last_type = MCSample(MCSample.ProcType.MB,com_energy=com_energy)
        elif sig_id>=111 and sig_id<=124:
            if not hasattr(ROOT,"qcdMCFiltType"):
                ROOT.gInterpreter.Declare("""
#include "FWCore/ParameterSet/interface/ParameterSet.h"
int qcdMCFiltType(edm::ParameterSet& pset,const int inclCode,const int emCode,const int muCode){
   if(pset.exists("emenrichingfilter")) return emCode;
   else if(pset.exists("mugenfilter")) return muCode;
   else return inclCode;
}
                """)  
                ROOT.gInterpreter.Declare("""
#include "FWCore/ParameterSet/interface/ParameterSet.h"
std::vector<std::string> getGenProcParam(edm::ParameterSet& pset){
   const auto& genPSet = pset.getParameterSet("generator");
   const auto& pythPSet = genPSet.getParameterSet("PythiaParameters");
   return pythPSet.getParameter<std::vector<std::string> >("processParameters");
}
                """)
              
            filt_type = ROOT.qcdMCFiltType(cfg_pset,MCSample.FiltType.Incl,MCSample.FiltType.Em,
                                           MCSample.FiltType.Mu)
            proc_params = ROOT.getGenProcParam(cfg_pset)
            min_pthat = 0
            max_pthat = 9999
            for param in proc_params:
                if param.lstrip().startswith("PhaseSpace:pTHatMin"):
                    min_pthat = float(self.getval_re.search(param).group(1))
                if param.lstrip().startswith("PhaseSpace:pTHatMax"):
                    max_pthat = float(self.getval_re.search(param).group(1))
            self.last_type = MCSample(MCSample.ProcType.QCD,filt_type,min_pthat,max_pthat,com_energy)

        elif sig_id==221:
            self.last_type = MCSample(MCSample.ProcType.DY,com_energy=com_energy)
        elif sig_id==9999:
            #not this just means its an external generator but now we have to figure out DY and WJets from the filename name for now
            if self.last_file.find("DYJets")!=-1:
                self.last_type = MCSample(MCSample.ProcType.DY,com_energy=com_energy)
            elif self.last_file.find("WJets")!=-1:
                self.last_type = MCSample(MCSample.ProcType.WJets,com_energy=com_energy)
            else:
                self.last_type = MCSample(MCSample.ProcType.Unknown)
        else:
            self.last_type = MCSample(MCSample.ProcType.Unknown)
        
        return self.last_type
