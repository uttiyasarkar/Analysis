from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ROOT
import sys
import re
from enum import Enum
import functools
import os
import importlib

def load_fwlitelibs():
    ROOT.gSystem.Load("libFWCoreFWLite.so");
    ROOT.gSystem.Load("libDataFormatsFWLite.so");
    ROOT.FWLiteEnabler.enable()

def load_cmssw_cfg(filename):
    if filename.endswith(".py"):    
        dirname = os.path.dirname(filename)
        if not dirname:
            dirname = "./"

        sys.path.insert(0,dirname)
        oldargv = sys.argv[:]
        sys.argv = sys.argv[:1]
        cmssw_cfg = importlib.import_module(os.path.basename(filename)[:-3]) #removing the .py
        sys.argv = oldargv[:]
        sys.path.pop(0)
        return cmssw_cfg.process
    else:
        print("load_cmssw_cfg: error: filename {} does not end in .py, not loading".format(filename))
        return None




def convert_args(input_args):
    """supports ints, floats and strings and removes starting and ending quotes from strings"""
    
    output_args = []
    for arg in input_args:
        arg = arg.rstrip().lstrip()
        try:
            output_args.append(int(arg))
            break
        except ValueError:
            pass
        try: 
            output_args.append(float(arg))
        except ValueError:
            pass
        if arg.startswith('"') and arg.endswith('"'):
            output_args.append(arg[1:-1])
        else:
            output_args.append(arg)
    return output_args
        

class UnaryStrFunc:
    def __init__(self,func_str):
        res = self._convert(func_str)
        self.name = res[0]
        self.iscallable = res[1]
        self.args = res[2]

    def _convert(self,func_str):
        """
        this resolves a function string into name, callable, and args
        note, it assumes there are no chained funcs, so no "."
        """
        if func_str.find(".")!=-1:
            raise ValueError('function string " {} " must be a single function and therefore not contain "."'.format(func_str))
        
        #first check if it is just a property 
        if func_str.replace("_","").isalnum(): #basically allows "_" but not other non alphanumerica charactor
            return func_str,False,{}

        #okay is it a function
        re_res = re.search(r'([\w]+)(\(\)\Z)',func_str)
        if re_res:
            func_name = re_res.group(1)
            return func_name,True,{}

        #now check if its a function with arguments
        re_res = re.search(r'([\w]+)(\(([\w",. ]+)\))',func_str)
        if re_res:
            func_name = re_res.group(1)
            args = convert_args(re_res.group(3).split(","))
            try:
                return func_name,True,args
            except ValueError as err: 
                #much easier in python3, small hack here for 2.7
                err.message = "for function '{}' with args {}\n {}".format(func_name,str(args),err.message)
                err.args = (err.message,) + err.args[1:] 
                raise err

        raise RuntimeError("function string {} could not be resolved".format(func_str))

    def __call__(self,obj):
        if not self.iscallable:
            return getattr(obj,self.name)
        else :
            return getattr(obj,self.name)(*self.args)
        

class ChainedUnaryStrFunc:
    """
    this simple class defines a chain of functions/methods via a string
    basically allows us to stop intepreting "obj.method1(args).member1" and similar
    each time and just save the results
    """
    def __init__(self,func_str):
        self.funcs = [UnaryStrFunc(s) for s in func_str.split(".")]
            
    def __call__(self,obj):
        for func in self.funcs:
            obj = func(obj)
        return obj
        
def call_func(obj,func_str):
    """
    allows us to call a function/method via a string as you would type it in python
    It can also chain functions or simply return member variables
    examples:
       var("hltEgammaClusterShapeUnseeded_sigmaIEtaIEta5x5",0)
       eventAuxiliary().run()

    Now this is all handled by a class but this function is here for convenience
       
    """
    return ChainedUnaryStrFunc(func_str)(obj)

def get_filenames(input_filenames,prefix=""):
    output_filenames = []
    for filename in input_filenames:
        if not filename.endswith(".root"):
            with open(filename) as f:
                output_filenames.extend(['{}{}'.format(prefix,l.rstrip()) for l in f])
        else:
            output_filenames.append('{}{}'.format(prefix,filename))
    return output_filenames


def get_filenames_vec(input_filenames,prefix=""):
    output_filenames = ROOT.std.vector("std::string")()
    for filename in input_filenames:
        if not filename.endswith(".root"):
            with open(filename) as f:
                for line in f:
                    output_filenames.push_back('{}{}'.format(prefix,line.rstrip()))
        else:
            output_filenames.push_back('{}{}'.format(prefix,filename))
    return output_filenames




class UnaryFunc:
    """
    this is a simple class which allows us to define a unary function 
    this can be a method of function or a normal one
    can be specified using parital wrapping around the function or a string
    which allows us to convert functions to unary functions vi
    """
    class FuncType(Enum):
        default = 0
        str_ = 1 
        partial_ = 2
        

    def __init__(self,func):
        self.func = func        

        func_type = type(func)
        if func_type==str:
            self.func_type = UnaryFunc.FuncType.str_
            self.func = ChainedUnaryStrFunc(func)
        elif func_type==functools.partial:
            self.func_type = UnaryFunc.FuncType.partial_
        else:
            self.func_type = UnaryFunc.FuncType.default


    def __call__(self,obj):
        if self.func_type==UnaryFunc.FuncType.str_:
            return self.func(obj)
        #here we work around the fact we need to put the object as the first
        #argument to the function when using partial
        elif self.func_type==UnaryFunc.FuncType.partial_: 
            return self.func.func(obj,*self.func.args,**self.func.keywords)
        elif self.func_type==UnaryFunc.FuncType.default:
            return self.func(obj)
        else:
            raise ValueError("error, func_type {} not known".func_type)


def get_best_dr_match(obj_to_match,coll,max_dr):
    best_dr2 = max_dr*max_dr
    matched_obj = None
    eta = obj_to_match.eta()
    phi = obj_to_match.phi()
    for obj in coll:
        dr2 = ROOT.reco.deltaR2(eta,phi,obj.eta(),obj.phi())
        if dr2 < best_dr2:
            best_dr2 = dr2
            matched_obj = obj
    return matched_obj
        
            
