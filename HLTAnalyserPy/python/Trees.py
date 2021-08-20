import ROOT
import Analysis.HLTAnalyserPy.CoreTools as CoreTools
import Analysis.HLTAnalyserPy.TrigTools as TrigTools
import Analysis.HLTAnalyserPy.GenTools as GenTools
import Analysis.HLTAnalyserPy.L1Tools as L1Tools
from Analysis.HLTAnalyserPy.CoreTools import UnaryFunc
from Analysis.HLTAnalyserPy.NtupTools import TreeVar
from Analysis.HLTAnalyserPy.EvtWeights import EvtWeights

from functools import partial
import itertools
from array import array
import six

class EgHLTTree:
    def __init__(self,tree_name,evtdata,min_et=0.,weights=None):
        self.tree = ROOT.TTree(tree_name,'')
        self.l1seeded = True
        self.evtdata = evtdata
        self.min_et = min_et
        self.weights = weights
        self.initialised = False
        self.eg_extra_vars = {}
        self.eg_update_funcs = []

    def add_eg_vars(self,vars_):
        self.eg_extra_vars.update(vars_)

    def add_eg_update_funcs(self,update_funcs):
        self.eg_update_funcs.extend(update_funcs)

    def _init_tree(self):
        self.evtvars = [
            TreeVar(self.tree,"runnr/i",UnaryFunc("eventAuxiliary().run()")),
            TreeVar(self.tree,"lumiSec/i",UnaryFunc("eventAuxiliary().luminosityBlock()")),
            TreeVar(self.tree,"eventnr/i",UnaryFunc("eventAuxiliary().event()")),
        
        ]
        self.evtdatavars = []
        if self.weights:
            self.evtdatavars.append(TreeVar(self.tree,"weight/F",self.weights.weight)),
            self.evtdatavars.append(TreeVar(self.tree,"filtweight/F",self.weights.filtweight))
        self.evtdatavars.append(TreeVar(self.tree,"genPtHat/F",UnaryFunc('get("geninfo").qScale()')))
        self.evtdatavars.append(TreeVar(self.tree,"nrHitsEB1GeV/F",UnaryFunc('get_fundtype("nrHitsEB1GeV")')))
        self.evtdatavars.append(TreeVar(self.tree,"nrHitsHGCalEE1GeV/F",UnaryFunc('get_fundtype("nrHGCalEE1GeV")')))
        self.evtdatavars.append(TreeVar(self.tree,"nrHitsHGCalHEB1GeV/F",UnaryFunc('get_fundtype("nrHGCalHEB1GeV")')))
        self.evtdatavars.append(TreeVar(self.tree,"nrHitsHGCalHEF1GeV/F",UnaryFunc('get_fundtype("nrHGCalHEF1GeV")')))
        self.evtdatavars.append(TreeVar(self.tree,"rho/F",UnaryFunc('get_fundtype("rho",0)')))
            
            
        max_pthats = 400
        self.nr_pthats = TreeVar(self.tree,"nrPtHats/i",UnaryFunc(partial(len)))
        self.pthats = TreeVar(self.tree,"ptHats/F",None,maxsize=max_pthats,sizevar="nrPtHats")
            
        egobjnr_name = "nrEgs"
        max_egs = 200    
        self.egobj_nr = TreeVar(self.tree,egobjnr_name+"/i",UnaryFunc(partial(len)))
       
        prod_tag = "L1Seeded" if self.l1seeded else "Unseeded" 

        vars_ = {
            'et/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.et)),
            'energy/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.energy)),
            'rawEnergy/F' : UnaryFunc("superCluster().rawEnergy()"),
            'eta/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.eta)),
            'phi/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.phi)),
            'phiWidth/F':UnaryFunc("superCluster().phiWidth()"),
            'nrClus/I':UnaryFunc("superCluster().clusters().size()"),
            'seedId/i':UnaryFunc("superCluster().seed().seed().rawId()"),
            'seedDet/I':UnaryFunc("superCluster().seed().seed().det()"),
            'sigmaIEtaIEta/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,"hltEgammaClusterShape{}_sigmaIEtaIEta5x5".format(prod_tag),0)),
            'ecalPFIsol_default/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,"hltEgammaEcalPFClusterIso{}".format(prod_tag),0)),
            'hcalPFIsol_default/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,"hltEgammaHcalPFClusterIso{}".format(prod_tag),0)),
            'hgcalPFIsol_default/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,"hltEgammaHGCalPFClusterIso{}".format(prod_tag),0)),
            'trkIsolV0/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,"hltEgammaEleGsfTrackIso{}".format(prod_tag),0)),
            'trkIsolV6_default/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,"hltEgammaEleGsfTrackIsoV6{}".format(prod_tag),0)),
            'trkIsolV72_default/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,"hltEgammaEleGsfTrackIsoV72{}".format(prod_tag),0)),
            'trkChi2_default/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,"hltEgammaGsfTrackVars{}_Chi2".format(prod_tag),0)),
            'trkMissHits/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,"hltEgammaGsfTrackVars{}_MissingHits".format(prod_tag),0)),
            'trkValidHits/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,"hltEgammaGsfTrackVars{}_ValidHits".format(prod_tag),0)),
            'invESeedInvP/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,"hltEgammaGsfTrackVars{}_OneOESeedMinusOneOP".format(prod_tag),0)),
            'invEInvP/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,"hltEgammaGsfTrackVars{}_OneOESuperMinusOneOP".format(prod_tag),0)),
            'trkDEta/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,"hltEgammaGsfTrackVars{}_Deta".format(prod_tag),0)),
            'trkDEtaSeed/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,"hltEgammaGsfTrackVars{}_DetaSeed".format(prod_tag),0)),
            'trkDPhi/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,"hltEgammaGsfTrackVars{}_Dphi".format(prod_tag),0)), 
            'trkNrLayerIT/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaGsfTrackVars{}_NLayerIT'.format(prod_tag),0)),
            'rVar/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaHGCALIDVars{}_rVar'.format(prod_tag),0)),
            'sigma2uu/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaHGCALIDVars{}_sigma2uu'.format(prod_tag),0)),
            'sigma2vv/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaHGCALIDVars{}_sigma2vv'.format(prod_tag),0)),
            'sigma2ww/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaHGCALIDVars{}_sigma2ww'.format(prod_tag),0)),
            'sigma2xx/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaHGCALIDVars{}_sigma2xx'.format(prod_tag),0)),
            'sigma2xy/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaHGCALIDVars{}_sigma2xy'.format(prod_tag),0)),
            'sigma2yy/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaHGCALIDVars{}_sigma2yy'.format(prod_tag),0)),
            'sigma2yz/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaHGCALIDVars{}_sigma2yz'.format(prod_tag),0)),
            'sigma2zx/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaHGCALIDVars{}_sigma2zx'.format(prod_tag),0)),
            'sigma2zz/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaHGCALIDVars{}_sigma2zz'.format(prod_tag),0)),
            'pms2_default/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaPixelMatchVars{}_s2'.format(prod_tag),0)),
            'hgcalHForHoverE/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaHGCALIDVars{}_hForHOverE'.format(prod_tag),0)),
            'hcalHForHoverE/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaHoverE{}'.format(prod_tag),0)), 
            'l1TrkIsoCMSSW/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaEleL1TrkIso{}'.format(prod_tag),0)),
            
            'bestTrkChi2/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaBestGsfTrackVars{}_Chi2'.format(prod_tag),0)),
            'bestTrkDEta/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaBestGsfTrackVars{}_Deta'.format(prod_tag),0)),
            'bestTrkDEtaSeed/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaBestGsfTrackVars{}_DetaSeed'.format(prod_tag),0)),
            'bestTrkDPhi/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaBestGsfTrackVars{}_Dphi'.format(prod_tag),0)),
            'bestTrkMissHits/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaBestGsfTrackVars{}_MissingHits'.format(prod_tag),0)),
            'bestTrkNrLayerIT/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaBestGsfTrackVars{}_NLayerIT'.format(prod_tag),0)),
            'bestTrkESeedInvP/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaBestGsfTrackVars{}_OneOESeedMinusOneOP'.format(prod_tag),0)),
            'bestTrkInvEInvP/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaBestGsfTrackVars{}_OneOESuperMinusOneOP'.format(prod_tag),0)),
            'bestTrkValitHits/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaBestGsfTrackVars{}_ValidHits'.format(prod_tag),0)),         
            'hgcaliso_layerclus/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaHGCalLayerClusterIso{}'.format(prod_tag),0)),
            'hgcaliso_layerclusem/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaHGCalLayerClusterIso{}_em'.format(prod_tag),0)),
            'hgcaliso_layerclushad/F' : UnaryFunc(partial(ROOT.trigger.EgammaObject.var,'hltEgammaHGCalLayerClusterIso{}_had'.format(prod_tag),0)),

           
        }
        vars_.update(self.eg_extra_vars)

        self.egobj_vars = []        
        for name,func in six.iteritems(vars_):
            self.egobj_vars.append(TreeVar(self.tree,"eg_"+name,func,max_egs,egobjnr_name))
            
        gen_vars_names = {
            'energy/F' : UnaryFunc(partial(ROOT.reco.GenParticle.energy)),
            'pt/F' : UnaryFunc(partial(ROOT.reco.GenParticle.pt)),
            'et/F' : UnaryFunc(partial(ROOT.reco.GenParticle.et)),
            'eta/F' : UnaryFunc(partial(ROOT.reco.GenParticle.eta)),
            'phi/F' : UnaryFunc(partial(ROOT.reco.GenParticle.phi)),
            'vz/F' : UnaryFunc(partial(ROOT.reco.GenParticle.vz)),
        }
        self.gen_vars = []
        for name,func in six.iteritems(gen_vars_names):
            self.gen_vars.append(TreeVar(self.tree,"eg_gen_"+name,func,max_egs,egobjnr_name))
        
        scales_params = L1Tools.make_egscale_dict()
        l1pho_vars_names = {
            'et/F' : UnaryFunc("et()"),
            'eta/F' : UnaryFunc("eta()"),
            'phi/F' : UnaryFunc("phi()"),
            'hwQual/F' : UnaryFunc("EGRef().hwQual()"),
            'trkIsol/F' : UnaryFunc('trkIsol()'),
            'trkIsolPV/F' : UnaryFunc('trkIsolPV()'),
            'passQual/b' : L1Tools.pass_eg_qual,
            'passIsol/b' : L1Tools.pass_eg_isol,
            
            'etThresIso/F' : UnaryFunc(partial(L1Tools.eg_thres,scales_params,use_iso=True)),
            'etThresNonIso/F' : UnaryFunc(partial(L1Tools.eg_thres,scales_params,use_noniso=True)),
            'etThres/F' : UnaryFunc(partial(L1Tools.eg_thres,scales_params))            
            }
        self.l1pho_vars = []
        for name,func in six.iteritems(l1pho_vars_names):
            self.l1pho_vars.append(TreeVar(self.tree,"eg_l1pho_"+name,func,max_egs,egobjnr_name))   
        l1ele_vars_names = dict(l1pho_vars_names)
        l1ele_vars_names.update({
            'vz/F' : UnaryFunc('trkzVtx()'),
            'trkCurve/F' : UnaryFunc('trackCurvature()')        
        })
        self.l1ele_vars = []
        for name,func in six.iteritems(l1ele_vars_names):
            self.l1ele_vars.append(TreeVar(self.tree,"eg_l1ele_"+name,func,max_egs,egobjnr_name))   


        trig_names = ["Gen_QCDMuGenFilter",
                      "Gen_QCDBCToEFilter",
                      "Gen_QCDEmEnrichingFilter",
                      "Gen_QCDEmEnrichingNoBCToEFilter"]
        self.trig_res = TrigTools.TrigResults(trig_names)
        self.trig_vars = []
        for name in trig_names:
            self.trig_vars.append(TreeVar(self.tree,"path_{}/b".format(name),
                                          UnaryFunc(partial(TrigTools.TrigResults.result,name))))


        self.initialised = True

    def fill(self):
        if not self.initialised:
            self._init_tree()

        for var_ in self.evtvars:
            var_.fill(self.evtdata.event.object())
        for var_ in self.evtdatavars:
            var_.fill(self.evtdata)

        pusum_intime = [x for x in self.evtdata.get("pu_sum") if x.getBunchCrossing()==0]
        pt_hats = [x for x in pusum_intime[0].getPU_pT_hats()]
        pt_hats.append(self.evtdata.get("geninfo").qScale())
        pt_hats.sort(reverse=True)
        self.nr_pthats.fill(pt_hats)
        for pt_hat_nr,pt_hat in enumerate(pt_hats):
            self.pthats.fill(pt_hat,pt_hat_nr)
            
        egobjs_raw = self.evtdata.get("egtrigobjs_l1seed") if self.l1seeded else self.evtdata.get("egtrigobjs") 
        egobjs = [eg for eg in egobjs_raw if eg.et()>self.min_et]
        egobjs.sort(key=ROOT.trigger.EgammaObject.et,reverse=True)
        for obj in egobjs:
            for update_func in self.eg_update_funcs:
                update_func(obj)

        genparts = self.evtdata.get("genparts")
        l1phos_eb  = self.evtdata.get("l1tkphos_eb")
        l1phos_hgcal = self.evtdata.get("l1tkphos_hgcal") 
        l1phos = [eg for eg in itertools.chain(l1phos_eb,l1phos_hgcal)]
        l1eles_eb  = self.evtdata.get("l1tkeles_eb")
        l1eles_hgcal = self.evtdata.get("l1tkeles_hgcal") 
        l1eles = [eg for eg in itertools.chain(l1eles_eb,l1eles_hgcal)]
        self.egobj_nr.fill(egobjs)
        for var_ in itertools.chain(self.gen_vars,self.l1pho_vars,self.l1ele_vars):
            var_.clear()
        
        gen_eles = GenTools.get_genparts(self.evtdata.get("genparts"),
                                         pid=11,antipart=True,
                                         status=GenTools.PartStatus.PREFSR)
       
        good_l1phos = [obj for obj in l1phos if L1Tools.pass_eg_qual(obj) ]

        for objnr,obj in enumerate(egobjs):
            for var_ in self.egobj_vars:                
                var_.fill(obj,objnr)

            gen_obj = CoreTools.get_best_dr_match(obj,gen_eles,0.1)
            if gen_obj:
                for var_ in self.gen_vars:
                    var_.fill(gen_obj,objnr)

            l1pho_obj = CoreTools.get_best_dr_match(obj,good_l1phos,0.2)
            l1ele_obj = L1Tools.get_l1ele_from_l1pho(l1pho_obj,l1eles) if l1pho_obj else None
            if l1pho_obj:
                for var_ in self.l1pho_vars:
                    var_.fill(l1pho_obj,objnr)
            if l1ele_obj:
                for var_ in self.l1ele_vars:
                    var_.fill(l1ele_obj,objnr)
                    

        self.trig_res.fill(self.evtdata)
        for var_ in self.trig_vars:
            var_.fill(self.trig_res)

        self.tree.Fill()


class HLTRateTree:
    def __init__(self,tree_name,weights_file,trig_res_name):
        self.tree = ROOT.TTree(tree_name,"")
        self.initialised = False
        self.gen_filters = TrigTools.TrigResults(["Gen_QCDMuGenFilter",
                                                  "Gen_QCDEmEnrichingNoBCToEFilter"])
        self.trig_res_name = trig_res_name
        self.weight_calc = EvtWeights(weights_file)

    def init_tree(self,trig_names):
        if self.initialised:
            return 

        self.hard_pt_hat = array("f",[0])
        self.nr_pt_hats = array("i",[0])
        self.pt_hats = ROOT.std.vector("float")()
        self.nr_expect_pu = array("f",[0])
        self.weight = array("f",[0])
        self.filtweight = array("f",[0])
        self.pass_em = array("i",[0])
        self.pass_mu = array("i",[0])
        self.mc_type = array("i",[0])
        self.filt_type = array("i",[0])
        
        self.tree.Branch("hardPtHat",self.hard_pt_hat,"hardPtHat/F")
        self.tree.Branch("nrPtHats",self.nr_pt_hats,"nrPtHats/I")
        self.tree.Branch("ptHats",self.pt_hats)
        self.tree.Branch("nrExptPU",self.nr_expect_pu,"nrExptPU/F")
        self.tree.Branch("weight",self.weight,"weight/F")
        self.tree.Branch("filtWeight",self.filtweight,"filtWeight/F")
        self.tree.Branch("passEM",self.pass_em,"passEM/I")
        self.tree.Branch("passMU",self.pass_mu,"passMU/I")
        self.tree.Branch("mcType",self.mc_type,"mcType/I")
        self.tree.Branch("filtType",self.filt_type,"filtType/I")

       
        self.trig_res = [array("B",[0]) for x in range(0,trig_names.size())]
        for trig_nr,trig_name in enumerate(trig_names):
            trig_name = TrigTools.sep_trig_ver(trig_name)[0]
            self.tree.Branch(trig_name,self.trig_res[trig_nr],trig_name+"/b")
            
        self.initialised = True

    def fill(self,evtdata): 
        trig_res = evtdata.get(self.trig_res_name) 
        if not self.initialised: 
            self.init_tree(evtdata.event.object().triggerNames(trig_res).triggerNames())
       
        geninfo = evtdata.get("geninfo")
        pu_sum  = evtdata.get("pu_sum")
        pu_sum_intime = [x for x in evtdata.get("pu_sum") if x.getBunchCrossing()==0]
        pt_hats = [x for x in pu_sum_intime[0].getPU_pT_hats()]
        pt_hats.append(geninfo.qScale())
        pt_hats.sort(reverse=True)
        self.nr_expect_pu[0] = pu_sum_intime[0].getTrueNumInteractions()
        self.gen_filters.fill(evtdata)

        self.hard_pt_hat[0] = geninfo.qScale()
        self.pt_hats.clear()
        for pt_hat in pt_hats:
            self.pt_hats.push_back(pt_hat)
        self.nr_pt_hats[0] = self.pt_hats.size()
        self.weight[0] = self.weight_calc.weight(evtdata,nr_expt_pu=pu_sum_intime[0].getTrueNumInteractions())
        self.filtweight[0] = self.weight_calc.filtweight(evtdata)
        self.pass_em[0] = self.gen_filters.result("Gen_QCDEmEnrichingNoBCToEFilter")
        self.pass_mu[0] = self.gen_filters.result("Gen_QCDMuGenFilter")
        self.mc_type[0] = self.weight_calc.mcsample_getter.get().proc_type
        self.filt_type[0] = self.weight_calc.mcsample_getter.get().filt_type
           
        #for whatever reason an enumerate was not working
        for trig_nr in range(0,trig_res.size()):
            self.trig_res[trig_nr][0] = trig_res[trig_nr].accept()
        
        self.tree.Fill()
