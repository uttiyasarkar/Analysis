#ifndef Analysis_HLTAnalyserPy_CutOptimiser_h
#define Analysis_HLTAnalyserPy_CutOptimiser_h

#include "Analysis/HLTAnalyserPy/FiltFuncs.h"

#include "ROOT/RDataFrame.hxx"
#include "ROOT/HistoModels.hxx"

#include <iostream>
class CutOptimiser{
private:
  ROOT::RDF::RNode sigDF_;
  ROOT::RDF::RNode bkgDF_;
  std::vector<std::string> cutVars_;
  std::string xVar_;
  std::string yVar_;
  ROOT::RDF::TH3DModel histCfg_;

  
  TH2* getCutValHist(TH3* hist,float targetEff):

}

#endif
