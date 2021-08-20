from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ROOT

import Analysis.HLTAnalyserPy.CoreTools as CoreTools

class CutBin:
    def __init__(self,var_func,var_label,bins,do_abs=False):
        self.var_func = CoreTools.UnaryFunc(var_func)
        self.var_label = var_label
        self.do_abs = do_abs
        self.bins = []

        for idx,bin_low in enumerate(bins[:-1]):
            bin_high = bins[idx+1]            
            if bin_low!=None and bin_high!=None:
                self.bins.append([bin_low,bin_high])
       
    def get_binnr(self,obj):
        var = self.var_func(obj)
        if self.do_abs:
            var = abs(var)
        for bin_nr,bin_range in enumerate(self.bins):
            if var>=bin_range[0] and var<bin_range[1]:
                return bin_nr
        return None

    def get_bin_str(self,binnr):
        return "{}{}{}".format(self.bins[binnr][0],self.var_label,self.bins[binnr][1]).replace(".","p").replace("-","M")
        
    def get_cut_label(self,binnr):
        return "{} #leq {} < {}".format(self.bins[binnr][0],self.var_label,self.bins[binnr][1])

class VarHist:
    def __init__(self,var_func,name,title,nbins,var_min,var_max,cut_func=None,cut_labels=[]):
        self.var_func = CoreTools.UnaryFunc(var_func)
        self.cut_func = cut_func
        self.hist = ROOT.TH1D(name,title,nbins,var_min,var_max)
        self.cut_labels = cut_labels

    def passcut(self,obj):
        if self.cut_func:
            return self.cut_func(self.var_func(obj))
        else:
            return True
    
    def fill(self,obj,weight=1.):
        self.hist.Fill(self.var_func(obj),weight)

class HistBin:
    def __init__(self,name,bin_suffix,title,nbins,var_min,var_max,cut_labels=[]):
        self.bin_suffix = str(bin_suffix)
        name = "{name}{suffix}".format(name=name,suffix=self.bin_suffix)
        self.hist = ROOT.TH1D(name,title,nbins,var_min,var_max)

        self.cut_labels = cut_labels
    
    def fill(self,var,weight=1.):
        self.hist.Fill(var,weight)

class VarHistBinned:

    def init_hists(self,hists,cutbins,bin_suffix,cut_labels,title,nbins,var_min,var_max):
        for bin_nr,bin_range in enumerate(cutbins[0].bins):
            hists.append([])
            newbin_suffix = "{}{}Bin{}".format(bin_suffix,cutbins[0].var_label,bin_nr)
            newcut_labels = list(cut_labels)
            newcut_labels.append(cutbins[0].get_cut_label(bin_nr))
            if cutbins[1:]:
                self.init_hists(hists[-1],cutbins[1:],newbin_suffix,newcut_labels,title,nbins,var_min,var_max)
            else:
                name = "{}{}".format(self.basename,self.coll_suffix)
                hists[-1] = HistBin(name,newbin_suffix,title,nbins,var_min,var_max,newcut_labels)
            

    def __init__(self,var_func,cutbins,basename,coll_suffix,title,nbins,var_min,var_max,use_for_eff=False):
        #we remove the cuts on the variable we are plotting
        self.cutbins = [cb for cb in cutbins if cb.var_func!=var_func]
        self.hists = []
        self.basename = basename
        self.coll_suffix = coll_suffix
        self.var_func = CoreTools.UnaryFunc(var_func)
        self.use_for_eff = use_for_eff
        self.init_hists(self.hists,self.cutbins,"",[],title,nbins,var_min,var_max)
        
    def _fill(self,var,obj,hists,cutbins,weight=1.):
        bin_nr = cutbins[0].get_binnr(obj)
        if bin_nr!=None:
            if cutbins[1:]:
                self._fill(var,obj,hists[bin_nr],cutbins[1:],weight)
            else:
                hists[bin_nr].fill(var,weight)
            
    def fill(self,obj,weight=1.):
        var = self.var_func(obj)
        self._fill(var,obj,self.hists,self.cutbins,weight)

    def _get_hist_data(self,hists,data):
        """ Okay this is a bit dirty, as the histograms are in n-dim list 
        it recursively loops over the list entry till its no longer a sequence
        which means it found the histogram and can append its data
        """
        try:
            for hist in hists:
                self._get_hist_data(hist,data)
        except TypeError:
            hist_dict = {"name" : hists.hist.GetName(),"cut_labels" : hists.cut_labels, "use_for_eff" : self.use_for_eff}
            data.append(hist_dict)
        return data

    def get_hist_data(self):
        data = []
        return self._get_hist_data(self.hists,data)

        
    def _get_hists(self,hists,hist_list):
        """ Okay this is a bit dirty, as the histograms are in n-dim list 
        it recursively loops over the list entry till its no longer a sequence
        which means it found the histogram and can append its data
        """
        try:
            for hist in hists:
                self._get_hists(hist,hist_list)
        except TypeError:
            hist_list.append(hists)
        return hist_list
        
    def get_hists(self):
        hist_list = []
        return self._get_hists(self.hists,hist_list)
        

class HistCollData: 
    def setval(self,**kwargs):
        for key,value in kwargs.items():
            if hasattr(self,key):
                setattr(self,key,value)
            else:
                raise AttributeError("HistCollData has no attribute {}".format(key))

    def __init__(self,**kwargs):
        self.desc = ""
        self.norm_val = 0.
        self.label = ""
        self.is_normable = True
        self.is_effhist = False
        self.display = True
        self.hist_names = []
        self.setval(**kwargs)
    

class HistColl:
    def __init__(self,suffix,label="",desc="",norm_val=0.,cutbins=None):
        self.hists = []
        self.suffix = suffix
        self.metadata = HistCollData(label=str(label),desc=str(desc),norm_val=norm_val)
        self.cutbins = cutbins

    def strip_suffix(self,name):
        start = name.rfind(self.suffix)
        if start!=-1:
            return name[0:start]
        else:
            return str(name)

    def add_hist(self,var_func,name,title,nbins,var_min,var_max,use_for_eff=False):
        self.hists.append(VarHistBinned(var_func,self.cutbins,name,self.suffix,title,nbins,var_min,var_max,use_for_eff))
    
    def get_hist(self,name):
        for hist in self.hists:
            if hist.basename==name:
                return hist
        return None

    def fill(self,obj,weight=1.):
        for histnr,hist in enumerate(self.hists):
            hist.fill(obj,weight)

    def get_metadata_dict(self):
        md_dict = dict(self.metadata.__dict__)
        print(md_dict)
        md_dict['hists'] = {}
    
        for hist in self.hists:
            md_dict['hists'][hist.basename]=hist.get_hist_data()
        return md_dict
            
    

def create_histcoll(add_gsf=False,tag="",label="",desc="",norm_val=0.,cutbins=None,meta_data=None):
    hist_coll = HistColl("{tag}Hist".format(tag=tag),label=label,desc=desc,norm_val=norm_val,cutbins=cutbins)
    hist_coll.add_hist("et()","et",";E_{T} [GeV];entries",20,0,100,use_for_eff = True)
    hist_coll.add_hist("et_gen","etGen",";E_{T}^{gen} [GeV];entries",20,0,100,use_for_eff = True)
    hist_coll.add_hist("eta()","eta",";#eta;entries",60,-3,3,use_for_eff = True)
    hist_coll.add_hist("phi()","phi",";#phi [rad];entries",64,-3.2,3.2,use_for_eff = True)

    hist_coll.add_hist('var("hltEgammaClusterShapeUnseeded_sigmaIEtaIEta5x5",0)',"sigmaIEtaIEta",";#sigma_{i#etai#eta};entries",100,0,0.1)
    hist_coll.add_hist('var("hltEgammaEcalPFClusterIsoUnseeded",0)',"ecalPFClusIso",";ecal pf clus isol [GeV];entries",100,0,20)
    hist_coll.add_hist('var("hltEgammaHcalPFClusterIsoUnseeded",0)',"hcalPFClusIso",";hcal pf clus isol [GeV];entries",100,0,20)
    hist_coll.add_hist('var("hltEgammaHGCalPFClusterIsoUnseeded",0)',"hgcalPFClusIso",";hgcal pf clus isol [GeV];entries",100,0,20)
    hist_coll.add_hist('var("hltEgammaHoverEUnseeded",0)',"hcalHForHOverE",";HCAL H for H/E [GeV];entries",100,0,20)
    hist_coll.add_hist('var("hltEgammaHGCALIDVarsUnseeded_hForHOverE",0)',"hgcalHForHOverE",";HGCAL H for H/E [GeV];entries",100,0,20) 
    hist_coll.add_hist('var("hltEgammaHGCALIDVarsUnseeded_sigma2uu",0)',"sigma2uu",";#sigma^{2}_{uu};entries",100,0,50)
    hist_coll.add_hist('var("hltEgammaHGCALIDVarsUnseeded_sigma2vv",0)',"sigma2vv",";#sigma^{2}_{vv};entries",100,0,2)
    hist_coll.add_hist('var("hltEgammaHGCALIDVarsUnseeded_sigma2ww",0)',"sigma2ww",";#sigma^{2}_{ww};entries",100,0,250)
    
    
    if add_gsf:
        hist_coll.add_hist('var("hltEgammaPixelMatchVarsUnseeded_s2,0)',"pmS2","PM S2",100,0,100)
        hist_coll.add_hist("gsfTracks().at(0).pt()","gsfTrkPt",";GsfTrk p_{T} [GeV];entries",20,0,100)
        hist_coll.add_hist('var("hltEgammaGsfTrackVarsUnseeded_Chi2")',"gsfChi2","Gsf Track #chi^{2}",100,0,100)
        hist_coll.add_hist('var("hltEgammaGsfTrackVarsUnseeded_DetaSeed")',"deltaEtaInSeed","#Delta#eta_{in}^{seed}",100,0,0.02)
        hist_coll.add_hist('var("hltEgammaGsfTrackVarsUnseeded_Dphi")',"deltaPhiIn","#Delta#phi_{in}",100,0,0.1)
        hist_coll.add_hist('var("hltEgammaGsfTrackVarsUnseeded_MissingHits")',"missHits","#miss hits",5,-0.5,4.5)
        hist_coll.add_hist('var("hltEgammaGsfTrackVarsUnseeded_ValidHits")',"validHits","#valid hits",21,-0.5,20.5)
        hist_coll.add_hist('var("hltEgammaGsfTrackVarsUnseeded_OneOESuperMinusOneOP")',"invEminusInvP","1/E - 1/p",100,-0.5,2)
        hist_coll.add_hist('var("hltEgammaEleGsfTrackIsoUnseeded")',"trkIsoV0","trk V0 isol",100,0,20)
        hist_coll.add_hist('var("hltEgammaEleGsfTrackIsoV6Unseeded")',"trkIsoV6","trk V6 isol",100,0,20)
        hist_coll.add_hist('var("hltEgammaEleGsfTrackIsoV72Unseeded")',"trkIsoV72","trk V72 isol",100,0,20)
        hist_coll.add_hist('var("hltEgammaEleL1TrkIsoUnseeded",0)',"trkIsoL1","L1 trk isol",100,0,20)
       
        
        
    if meta_data!=None:
        meta_data[tag] = hist_coll.get_metadata_dict()
    return hist_coll

def make_effhists_fromcoll_old(numer,denom,tag="",dir_=None,out_hists=[]):
    #building a map for numer hists
    numer_hist_map = {}
    for varhist in numer.hists:
        numer_hist_map[numer.strip_suffix(varhist.hist.GetName())] = varhist.hist
    
    for denom_varhist in denom.hists:
        hist_name = denom.strip_suffix(denom_varhist.hist.GetName())
        try:
            numer_hist = numer_hist_map[hist_name] 
            eff_hist = numer_hist.Clone("{name}{tag}EffHist".format(name=hist_name,tag=tag))
            eff_hist.Divide(numer_hist,denom_varhist.hist,1,1,"B")
            eff_hist.Draw()
            if dir_:
                eff_hist.SetDirectory(dir_)
            out_hists.append(eff_hist)
        except KeyError:
            print("hist {} not found".format(hist_name))
            print(numer_hist_map)
    return out_hists
 
def make_effhists_fromcoll_binned(numer,denom,tag="",dir_=None,out_hists=[],hists_data=None):
    numer_hist_map = {}
    numer_hists = numer.get_hists()
    for hist in numer_hists:
        numer_hist_map["{}{}".format(numer.basename,hist.bin_suffix)] = hist
        
    denom_hists = denom.get_hists()
    for denom_hist in denom_hists:
        hist_name = "{}{}".format(numer.basename,denom_hist.bin_suffix)
        try:
            numer_hist = numer_hist_map[hist_name] 
            eff_histname = "{basename}{tag}EffHist{bin_suffix}".format(basename=numer.basename,tag=tag,bin_suffix=numer_hist.bin_suffix)
            eff_hist = numer_hist.hist.Clone(eff_histname)
            eff_hist.Divide(numer_hist.hist,denom_hist.hist,1,1,"B")
            eff_hist.Draw()
            if hists_data!=None:
                hists_data.append({"name" : eff_histname,"cut_labels" :  numer_hist.cut_labels})
                
            if dir_:
                eff_hist.SetDirectory(dir_)
            out_hists.append(eff_hist)
        except KeyError:
            print("hist {} not found".format(hist_name))
            print(numer_hist_map)
    return out_hists
 


def make_effhists_fromcoll(numer,denom,tag="",dir_=None,out_hists=[],desc="",meta_data=None):
    colldata = HistCollData(desc=str(desc),is_normable=False,is_effhist=True)
    md_dict = dict(colldata.__dict__)
    md_dict['hists'] = {}
    for denom_hist in denom.hists:
        if denom_hist.use_for_eff:
            numer_hist = numer.get_hist(denom_hist.basename)
            md_dict['hists'][denom_hist.basename]=[]
            make_effhists_fromcoll_binned(numer_hist,denom_hist,tag,dir_,out_hists,md_dict['hists'][denom_hist.basename])
    if meta_data!=None:
        meta_data[tag]=md_dict
        

def get_from_canvas(c1,classname,verbose=0):
    if verbose>0:
        for obj in c1.GetListOfPrimitives():
            print(obj.ClassName())
    return [obj for obj in c1.GetListOfPrimitives() if obj.ClassName()==classname]

def get_from_file(in_file,classname="TH1D",starts_with=""):
    objs = {}
    for key in in_file.GetListOfKeys():
        obj = key.ReadObj()
        if obj.ClassName()==classname and obj.GetName().startswith(starts_with):
            objs[obj.GetName()]=obj
    return objs

def dump_graphic_coord(c1):
    for obj in c1.GetListOfPrimitives():
        if hasattr(obj,"GetX1NDC"):
            if hasattr(obj,"GetLabel"):
                print("{} : {} : {:.3f},{:.3f},{:.3f},{:.3f}".format(obj.ClassName(),obj.GetLabel(),obj.GetX1NDC(),obj.GetY1NDC(),obj.GetX2NDC(),obj.GetY2NDC()))
            else:
                print("{} : {:.3f},{:.3f},{:.3f},{:.3f}".format(obj.ClassName(),obj.GetX1NDC(),obj.GetY1NDC(),obj.GetX2NDC(),obj.GetY2NDC()))
     
