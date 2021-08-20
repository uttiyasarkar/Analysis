from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ROOT
import re

def get_indx_best_gsf(egobj):
    min_epm1=999.9
    min_mhit=999
    index_best_gsf=0
    for index,gsf in enumerate(egobj.gsfTracks()):
        this_mhit = gsf.hitPattern().numberOfLostHits(ROOT.reco.HitPattern.MISSING_INNER_HITS)
        this_epm1 = abs(( (egobj.superCluster().energy()) /  (gsf.innerMomentum().R() ) ) - 1)
        if ( this_mhit < min_mhit ):
            min_mhit=this_mhit
            if (this_epm1 < min_epm1): min_epm1 = this_epm1
            index_best_gsf=index
        elif (this_mhit == min_mhit):
            if (this_epm1 < min_epm1):
                index_best_gsf=index
    return index_best_gsf


def get_nlayerpix_gsf(egobj):
    if egobj.gsfTracks().empty():
        return 0
    else:
        indx_bestgsf=get_indx_best_gsf(egobj)
        return egobj.gsfTracks()[indx_bestgsf].hitPattern().pixelLayersWithMeasurement()


def get_nlayerstrip_gsf(egobj):
    if egobj.gsfTracks().empty():
        return 0
    else:
        indx_bestgsf=get_indx_best_gsf(egobj)
        return egobj.gsfTracks()[indx_bestgsf].hitPattern().stripLayersWithMeasurement()


def get_normchi2_gsf(egobj):
    if egobj.gsfTracks().empty():
        return 999
    else:
        indx_bestgsf=get_indx_best_gsf(egobj)
        return egobj.gsfTracks()[indx_bestgsf].normalizedChi2() 

def get_ngsf(egobj):
    return len(egobj.gsfTracks())

