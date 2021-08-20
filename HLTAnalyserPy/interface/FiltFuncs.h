#ifndef Analysis_HLTAnalyserPy_FiltFuncs_h
#define Analysis_HLTAnalyserPy_FiltFuncs_h

#include <boost/algorithm/string/replace.hpp>

#include "ROOT/RDataFrame.hxx"
#include "ROOT/RResultPtr.hxx"
#include "TH1D.h"

#include <iostream>

class FiltFuncs {
public:
  ROOT::RDF::RNode addHistFilter(ROOT::RDF::RNode df,const std::string& cut,const std::string& cutname){
    df = df.Define(cutname,cut);
    return df;
  }
  ROOT::RDF::RNode addCut(ROOT::RDF::RNode df,const std::string& cut,const std::string& cutname,int nrobjs){
    df = df.Define(cutname,cut);
    //    df = df.Filter();
    return df;
  }

  class CutFlow {
  public:
    class Cut {
    private:
      std::string name_;
      std::string expres_;
    public:
      Cut(std::string name="",std::string expres=""):
	name_(std::move(name)),
	expres_(std::move(expres)){}
      
      std::string expres(const std::string& qualifier="")const{
	std::string expresMod(expres_);
	boost::algorithm::replace_all(expresMod,"{}",qualifier);
	return expresMod;
      }
      const std::string& name()const{return name_;}
      const std::string& expres_raw()const{return expres_;}
      
    };
    class HistCfg {
    private:
      std::string name_;
      std::string title_;
      int nrBins_;
      float xmin_;
      float xmax_;
      std::string var_;
    public:
      HistCfg(std::string name,std::string title,int nrBins,float xmin,float xmax,std::string var):
	name_(std::move(name)),title_(std::move(title)),
	nrBins_(nrBins),xmin_(xmin),xmax_(xmax),
	var_(std::move(var))
      {}
      
      std::string var(const std::string& qualifier)const{
	std::string varMod(var_);
	boost::algorithm::replace_all(varMod,"{}",qualifier);
	return varMod;
      }
      ROOT::RDF::TH1DModel histModel(const std::string& collname)const{
	return ROOT::RDF::TH1DModel((collname+name_).c_str(),title_.c_str(),nrBins_,xmin_,xmax_);
      }
      
    };
    class CutHistColl{
      std::string cutName_;
      std::string cutStr_;
      using StrHistPair = std::pair<std::string,ROOT::RDF::RResultPtr<TH1D> >; 
      std::vector<StrHistPair> hists_;
    public:
      
      CutHistColl(std::string cutName="",std::string cutStr=""):
	cutName_(std::move(cutName)),cutStr_(std::move(cutStr)){}

      void add(std::string var,ROOT::RDF::RResultPtr<TH1D> hist){
	hists_.emplace_back(StrHistPair(std::move(var),std::move(hist)));
      }
      const std::string& cutName()const{return cutName_;}
      const std::string& cutStr()const{return cutStr_;}
      const std::vector<StrHistPair>& hists()const{return hists_;}
      

    };
  private:
    std::vector<HistCfg> histCfgs_;
    using HistSubColl = std::unordered_map<std::string,ROOT::RDF::RResultPtr<TH1D> >;
    using HistColl = std::unordered_map<std::string,HistSubColl>;
  
    std::vector<Cut> cuts_;
    std::vector<Cut> defines_;
    std::string name_;
    std::string prefix_;
    int nrObj_;
    

  public:
    CutFlow(std::string name,int nrObj):name_(std::move(name)),
					prefix_(name_.empty() ? "" : name_+"_"),
					nrObj_(nrObj){}
      
    void addHist1D(const std::string& name,const std::string& var){
      
    }
    void addHist1D(const std::string& name,const std::string& title,
    		   int bins,float xmin,float xmax,const std::string& var){
      histCfgs_.push_back({name,title,bins,xmin,xmax,var});
    }
    

    void addCut(const Cut& cut){
      addCut(prefix_+cut.name(),cut.expres_raw());
    }
    void addCut(std::string name,std::string expres){
      cuts_.emplace_back(Cut(prefix_+name,expres));
    }
    void addDef(std::string name,std::string expres){
      defines_.emplace_back(Cut(prefix_+name,expres));
    }

    ROOT::RDF::RNode define(ROOT::RDF::RNode df){
      for(const auto& def : defines_){
	df = df.Define(def.name(),def.expres(""));
      }

      std::string suffix = "";
      std::string prev_cut = "";
      for(const auto& cut : cuts_){
	std::string cut_str = cut.expres("");
	if(!prev_cut.empty()) cut_str = prev_cut+" && "+cut_str;
	std::cout <<"cut "<<cut.name()<<" "<<cut_str<<std::endl; 
	df = df.Define(cut.name(),cut_str);
	//df = df.Filter("Sum("+cut.name()+")>="+std::to_string(nrObj_),cut.name());
	suffix = "["+cut.name()+"]";
	//if(!cut_str.empty()) cut_str += " && ";			      
	prev_cut = cut.name();
      }
      return df;
    }
    ROOT::RDF::RNode filter(ROOT::RDF::RNode df){        
      for(const auto& cut : cuts_){
	df = df.Filter("Sum("+cut.name()+")>="+std::to_string(nrObj_),cut.name());
      }
      return df;
    }

    HistColl histsOld(ROOT::RDF::RNode df){
      HistColl hists;     
      for(const auto& cut : cuts_){
	auto cutHists =  hists.insert({cut.name(),HistSubColl()}).first;
	for(const auto& cfg : histCfgs_){
	  std::string cutVar = cfg.var("_cut_"+cut.name());
	  df = df.Define(cutVar,cfg.var("["+cut.name()+"]"));
	  auto hist = df.Histo1D(cfg.histModel(cut.name()),cutVar);
	  cutHists->second.insert({cfg.var(""),hist});
	}
      }
      return hists;
    }
    
    //gets the cut string for printing, adding any defines used
    //this is a bit awful and should be refactored
    std::string getCutStr(const Cut& cut)const{
      std::cout <<"cut " <<cut.name()<<" "<<cut.expres()<<std::endl;
      std::string retVal(cut.expres());
      bool finished=false;
      std::vector<bool> found(defines_.size(),0);
      while(!finished){
	finished = true;
	for(size_t indx = 0;indx< defines_.size(); indx++){
	  const auto& define = defines_[indx];
	  //should do proper regex as this is overly greedy
	  if(!found[indx] && cut.expres().find(define.name())!=std::string::npos){
	    retVal+="\n"+define.name()+" = "+define.expres();
	    found[indx] = true;
	    finished = false;
	    std::cout<<"adding define "<<define.name()<<" "<<define.expres()<<std::endl;
	  }
	}
      }
      return retVal;
    }

    std::vector<CutHistColl> hists(ROOT::RDF::RNode df){
      std::vector<CutHistColl> hists;
      for(const auto& cut : cuts_){
	CutHistColl cutHists(cut.name(),getCutStr(cut));
	for(const auto& cfg : histCfgs_){
	  std::string cutVar = cfg.var("_cut_"+cut.name());
	  df = df.Define(cutVar,cfg.var("["+cut.name()+"]"));
	  auto hist = df.Histo1D(cfg.histModel(cut.name()),cutVar);
	  cutHists.add(cfg.var(""),hist);
	 
	}
	hists.push_back(cutHists);
      }
      return hists;
    }
    
  };

  class Hist2DBasedCut {

  public:
    
    Hist2DBasedCut(TH2* hist){
      hist_ = (TH2*) hist->Clone("hist2DCutValues");
      hist_->SetDirectory(0);
    }
    
    ~Hist2DBasedCut(){
      delete hist_;
    }
    
    Hist2DBasedCut(const Hist2DBasedCut& rhs){
      hist_ = (TH2*) rhs.hist_->Clone("hist2DCutValues");
    }
    Hist2DBasedCut(Hist2DBasedCut&& rhs){
      hist_ = rhs.hist_;
      rhs.hist_ = nullptr;
    }
    
    Hist2DBasedCut& operator=(const Hist2DBasedCut& rhs){
      if(this!=&rhs){
	delete hist_;
	hist_ = (TH2*) rhs.hist_->Clone("hist2DCutValues");
      }
      return *this;
    }
    Hist2DBasedCut& operator=(Hist2DBasedCut&& rhs){
      if(this!=&rhs){
	delete hist_;
	hist_ = rhs.hist_;
	rhs.hist_=nullptr;
      }
      return *this;
    }
    
    ROOT::VecOps::RVec<bool>
    operator() (const ROOT::VecOps::RVec<float>& var,
		const ROOT::VecOps::RVec<float>& xvar,
		const ROOT::VecOps::RVec<float>& yvar)const{
      ROOT::VecOps::RVec<bool> retVal(var.size());
      for(size_t index=0;index<var.size();index++){
	const int xbinnr = hist_->GetXaxis()->FindFixBin(xvar[index]);
	const int ybinnr = hist_->GetYaxis()->FindFixBin(yvar[index]);
	const float cutval = hist_->GetBinContent(xbinnr,ybinnr);
	retVal[index]=var[index] < cutval;
      }
      return retVal;
    }
    
  private:
    TH2* hist_;
  };
  
};

#endif
