//
//  clm.cpp
//  modules
//
//  Created by Thorsten Kurth on 28.04.15.
//
//

#include "PyModules.hpp"

//destructor
static void PyDelZetfunc(void* ptr){
    Zetafunc* zetptr=static_cast<Zetafunc*>(ptr);
    delete zetptr;
    return;
}

//constructor
static PyObject*
clm_init(PyObject *self, PyObject *args)
{
    //return value
    PyObject* result=NULL;
    
    //parse variables
    unsigned int lval=0;
    int mval=0;
    if(!PyArg_ParseTuple(args,"li",&lval,&mval)){
        ::std::cout << "Please specify l and m!" << ::std::endl;
        return result;
    }
    
    //class instance:
    Zetafunc* zetfunc=new Zetafunc(lval,mval);
    result=PyCObject_FromVoidPtr(zetfunc, PyDelZetfunc);
    return result;
}

//evaluate
PyObject* clm_evaluate(PyObject*, PyObject* args){
    //get the PyCObject from the args tuple:
    PyObject *pyzetfunc=0;
    if(!PyArg_ParseTuple(args,"O",&pyzetfunc)){
        return NULL;
    }
    
    //convert the object to void pointer and cast it to a zetfunc pointer
    void* tmp=PyCObject_AsVoidPtr(pyzetfunc);
    Zetafunc* zetfunc=static_cast< Zetafunc* >(tmp);
    
    //parse value:
    double x;
    if(!PyArg_ParseTuple(args,"d",&x)){
        ::std::cout << "Please specify a number at which the function shall be evaluated!" << ::std::endl;
        return NULL;
    }
    double result=(*zetfunc)(x).re();
    
    //return the result as a packed function:
    return Py_BuildValue("d",result);
}

static PyMethodDef clmMethods[] = {
    {"init",  clm_init, METH_VARARGS, "Initialize clm class!"},
    {"evaluate", clm_evaluate, METH_VARARGS, "Evaluate the Zeta-Function!"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initclm(void)
{
    (void) Py_InitModule("clm", clmMethods);
}

