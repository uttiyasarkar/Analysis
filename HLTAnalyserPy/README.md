# HLTAnalyserPy

A set of tools to analyse the HLT EDM files in py fwlite

## Checkout instructions

```
#in your CMSSW src directory
git clone ssh://git@gitlab.cern.ch:7999/sharper/HLTAnalyserPy.git Analysis/HLTAnalyserPy
scram b -j 4
```

This does not depend on specific CMSSW version however the classes need to be availible if you register them even if you dont need them

This supports python2 and python3 but very soon it will become python3 now that the ROOT version in CMSSW_11_3 onwards plays nice with python3


## EvtData module

A package which eases the use retrieval of objects from the event


### EvtData 

The main class EvtData is designed as a single access point for retreiving objects from the event, it is expected that all objects are retrieved through this object

   * EvtData(products=[],verbose=False)
      * takes a list of products to setup handles 
      * product format is a dict with fields name, type and tag
         * name = name to retrieve the object with
         * type = c++ type, eg "std::vector<reco::EgTrigSumObj>"
	 * tag = input tag corresponding the the product
      * EvtData can be set to "lazy" and so does not retrieve any declared product till it is required so is costs nothing to over declare the products here
    * get_handles(event,on_demand=True)
      * gets the handles for the event, if on_demand=True, it instead waits for something to request the handle
      * necessary to call on each new event before retreiving the products
      * a better name would be initalise_handles()
    * get_handle(name):
      * gets the handle corresponding to the product with nane name
    * get(name):
      * gets the product with name name, returns None if the handle is invalid
 
### EvtWeight

This takes in a json of all the MC weights and returns the correct one for a given event.   

   * EvtWeights(input_filename,lumi)
      * reads in the weights from input_filename for a luminosity of lumi (in pb)
   * weight_from_evt(event)
      * returns the weight appriopriate for the event
      * note: it does this based of the file the event is read from so requires the filename is encoded in a certain way
      * note you need to pass in a fwlite::ChainEvent not the FWLite.Events class, therefore you might need to do a events.object() if you are using the Events class directly
   * weight_from_name(dataset_name)
      * returns the weight for  a given dataset with the specified name

### Misc Funcs

   * add_product(prods,name,type_,tag)
      * helper func to make add a product dict with keys name,type and tag to a list of product dicts named prods
   * get_objs(evtdata,events,objname,indx)
      * used interactively, simplifes getting an object from the event, basically saves typing events.to(index), evtdata.gethandles(events), evtdata.get(objname)
      * should not be used interactively as its inefficient and may have side effects if its used for multiple collections


## GenTools

This package allows us to gen match objects

  * get_genparts(genparts,pid=11,antipart=True,status=PartStatus.PREFSR)
     * returns a list of all gen particles matching the given criteria from the the hard process
     * genparts = the GenParticle collection
     * pid = pid of the particle
     * antipart if true, also allows the antiparticle
     * status: whether it is prefsr (PREFSR), post fsr (POSTFSR) or final version of the object (FINAL)
 
  * match_to_gen(eta,phi,genparts,pid=11,antipart=True,max_dr=0.1,status=PartStatus.PREFSR)
     * returns (GenParticle,dr) of the best match to the eta,phi passed in. If no match is found GenParticle is None
     * eta/phi = eta/phi to do the dr with
     * max_dr = maximum allowed dr to consider a match
     * pid = pid of the particle
     * antipart if true, also allows the antiparticle
     * status: whether it is prefsr (PREFSR), post fsr (POSTFSR) or final version of the object (FINAL)

## TrigTools

This module allows us access trigger information. 

To access whether a trigger passes or fails, you can use the TrigResults class. You can spass in a list of triggers you are interested in and then it'll track the indices they correspond to making it easier to see if a trigger passes or not. 

Note to deal with versions, it matches based on "startwith", ie it selects the triggers that start with the given string. Therefore if your trigger is "HLT_Ele32_WPTight_Gsf_v14" you can just pass in "HLT_Ele32_WPTight_Gsf_v" to match any version of that trigger or "HLT_Photon" to match any triggers that start with HLT_Photon (it will OR them together).

```python

trig_res = TrigTools.TrigResults(["HLT_Ele32_WPTight_Gsf_v","HLT_Photon"])
for eventnr,event in enumerate(events):
    #now fill the trigger results object, needs to be done every event
    trig_res.fill(evtdata)
    #see if a given trigger passes or fails, must be one of the triggers it was 
    #initialised with, if not an error will occur
    trig_res.result("HLT_Ele32_WPTight_Gsf_v")  
    
```

Then to access the trigger filter objects simply do 

```python 
for eventnr,event in enumerate(events):
    ele32_objs = TrigTools.get_objs_passing_filter_aod(evtdata,"hltEle32WPTightGsfTrackIsoFilter")
```
which will return all the trigger objects passing the hltEle32WPTightGsfTrackIsoFilter

     

## Scripts

The following scripts exist in the test directory

### runMultiThreaded.py

A useful script to parallelise other scripts. Pythons multithreading is a bit awful, listwise with roots. The simpliest solution is just to run N seperate versions of a script, splitting the input files amoungst the N jobs and then concatenate the output. This script will automatically do this for you and then optionally hadd the output 

It assumes the script its parallelising takes a list of input files as the first argument and "-o" as the output filename. 

if you have a script 
```python Analysis/HLTAnalyserPy/test/makePhaseIINtup.py /eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/Upgrade/EGM_PhaseII/mc/11_1_3/DoubleElectron_FlatPt-1To100__Phase2HLTTDRSummer20ReRECOMiniAOD-PU200_Oct11th/DoubleElectron_FlatPt-1To100__Phase2HLTTDRSummer20ReRECOMiniAOD-PU200_Oct11th_* -o doubleEleTest.root -w weights_Oct4th.json -r 5000```

to parallelise it you just need to do

```python Analysis/HLTAnalyserPy/test/runMultiThreaded.py -o doubleEleTest.root /eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/Upgrade/EGM_PhaseII/mc/11_1_3/DoubleElectron_FlatPt-1To100__Phase2HLTTDRSummer20ReRECOMiniAOD-PU200_Oct11th/DoubleElectron_FlatPt-1To100__Phase2HLTTDRSummer20ReRECOMiniAOD-PU200_Oct11th_* --cmd "python Analysis/HLTAnalyserPy/test/makePhaseIINtup.py  -w weights_Oct4th.json -r 5000" --hadd```

where we have moved the input and output filenames to arguments of the runMultiThreaded script and then put the command to execute as --cmd "<  >". We have set it to automatically hadd the output, remove "--hadd" to stop this


### makePhaseIINtup.py

This script reads in our HLT EDM format and converts it to a flat tree. This as been designed to be easy to collaborate between ourselfs to add new variables

The tree is constructed by EgHLTTree in Trees. The EgHLTTree class defines a series of core branches and how to fill them from the EvtData object. 

To aid collaboration, two extra functions have been defined `add_eg_vars` and `add_eg_update_funcs`. These functions will add you to add variables for a e/g hlt objects to the tree and also specific functions which may be needed to update the e/g hlt objects before filling the tree

To add new variables, you will need to define a function to make it which takes an EgTrigSumObj as the first argument (or is a method of EgTrigSumObj, to python these are effectively the same thing). 

It would be best to create a new file in HLTAnalyserPy/python with the function or collection of functions and import that function into makePhaseIINtup.py

#### Adding a New EG Variable

To add a variable simply pass as dictionary with the keys being the name of the variable with the [root type](https://root.cern.ch/doc/master/classTTree.html#addcolumnoffundamentaltypes) appended (eg "et/F") and the values being a function or other callable object which takes an EgTrigSumObj as its sole arugment to EgHLTTree.add_eg_vars(). This function can be called multiple times and will just add the variables, overriding existing variables of the same name

If the function to produce the variable requires additional arguements beyond the egobj, you can use CoreTools.UnaryFunc. This you can pass in either a string as you would type in python, including nesting functions such as superCluster().energy(). In this case the string has to be a method of the object the unary func is called with. You can also pass in functools.partial object where you can specify the addtional arguements and these can be either member functions or non member functions or in deed any callable object.
   
You can see examples of this in the EgHLTTree class defination where it fills the default variables. Its important to remember here that member variables in python act like a function which takes the object as the first argument, a fact we exploit here. 

#### Updating the EG objects

It might be useful to update the e/gamma objects before filling. This might be adding new variables to them, fixing existing variables, etc. This can be done by passing a function which takes an EgTrigSumObj as its only argument. As before functions which require additional arguments can be added using UnaryFunc taking a functools.partial object


## QCD Reweighting

### Introduction

This package also includes tools for QCD reweighting which is a port of Christian Veelken's [mcStiching](https://github.com/veelken/mcStitching). 

The key point to understand that there is no difference between a "QCD" event and a "pileup" or "MinBias" event, its the same pythia process. Typically we define the hard interaction as the highest pt interaction in the event but in the case of QCD/MB, the generated event may actually be lower pt hat than one of the pileup events added in. Thus naively reweighting according to the pt hat of the generated QCD event will not work as what we think is a pthat = 30 GeV event is really a pthat=40 GeV event. 

Therefore we reweight considering all pt hats in the event, the generated pt hat and the pu events pt hats. This method is done counting the entries in each pt hat bin of an event, comparing to that expected and reweighting accordingly. 

There is an additional complication for enriched entries. In this case, we do not consider pileup as generated event is the one enriched. We first calculate the weight appropriate for the generated events pt hat and the pt hat of the PU events as normal. Then we apply an additional weight to correct for the fact we have enriched samples. Specifically the weight is the number of total events in that category / the number events expected in that category not including the enriched samples. The categories are passing EM-only, passing MU-only or passingMU+EM. 

Note none of this applies to W+jets or DY samples which should be weighted as normal as they are a different generator process to the pileup.

### Usage

There are two classes to use, a python based on and a c++ one. The python is EvtData.QCDWeightCalc and there is a c++ implimenation QCDWeightCalc

Both load the necessary information by a common json format

#### Input Json

The code currently expects a json with a field "v2" which then contains a field "qcd" which defines the parameters for each bin. 

The parameters are
  * min_pt : minimum pt of the bin
  * max_pt : maximum pt of the bin
  * xsec : cross-section (in pb) of the sample
  * nr_em : number of events in the emenriched sample for this bin, set to zero if not running of emenriched
  * nr_mu : number of events in the muon enriched sample for this bin, set to zero if not running over muon enriched
  * nr_inclusive: number of events in the inclusive sample, set to zero if not running over an inclusive sample in this bin
  * em_filt_eff : the efficiency of the em enriching filter
  * em_mu_filter_eff : the fraction of em enriched events that are also muon enriched
  * mu_filt_eff : the efficiency of the muon enriching filter
  * mu_em_filter_eff : the fraction of muon enriched events that are also em enriched

Note, the minbias bin should be also included here. It should have a range of min_pt of 0 and max_pt of 9999. It is the only bin which is allowed to overlap with other bins, all the other pt bins must be exclusive to each other. In the future we may end up seperating out the minbias bin to its own category due to this bin being special. 

A script to generate this json is [makeWeightsJson.py](test/makeWeightsJson.py). The script can detect if its running on a DY, WJets, MB and QCD sample and assign the count accordingly. So just put as input all the files you wish to run over for the rates. It does not handle binned DY or WJets yet.

```
python test/makeWeightsJson.py <inputfiles> -o output_filename_with_weights.json"
```


#### c++ instructions

The QCDWeightCalc takes a parameter which is the filename of the input json containing the parameters for the weights and optionally the bunch frequency. 

QCDWeightCalc::weight() returns the QCD appropriate  weight. It takes the genPtHat of the event, the pu hats of the pileup events and two bools indicating whether it passed em enriching and passed mu enriching. 

The genPtHat can be got from GenEventInfoProduct which usually has the name "generator" via GenEventInfoProduct::qScale. 

The pu pt hats can be objected from std::vector<PileupSummaryInfo> named addPileupInfo (in the miniAOD slimmedAddPileupInfo or similar). You need to find the entry with getBunchCrossing()==0. Then the pt hats are simply genPU_put_hats()

Finally the weight just resulting from the enriching filter can be obtained from QCDWeightCalc::filtWeight()

#### python instructions

Simply pass the EvtData object into the EvtData.QCDWeightCalc.weight method. Currently this does not support muon enriching. 

#### example

An example is checkPUPtHat.py

  



