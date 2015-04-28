//
//  PyClm.h
//  modules
//
//  Created by Thorsten Kurth on 28.04.15.
//
//

#ifndef _PYCLM
#define _PYCLM

#include <Python/Python.h>
#include "mathutils.hpp"
#include "pertutils.hpp"

using namespace anatools;


//destructor
static void PyDelZetfunc(void* ptr){
    std::cout << "DELETED!" << std::endl;
    Zetafunc* zetptr=static_cast<Zetafunc*>(ptr);
    delete zetptr;
    return;
}

//constructor
static PyObject* clm_init(PyObject*, PyObject *args)
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
static PyObject* clm_evaluate(PyObject*, PyObject* args){
    //get the PyCObject from the args tuple:
    PyObject *pyzetfunc=0;
    if(!PyArg_ParseTuple(args,"O",&pyzetfunc)){
        std::cerr << "Cannot find object!" << std::endl;
        return NULL;
    }
    if(pyzetfunc==NULL){
        std::cerr << "Cannot find object!" << std::endl;
        return NULL;
    }
    
    //convert the object to void pointer and cast it to a zetfunc pointer
    void* tmp=PyCObject_AsVoidPtr(pyzetfunc);
    Zetafunc* zetfunc=static_cast< Zetafunc* >(tmp);
    
    std::cout << zetfunc->getGamma() << std::endl;
    
    //parse value:
    //double x=0.12;
    /*if(!PyArg_ParseTuple(args,"d",&x)){
        std::cerr << "Specify a number at which you want to evaluate the function" << std::endl;
        return NULL;
    }*/
    //double result=(*zetfunc)(x).re();
    
    //return the result as a packed function:
    //return Py_BuildValue("d",result);
}

#endif
