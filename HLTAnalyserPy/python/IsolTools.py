from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ROOT
import sys
import re

import Analysis.HLTAnalyserPy.GsfTools as GsfTools

# Redefined isolation variables for phase-2, 
# more details in 
# https://indico.cern.ch/event/962025/contributions/4088172/attachments/2135799/3597622/HLT%20Workshop%2003_11_2020.pdf

def get_hlt_iso(egobj,evtdata,trkcoll="trksv6",min_pt=1.,max_dz=0.15,min_deta=0.01,max_dr2=0.3*0.3,min_dr2=0.01*0.01):

    if egobj.gsfTracks().empty():
        return 99. # if no gsf track, then that SC do not pass track isolation

    indx_bestgsf = GsfTools.get_indx_best_gsf(egobj)

    eta = egobj.gsfTracks()[indx_bestgsf].eta()
    phi = egobj.gsfTracks()[indx_bestgsf].phi()
    vz = egobj.gsfTracks()[indx_bestgsf].vz() 

    isol = 0.

    trks = evtdata.get(trkcoll)
    for trk in trks:
        if trk.pt()<min_pt: continue
        dz = vz - trk.vz()
        if abs(dz)>max_dz: continue
        deta = eta - trk.eta()
        if abs(deta)<min_deta: continue #selecting a phi strip cutting on eta
        dr2 = ROOT.reco.deltaR2(eta,phi,trk.eta(),trk.phi())
        if dr2 > max_dr2 or dr2 < min_dr2: continue
        isol+=trk.pt()

    return isol

def get_l1_iso(egobj,evtdata,min_pt=2.,max_dz=0.7,min_deta=0.003,max_dr2=0.3*0.3,min_dr2=0.01*0.01):

    if egobj.gsfTracks().empty():
        return 99999. # if no gsf track, then that SC do not pass track isolation  

    indx_bestgsf = GsfTools.get_indx_best_gsf(egobj)

    eta = egobj.gsfTracks()[indx_bestgsf].eta()
    phi = egobj.gsfTracks()[indx_bestgsf].phi()
    vz = egobj.gsfTracks()[indx_bestgsf].vz()
                      
    l1isol = 0.

    l1trks = evtdata.get("l1trks")
    for l1trk_extra in l1trks:
        l1trk = l1trk_extra.ttTrk()
        pt = l1trk.momentum().perp()
        if pt <min_pt: continue
        dz = vz - l1trk.z0()
        if abs(dz)>max_dz: continue
        deta = eta - l1trk.eta() #selecting a phi strip cutting on eta
        if abs(deta)<min_deta: continue
        dr2 = ROOT.reco.deltaR2(eta,phi,l1trk.eta(),l1trk.phi())
        if dr2 > max_dr2 or dr2 < min_dr2: continue
        l1isol+=pt

    return l1isol


def get_hgcal_iso(egobj,evtdata,min_pt=2.0,min_deta=0.0,max_dr2=0.2*0.2,min_dr2=0.0*0.0):
    hgcal_isol=0
    ele_eta = egobj.superCluster().eta()
    ele_phi = egobj.superCluster().phi()
    for clus in evtdata.get("hgpfclus"):
        if clus.pt()<min_pt: continue
        if abs(clus.eta()-ele_eta)<min_deta: continue
        dr2 = ROOT.reco.deltaR2(ele_eta,ele_phi,clus.eta(),clus.phi())
        if dr2>max_dr2 or dr2<min_dr2: continue
        sc_seed_ids = [c.seed().rawId() for c in egobj.superCluster().clusters()]
        if clus.seed().rawId() not in sc_seed_ids:
                hgcal_isol+=clus.pt()
    return hgcal_isol

# hgcal isolation based on 2D layer clusters
def get_hgcal_iso_layerclus(egobj,evtdata,min_dr_had=0.0,min_dr_em=0.02,max_dr=0.2,min_energy_had=0.07,min_energy_em=0.02):
    layerclus = evtdata.get("hglayerclus")
    hgcal_isol_had = ROOT.HGCalClusterTools.hadEnergyInCone(egobj.eta(),egobj.phi(),layerclus,min_dr_had,max_dr,0.0,min_energy_had)
    hgcal_isol_em   = ROOT.HGCalClusterTools.emEnergyInCone(egobj.eta(),egobj.phi(),layerclus,min_dr_em, max_dr,0.0,min_energy_em)
    hgcal_isol = hgcal_isol_had + hgcal_isol_em
    return hgcal_isol


def get_ecal_iso(egobj,evtdata,min_pt=0.0,min_deta=0.0,max_dr2=0.2*0.2,min_dr2=0.0*0.0):
    ecal_isol=0
    ele_eta = egobj.superCluster().eta()
    ele_phi = egobj.superCluster().phi()
    for clus in evtdata.get("ecalpfclus"):
        if clus.pt()<min_pt: continue
        if abs(clus.eta()-ele_eta)<min_deta: continue
        dr2 = ROOT.reco.deltaR2(ele_eta,ele_phi,clus.eta(),clus.phi())
        if dr2>max_dr2 or dr2<min_dr2: continue
        sc_seed_ids = [c.seed().rawId() for c in egobj.superCluster().clusters()]
        if clus.seed().rawId() not in sc_seed_ids:
                ecal_isol+=clus.pt()
    return ecal_isol


def get_hcal_iso(egobj,evtdata,min_pt=2.0,min_deta=0.0,max_dr2=0.3*0.3,min_dr2=0.05*0.05):
    hcal_isol=0
    ele_eta = egobj.superCluster().eta()
    ele_phi = egobj.superCluster().phi()
    for clus in evtdata.get("hcalpfclus"):
        if clus.pt()<min_pt: continue
        if abs(clus.eta()-ele_eta)<min_deta: continue
        dr2 = ROOT.reco.deltaR2(ele_eta,ele_phi,clus.eta(),clus.phi())
        if dr2>max_dr2 or dr2<min_dr2: continue
        hcal_isol+=clus.pt()
    return hcal_isol


# hcal depth vars, for H/E
# this is not strictly isolation, but still adding in IsolTools, if needed can move to separate file later
def get_hcalen_depth(egobj,evtdata,depth=1):
    seed_id = egobj.superCluster().seed().seed() # get seed crystal
    if seed_id.subdetId()!=1: # if seed crystal not in barrel, return 0.  
        return 0.0
    seed_ebid = ROOT.EBDetId(seed_id)
    seed_tower_ieta = seed_ebid.tower_ieta() # hcal tower behind seed crystal
    seed_tower_iphi = seed_ebid.tower_iphi()
    hcal_id = ROOT.HcalDetId(ROOT.HcalBarrel,seed_tower_ieta,seed_tower_iphi,depth)
    hits = evtdata.get("hcalhits")
    hit = hits.find(hcal_id)
    if hit != hits.end():
        return hit.energy()
    else:
        return 0.
