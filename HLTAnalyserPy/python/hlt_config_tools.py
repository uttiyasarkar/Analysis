
import FWCore.ParameterSet.Config as cms

import json
import subprocess
import os
import six

def enableESConditionsDump(process):
    process.escontent = cms.EDAnalyzer( "PrintEventSetupContent",
                                        compact = cms.untracked.bool( True ),
                                        printProviders = cms.untracked.bool( True )
                                    )

    process.esretrieval = cms.EDAnalyzer( "PrintEventSetupDataRetrieval",
                                          printProviders = cms.untracked.bool( True )
    )
    process.esout = cms.EndPath(process.escontent + process.esretrieval)
    return process

def customiseMessageLogger(process,reportEvery=100):
    if not hasattr(process,'MessageLogger'):
        process.load("FWCore.MessageLogger.MessageLogger_cfi")
    
    process.MessageLogger.cerr.FwkReport = cms.untracked.PSet(
        reportEvery = cms.untracked.int32(reportEvery),
        limit = cms.untracked.int32(10000000)
    )
    if not hasattr(process.MessageLogger,'suppressWarning'):
        process.MessageLogger.suppressWarning = cms.untracked.vstring()
    if not hasattr(process.MessageLogger,'suppressError'):
        process.MessageLogger.suppressError = cms.untracked.vstring()

    process.MessageLogger.suppressWarning.append('hltSiPixelRecHits')
    process.MessageLogger.suppressError.append('hltSiPixelRecHits')
    process.MessageLogger.suppressWarning.append('siPixelRecHits')
    process.MessageLogger.suppressError.append('siPixelRecHits')


def addInputFilesFromFilelist(process,filelist,verbose=True):
    with open(filelist) as f:
        for line in f:
            line = line.partition('#')[0]
            line = line.rstrip()
            if verbose: print "adding file: {}".format(line)
            process.source.fileNames.append(line)


def addInputFilesFromDAS(process,dataset,verbose=True):
    dascmd = ['dasgoclient','--query','file dataset={}'.format(dataset),'--json'] 
    result,error = process.Popen(dascmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
    if error: 
        raise Exception("das query error:\n{}".format(error))
    if result=="[\n]\n":
        raise Exception("das query error: no results found for dataset {}".format(dataset))
    for result in query_results:
        for file_ in result['file']:
            if verbose: print "adding file: {}".format(file_['name'])
            process.source.fileNames.append(file_['name'])
            

def setInputFiles(process,inputFiles,verbose=True):
    process.source.fileNames = cms.untracked.vstring()

    nr_files = len(inputFiles)
    if len(inputFiles)==1 and inputFiles[0].split(".")[-1]!="root":
        if os.path.isfile(inputFiles[0]):
            addInputFilesFromFilelist(process,inputFiles[0],verbose)
        else:
            addInputFilesFromDAS(process,dataset,verbose=True)
            
    else:
        process.source.fileNames = inputFiles



def rmOutputMods(process):
    for endPath in process.endpaths_().keys():
        for modName in process.outputModules_().keys():
            outMod = getattr(process,modName)
            getattr(process,endPath).remove(outMod)



def rmAllEndPathsWithOutput(process):

    outputModuleNames=process.outputModules_().keys()
    for endPathName in process.endpaths_().keys():
        if len(endPathName)-endPathName.find("Output")==6 and len(endPathName)>=6:
            print "removing endpath ",endPathName
            delattr(process,endPathName)

            
        else:
            endPath = getattr(process,endPathName)
            pathModuleNames = endPath.moduleNames()
            for outModName in outputModuleNames:
                if outModName in pathModuleNames: 
                    print "removing endpath ",endPathName
                    delattr(process.endPathName)
                    break

def rmPath(process,pathName):
     print "removing path ",pathName   
     delattr(process,pathName)     
     try:
         for psSet in process.PrescaleService.prescaleTable:
             if psSet.pathName.value()==pathName:
                 process.PrescaleService.prescaleTable.remove(psSet)
     except:
         pass

def rmPathPattern(process,pathPattern):
    for pathName in process.pathNames().split():
        if pathName.find(pathPattern)!=-1:
            rmPath(process,pathName)

               
def rmAllPathsExcept(process,pathsToKeep):
    for pathName in process.pathNames().split():
        if (pathName.find("HLT_")==0 or pathName.find("MC_")==0 or pathName.find("AlCa_")==0 or pathName.find("DST_")==0) and pathName not in pathsToKeep:
            rmPath(process,pathName)
            

def rmL1Seeds(process,l1SeedsToRM):
           
    for filterName in process.filterNames().split():
        filt=getattr(process,filterName)
        if filt.type_()=="HLTL1TSeed":           
            l1SeedsInExp=filt.L1SeedsLogicalExpression.value().split(" OR ")
            for l1SeedToRM in l1SeedsToRM:
                for l1SeedInExp in l1SeedsInExp:
                    if l1SeedInExp==l1SeedToRM: l1SeedsInExp.remove(l1SeedInExp)
            

            l1SeedStr=""
            for l1SeedInExp in l1SeedsInExp[:-1]:
                l1SeedStr+=l1SeedInExp+" OR "
            try:
                l1SeedStr+=l1SeedsInExp[-1]
            except:
                l1SeedStr+="L1_ZeroBias"
            filt.L1SeedsLogicalExpression=l1SeedStr    
        


def addOutputMod(process,outname="output.root",eventContent=None):
    
    process.hltOutputTot = cms.OutputModule( "PoolOutputModule",
                                             fileName = cms.untracked.string( outname ),
                                             fastCloning = cms.untracked.bool( False ),
                                             dataset = cms.untracked.PSet(
                                                 filterName = cms.untracked.string( "" ),
                                                 dataTier = cms.untracked.string( "RAW" )
                                             ),
                                             SelectEvents = cms.untracked.PSet(),
                                             outputCommands = cms.untracked.vstring( 
                                                 'drop *',
                                                 #   'keep *',
                                                'keep *_hltGtStage2ObjectMap_*_*',
                                                 #     'keep FEDRawDataCollection_rawDataCollector_*_*',
                                                #     'keep FEDRawDataCollection_source_*_*',
                                                 'keep edmTriggerResults_*_*_*',
                                                 'keep triggerTriggerEvent_*_*_*',
                                                 'keep recoRecoEcalCandidates*_*_*_*',
                                                 'keep recoSuperClusters_*_*_*',
                                                 'keep recoCaloClusters_*_*_*',
                                                 'keep *_genParticles_*_*',
                                                 'keep *_addPileupInfo_*_*',
                                                 'keep *_externalLHEProducer_*_*',
                                                 'keep *_generator_*_*',
                                                 'keep *_hltEgammaGsfTracks*_*_*',
                                                 'keep recoElectronSeeds_*_*_*',
                                                 'keep *_nrEventsStorer*_*_*')
                                             
    )
    if eventContent:
        process.hltOutputTot.outputCommands = eventContent
    process.HLTOutput = cms.EndPath(process.hltOutputTot)
    try:
        process.HLTSchedule.insert(len(process.HLTSchedule),process.HLTOutput)
    except AttributeError:
        pass




def outputCmdsEgExtra():
    res = cms.untracked.vstring("drop *",
                                "keep *_hltParticleFlowSuperClusterECALL1Seeded_*_*",
                                "keep *_hltParticleFlowClusterECALL1Seeded_*_*",
                                "keep *_hltParticleFlowClusterPSL1Seeded_*_*",
                                "keep *_hltEgammaElectronPixelSeed_*_*",
                                "keep *_hltEgammaGsfTracks_*_*",
                                "keep *_hltEgammaHLTExtraL1Seeded_*_*",
                                "keep *_hltParticleFlowSuperClusterECALUnseeded_*_*",
                                "keep *_hltParticleFlowClusterECALUnseeded_*_*",
                                "keep *_hltParticleFlowClusterPSUnseeded_*_*",
                                "keep *_hltEgammaElectronPixelSeedsUnseeded_*_*",
                                "keep *_hltEgammaGsfTracksUnseeded_*_*",
                                "keep *_hltEgammaHLTExtraUnseeded_*_*",
                                "keep *_genParticles_*_*", 
                                "keep *_addPileupInfo_*_*",
                                "keep *_generator_*_*",
                                "keep *_externalLHEProducer_*_*",
                                'keep *_hltTriggerSummaryAOD_*_*',
                                'keep *_TriggerResults_*_*',
                                'keep *_hltGtStage2Digis_*_*',
                                "keep *_hltGtStage2ObjectMap_*_*",
                                "keep *_hltScalersRawToDigi_*_*",
    )
    return res

def addEgHLTExtraOutMod(process,outname="output.root"):
    process.load("RecoEgamma.EgammaHLTProducers.hltEgammaHLTExtraL1Seeded_cfi")
    process.load("RecoEgamma.EgammaHLTProducers.hltEgammaHLTExtraUnseeded_cfi")
    process.egHLTExtraOutMod = cms.OutputModule( "PoolOutputModule",
                                                 fileName = cms.untracked.string( outname ),
                                                 fastCloning = cms.untracked.bool( False ),
                                                 dataset = cms.untracked.PSet(
                                                     filterName = cms.untracked.string( "" ),
                                                     dataTier = cms.untracked.string( "RAW" )
                                                 ),
                                                 SelectEvents = cms.untracked.PSet(),
                                                 outputCommands = outputCmdsEgExtra(),
                                            )

    process.egHLTExtraOut = cms.EndPath(process.hltEgammaHLTExtraL1Seeded*process.hltEgammaHLTExtraUnseeded*process.egHLTExtraOutMod)
    try:
        process.HLTSchedule.append(process.egHLTExtraOut)
    except AttributeError:
        pass


def convert_to_hltname(input_str):
    try:
        return "hlt{}{}".format(input_str[0].upper(),input_str[1:])
    except IndexError:
        return input_str

def rename_mod_inputs(pset,oldmod,newmod):
    names = pset.parameterNames_()
    for para_name in names:
        if hasattr(pset,para_name):
            para = getattr(pset,para_name)
            para_type = para.pythonTypeName()
            if para_type == "cms.InputTag":
                if para.getModuleLabel() == oldmod:
                    para.setModuleLabel(newmod)
            if para_type == "cms.VInputTag":
                for tag in para:
                    if type(tag)==cms.InputTag:
                        if tag.getModuleLabel() == oldmod:
                            tag.setModuleLabel(newmod)
                    else:
                        modlabel = tag.split(":")[0]
                        if modlabel == oldmod:
                            tag.replace(modlabel+":",newmod+":")
            if para_type == "cms.PSet":
                rename_mod_inputs(para,oldmod,newmod)
            if para_type == "cms.VPSet":
                #oddly iterating over it normally
                #wipes out parameters after untracked paras
                for index in range(0,len(para)):
                    rename_mod_inputs(para[index],oldmod,newmod)
        
def rename_mod_inputs_old(pset,oldmod,newmod):
    for paraname,para in six.iteritems(pset.parameters_()):
        para_type = para.pythonTypeName()          
        if para_type == "cms.PSet":
            print "PSet"
            rename_mod_inputs(para,oldmod,newmod)
        if para_type == "cms.VPSet":
            print "VPSet"
            for pset in para:                
                rename_mod_inputs(pset,oldmod,newmod)
        if para_type == "cms.InputTag":
            if para.getModuleLabel() == oldmod:
                para.setModuleLabel(newmod)
        elif para_type == "cms.VInputTag":
            for tag in para:
                if type(tag)==cms.InputTag:
                    if tag.getModuleLabel() == oldmod:
                        tag.setModuleLabel(newmod)
                else:
                    modlabel = tag.split(":")[0]
                    if modlabel == oldmod:
                        tag.replace(modlabel+":",newmod+":")

                        
def rename_mod_inputs_allprod(process,oldmod,newmod):
    for prodname in process.producerNames().split():
        prod = getattr(process,prodname)
        print "begin ",prodname
        rename_mod_inputs(prod,oldmod,newmod)
        print "end",prodname

def rename_module(process,name,new_name):
    mod = getattr(process,name)
    setattr(process,new_name,mod.clone())
    new_mod = getattr(process,new_name)
    for taskname,task in six.iteritems(process.tasks):
        task.replace(mod,new_mod)
    for seqname,seq in six.iteritems(process.sequences):
        seq.replace(mod,new_mod)
    for pathname,path in six.iteritem(process.paths):
        path.replace(mod,new_mod)
    for pathname,path in six.iteritems(process.endpaths):
        path.replace(mod,new_mod)
    rename_mod_inputs_allprod(process,name,new_name)
    delattr(process,name)
