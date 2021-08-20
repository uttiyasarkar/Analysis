#ifndef ANALYSIS_HLTANALYSERPY_QCDWEIGHTCALC_H
#define ANALYSIS_HLTANALYSERPY_QCDWEIGHTCALC_H

#include <string>
#include <vector>   
#include <boost/property_tree/ptree.hpp>

// port of Christian Veelken's mcStiching
// https://github.com/veelken/mcStitching

//some improvement it might be better for the MinBias entry to be 
//explictly seperated out rather than having it as the entry with pt=0
//MB is rather special compared to the binned samples

class QCDWeightCalc {
public:
  struct PtBinnedSample {
    float minPt;
    float maxPt;
    float xsec;
    float nrIncl;
    float nrEm;
    float emFiltEff;
    float emMuFiltEff;
    float nrMu;
    float muFiltEff;
    float muEmFiltEff;
    float nrEmNoMuExpect;
    float nrEmNoMuActual;
    float nrMuNoEmExpect;
    float nrMuNoEmActual;
    float nrEmMuExpect;
    float nrEmMuActual;
  
    
    PtBinnedSample(const boost::property_tree::ptree& sampleInfo);
    void setEnrichedCounts(float nrMinBias,float minBiasXSec);
  };

  QCDWeightCalc(const std::string& inputFilename,float bxFreq=30E6);
  float weight(float genPtHat,const std::vector<float>& puPtHats,bool passEm,bool passMu)const;
  float filtWeight(float genPtHat,bool passEm,bool passMu)const;
  float operator()(float genPtHat,const std::vector<float>& puPtHats,bool passEm,bool passMu)const{
    return weight(genPtHat,puPtHats,passEm,passMu);
  }
private:
  size_t getBinNr(float ptHat)const;
  float bxFreq_;
  std::vector<PtBinnedSample> bins_;
  
};



#endif
