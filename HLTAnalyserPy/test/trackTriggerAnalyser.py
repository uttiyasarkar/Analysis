#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from array import array
import argparse
import sys
import ROOT
import numpy as np

from DataFormats.FWLite import Events, Handle
from Analysis.HLTAnalyserPy.EvtData import EvtData, EvtHandles,phaseII_products
import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.GenTools as GenTools

def cal_trk_iso(ele_trk,trks,max_dr2,min_dr2,min_dphi,max_dz,min_pt):

    #an example of the cuts applied to general tracks
    #we can also add in some cuts on other track quantities later one
    #but now we just cut on pt,eta,phi and vtx
    eta = ele_trk.eta()
    phi = ele_trk.phi()
    vz = ele_trk.vz() #this is the z vertex of the track, important for PU rejection
    
    isol = 0.
    
    for trk in trks:
        #note the ordering of the cuts, done so the expensive dR2 calculation is done last
        #note that its dr*dr not dr that is calcualted to save time
        if trk.pt()<min_pt: continue
        dz = vz - trk.vz()
        if abs(dz)>max_dz: continue
        dphi = ROOT.reco.deltaPhi(phi,trk.phi())
        if abs(dphi)<min_dphi: continue
        dr2 = ROOT.reco.deltaR2(eta,phi,trk.eta(),trk.phi())
        if dr2 > max_dr2 or dr2 < min_dr2: continue
        isol+=trk.pt()

    return isol

def cal_l1trk_iso(ele_trk,l1trks,max_dr2,min_dr2,min_dphi,max_dz,min_pt):

    #an example of the cuts applied to general tracks
    #we can also add in some cuts on other track quantities later one
    #but now we just cut on pt,eta,phi and vtx
    eta = ele_trk.eta()
    phi = ele_trk.phi()
    vz = ele_trk.vz() #this is the z vertex of the track, important for PU rejection

    isol = 0.

    for l1trk_extra in l1trks:
        #note the ordering of the cuts, done so the expensive dR2 calculation is done last
        #note that its dr*dr not dr that is calculated to save time
        l1trk = l1trk_extra.ttTrk()
        pt = l1trk.momentum().perp()
        if pt <min_pt: continue
        dz = vz - l1trk.z0()
        if abs(dz)>max_dz: continue
        dphi = ROOT.reco.deltaPhi(phi,l1trk.phi())
        if abs(dphi)<min_dphi: continue
        dr2 = ROOT.reco.deltaR2(eta,phi,l1trk.eta(),l1trk.phi())
        if dr2 > max_dr2 or dr2 < min_dr2: continue
        isol+=pt

    return isol




if __name__ == "__main__":

    CoreTools.load_fwlitelibs()

    L1isohistB = []
    L1isohistE = []
    V0isohistB = []
    V0isohistE = []

    ROOT.gROOT.SetStyle('Plain') # white background
    for index in range(1,11,1):
        value = index*0.1
        L1isohistB_element = ROOT.TH1F ("L1isohistB"+str(index), "Trk_isol_l1 distribution dz_max (Barrel) = "+str(value), 60, 0, 60)
        L1isohistB.append(L1isohistB_element)
        L1isohistE_element = ROOT.TH1F ("L1isohistE"+str(index), "Trk_isol_l1 distribution dz_max (Endcaps) = "+str(value), 60, 0, 60)
        L1isohistE.append(L1isohistE_element)
        V0isohistB_element = ROOT.TH1F ("V0isohistB"+str(index), "Trk_isol_v0 distribution dz_max (Barrel) = "+str(value), 60, 0, 60)
        V0isohistB.append(V0isohistB_element)
        V0isohistE_element = ROOT.TH1F ("V0isohistE"+str(index), "Trk_isol_v0 distribution dz_max (Endcaps) = "+str(value), 60, 0, 60)
        V0isohistE.append(V0isohistE_element)


    parser = argparse.ArgumentParser(description='example e/gamma HLT analyser')
    parser.add_argument('in_filename',nargs="+",help='input filename')
    parser.add_argument('--out','-o',default="output.root",help='output filename')
    parser.add_argument('--weights','-w',default="weights.json",help="weights filename")
    args = parser.parse_args()
   
    events = Events(args.in_filename)    
    evtdata = EvtData(phaseII_products,verbose=True)
    weights = EvtWeights(args.weights)

    L1signalB = [0,0,0,0,0,0,0,0,0,0]
    V0signalB = [0,0,0,0,0,0,0,0,0,0]
    V2signalB = [0,0,0,0,0,0,0,0,0,0]
    L1signalE = [0,0,0,0,0,0,0,0,0,0]
    V0signalE = [0,0,0,0,0,0,0,0,0,0]
    V2signalE = [0,0,0,0,0,0,0,0,0,0]
    L1sig_vs_rateB = [0,0,0,0,0,0,0,0,0,0] 
    V0sig_vs_rateB = [0,0,0,0,0,0,0,0,0,0]
    V2sig_vs_rateB = [0,0,0,0,0,0,0,0,0,0]
    L1sig_vs_rateE = [0,0,0,0,0,0,0,0,0,0] 
    V0sig_vs_rateE = [0,0,0,0,0,0,0,0,0,0]
    V2sig_vs_rateE = [0,0,0,0,0,0,0,0,0,0]
    total_egtracks = 0

    for event_nr,event in enumerate(events):
        evtdata.get_handles(event)

        weight = weights.weight_from_evt(event.object())

        for egobj in evtdata.handles.egtrigobjs.product():
             if not egobj.gsfTracks().empty():
                total_egtracks += egobj.gsfTracks().size()
                print("total eg_tracks", total_egtracks)             
                if egobj.et() <20: continue

                for A in range(1,11,1):
                    #taking the first gsf track entry for now
                    trk_isol_v0  = cal_trk_iso(egobj.gsfTracks()[0],evtdata.handles.trksv0.product(),max_dr2=0.2*0.2,min_dr2=0.03*0.03,min_dphi=0.01,max_dz=A*0.1,min_pt=1)
                    #trk_isol_v2  = cal_trk_iso(egobj.gsfTracks()[0],evtdata.handles.trksv2.product(),max_dr2=0.2*0.2,min_dr2=0.03*0.03,min_dphi=0.01,max_dz=0.1,min_pt=1)
                    trk_isol_l1 =  cal_l1trk_iso(egobj.gsfTracks()[0],evtdata.handles.l1trks.product(),max_dr2=0.2*0.2,min_dr2=0.03*0.03,min_dphi=0.01,max_dz=A*0.1,min_pt=1)
                    if (egobj.gsfTracks()[0].eta() < abs(1.5)):
                       L1signalB[A-1]+=1
                       L1isohistB[A-1].Fill( trk_isol_l1, weight )
                       V0signalB[A-1]+=1
                       V0isohistB[A-1].Fill( trk_isol_v0, weight )
                       #V2signalB[A-1]+=1
                       #V2isohistB[A-1].Fill( trk_isol_v2 )
                    if ( ((egobj.gsfTracks()[0].eta() > 1.5) and (egobj.gsfTracks()[0].eta() < 3.0)) or ((egobj.gsfTracks()[0].eta() < -1.5) and (egobj.gsfTracks()[0].eta() > -3.0)) ):
                        L1signalE[A-1]+=1
                        L1isohistE[A-1].Fill( trk_isol_l1, weight )
                        V0signalE[A-1]+=1
                        V0isohistE[A-1].Fill( trk_isol_v0, weight )
                        #V2signalE[A-1]+=1
                        #V2isohistE[A-1].Fill( trk_isol_v2 )

    #print "total tracks ", total_egtracks
    #print "segnale ", L1signalB 

    for A in range(1,11,1):
        if total_egtracks != 0:
           L1sig_vs_rateB[A-1] = float(L1signalB[A-1])/float(total_egtracks)
           print("{} {} {} {}".format("L1 tracks-> Signal vs rate dz_max = ", A*0.1, ":", L1sig_vs_rateB[A-1]))
        if total_egtracks != 0:
           V0sig_vs_rateB[A-1] = float(V0signalB[A-1])/float(total_egtracks)
           print("{} {} {} {}".format("V0 tracks-> Signal vs rate dz_max = ", A*0.1, ":", V0sig_vs_rateB[A-1]))
        #if total_egtracks != 0:
          #V2sig_vs_rateB[A-1] = float(V2signalB[A-1])/float(total_egtracks)
          #print("{} {} {} {}".format("V2 tracks-> Signal vs rate dz_max = ", A*0.1, ":", V2sig_vs_rateB[A-1]))
      
    outHistFile = ROOT.TFile.Open(args.out, "RECREATE")
    outHistFile.cd()
    for A in range(1,11,1):
        L1isohistB[A-1].Write()   
        V0isohistB[A-1].Write()
        L1isohistE[A-1].Write()
        V0isohistE[A-1].Write()
    outHistFile.Close() 
