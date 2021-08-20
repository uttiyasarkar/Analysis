from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ROOT
import re

def pass_eg_qual(l1obj):
    if abs(l1obj.eta())<1.479:
        return (l1obj.EGRef().hwQual()&0x2)!=0
    else:
        return l1obj.EGRef().hwQual()==5

def pass_ele_isol(l1obj):
    if abs(l1obj.eta())<1.479:
        return l1obj.trkIsol()<0.12
    else:
        return l1obj.trkIsol()<0.2


def pass_pho_isol(l1obj):
    if abs(l1obj.eta())<1.479:
        return l1obj.trkIsol()<0.35
    else:
        return l1obj.trkIsol()<0.28

def pass_eg_isol(l1obj):
    if type(l1obj).__name__=='TkElectron':
        return pass_ele_isol(l1obj)
    else:
        return pass_pho_isol(l1obj)
    
def make_egscale_dict():
    scale_text = """function :: EGPhotonOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-2.6604)/1.06077 if abs(Eta)<1.5 else Et>(offline-3.17445)/1.13219
function :: EGElectronOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-2.86427)/1.16564 if abs(Eta)<1.5 else Et>(offline-3.41935)/1.20041
function :: TkElectronOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-0.805095)/1.18336 if abs(Eta)<1.5 else Et>(offline-0.453144)/1.26205
function :: TkIsoElectronOfflineEtCut :: args:=(offline,Et,Eta); lambda:=Et>(offline-0.434262)/1.20586 if abs(Eta)<1.5 else Et>(offline-0.266186)/1.25976"""

    scales_dict = {}
    for line in scale_text.split("\n"):
        func_name = re.match(r'.*:: ([\w]+) ::',line).group(1)
        params = [float(x) for x in re.findall(r'[-\d.]+',line)]
        scales_dict.update({
            func_name : {
                'offset_eb' : params[0],'scale_eb' : params[1],
                'eta_boundary' : params[2],
                'offset_hgcal' : params[3],'scale_hgcal' : params[4]
            }
        })
    return scales_dict

def get_offthres_func(egobj,eta_boundary,offset_eb,scale_eb,offset_hgcal,scale_hgcal):
    if abs(egobj.eta()) < eta_boundary:
        return egobj.et()*scale_eb - offset_eb
    else:
        return egobj.et()*scale_hgcal - offset_hgcal

def get_offthres(egobj,params):
    if abs(egobj.eta()) < params['eta_boundary']:
        return egobj.et()*params['scale_eb'] - params['offset_eb']
    else:
        return egobj.et()*params['scale_hgcal'] - params['offset_hgcal']

def eg_thres(egobj,scales_dict,use_noniso=False,use_iso=False):
    if use_noniso and use_iso:
        raise ValueError("error, use_noniso and use_iso can not both be truth")
    func_name = None
    if type(egobj).__name__=='TkElectron':
        if use_iso or (not use_noniso and pass_ele_isol(egobj)):
            func_name="TkIsoElectronOfflineEtCut"
        else:
            func_name="TkElectronOfflineEtCut"
    else:
        func_name = "EGElectronOfflineEtCut"
    return get_offthres(egobj,scales_dict[func_name])
        
def get_l1ele_from_l1pho(l1pho,l1eles):
    for l1ele in l1eles:
        if l1ele.EGRef()==l1pho.EGRef():
            return l1ele
    return None
    

                    

