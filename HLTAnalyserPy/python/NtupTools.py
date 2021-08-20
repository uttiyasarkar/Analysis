from array import array

def treetype_to_arraytype(treetype):
    if treetype=='I': 
        return 'i'
    if treetype=='i': 
        return 'I'
    elif treetype=='F':
        return 'f'
    elif treetype=='b':
        return 'B'
    elif treetype=='B':
        return 'b'
    else:
        raise ValueError("undefined type code",treetype)

def make_leaf_name(name,type_,sizename=None):
    """converts a names to a leaf string for a branch
    goes to the format {name}/{type_} or the format {name}[sizename]/{type_}
    also changes '-' to '_'
    """
    array_str = "[{sizename}]".format(sizename=sizename) if sizename else ""    
    return '{}{}/{}'.format(name,array_str,type_).replace('-','_')


class TreeVar:
    """
    this defines a variable for a tree, creating a single branch for it
    the branch can be a single variable or an array depending on options
       tree = tree to add branch to
       varnametype = name of branch and root type eg foo/F
       func = a unary callable object which acts on the object the branch is being filled from
       maxsize = maxmimum number of objects storable  (sets the size of the storing array)     
       sizevar = a string if specified giving the number of objects stored in the branch for that entry, if empty the branch is just a single variable
    """
       
    def __init__(self,tree,varnametype,func,maxsize=1,sizevar=""):
        self.varname = varnametype.split("/")[0]
        self.vartype = varnametype.split("/")[1]
        self.func = func
        self.data = array(treetype_to_arraytype(self.vartype),[0]*maxsize)
        self.sizevar = sizevar
        self.create_branch(tree)

    def create_branch(self,tree):       
        tree.Branch(self.varname,self.data,make_leaf_name(self.varname,self.vartype,self.sizevar))
        
    def fill(self,obj,objnr=0):
        val = self.func(obj) if self.func else obj
        try:
            self.data[objnr] = val 
        except (IndexError,TypeError) as err:
            #much easier in python3, small hack here for 2.7
            err.message = "for var {} with objnr {} {} type {} error: '{}'".format(self.varname,objnr,len(self.data),self.vartype,err.message)
            err.args = (err.message,) + err.args[1:] 
            raise err


    def clear(self):
        for n,x in enumerate(self.data):
            self.data[n] = 0


