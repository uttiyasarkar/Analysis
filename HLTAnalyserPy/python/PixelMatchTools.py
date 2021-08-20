from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ROOT
import re

# spread (aka a_params) obtained from fit performed in phase2 DoubleEle gun sample
def get_a_dphi1_phase2(abseta,nclus):
   fx=999.
   x=abseta
   if (nclus==1):
      if (x>=0.0 and x<1.5): fx = 2.73931e-03 - 2.51994e-03*x + 3.24979e-03*x*x
      if (x>=1.5 and x<2.4): fx = 3.79945e-02 - 3.34501e-02*x + 7.99893e-03*x*x
      if (x>=2.4): fx = 5.79179e-03 - 9.56301e-03*x + 3.57333e-03*x*x  
      # fits are done upto |SC eta|<3.0
      # but here, not specifying upper |eta| as 3.0. 
      # if an electron has |eta|>3.0 for mismeasurement, that won't be rejected due to pm_s2 
   if (nclus==2):
      if (x>=0.0 and x<1.5): fx = 4.65536e-03 - 1.70883e-03*x + 2.23950e-03*x*x
      if (x>=1.5): fx = 2.94649e-02 - 2.35045e-02*x + 5.66937e-03*x*x
   if (nclus>2):
      if (x>=0.0 and x<1.5): fx = 6.12202e-03 - 9.85677e-04*x + 2.30772e-03*x*x
      if (x>=1.5 and x<2.0): fx = 2.27801e-02 - 8.99003e-03*x
      if (x>=2.0): fx = -0.0448686 + 0.0405059*x - 0.00789926*x*x
   return fx


def get_a_dphi2_phase2(abseta,nclus):
   fx=999.
   x=abseta
   if (nclus>0):
      if (x>=0.0 and x<0.6): fx = 2.62924e-04 - 1.25750e-04*x
      if (x>=0.6 and x<1.47): fx = -2.83732e-04 + 1.05965e-03*x - 4.60304e-04*x*x
      if (x>=1.47): fx = 1.72122e-03 - 1.49787e-03*x + 3.70645e-04*x*x
   return fx


def get_a_drz2_phase2(abseta,nclus):
   fx=999
   x=abseta
   if (nclus>0):
      if (x>=0.0 and x<1.13): fx = 5.02445e-03 - 4.77990e-03*x + 8.08078e-03*x*x
      if (x>=1.13 and x<1.48): fx = 2.00700e-01 -3.05712e-01*x + 1.21756e-01*x*x
      if (x>=1.48 and x<1.9): fx = 1.69387e-01 -1.77821e-01*x +4.77192e-02*x*x
      if (x>=1.9): fx = 2.45799e-02 -1.97369e-02*x + 4.51283e-03*x*x
   return fx


def get_pms2_phase2(egobj):
    abseta=abs(egobj.superCluster().eta())
    nclus=egobj.superCluster().clustersSize()

    #get a_params
    dphi1const =  get_a_dphi1_phase2(abseta,nclus)
    dphi2const =  get_a_dphi2_phase2(abseta,nclus)
    drz2const  =  get_a_drz2_phase2(abseta,nclus)

    min_s2=9999.
    for seed in egobj.seeds():
        charge = seed.getCharge()
        if (charge < 0):   
            dphi1_term=seed.dPhiNeg(0)/dphi1const
            dphi2_term=seed.dPhiNeg(1)/dphi2const
            drz2_term=seed.dRZNeg(1)/drz2const
        elif (charge > 0): 
            dphi1_term=seed.dPhiPos(0)/dphi1const 
            dphi2_term=seed.dPhiPos(1)/dphi2const
            drz2_term=seed.dRZPos(1)/drz2const
            
        this_s2 = dphi1_term*dphi1_term + dphi2_term*dphi2_term + drz2_term*drz2_term

        if (this_s2 < min_s2):
            min_s2=this_s2
           
    return min_s2
