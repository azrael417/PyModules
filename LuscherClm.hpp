//
//  PyClm.h
//  modules
//
//  Created by Thorsten Kurth on 28.04.15.
//
//

#ifndef _PYCLM
#define _PYCLM

#include "boost/python.hpp"
#include "mathutils.hpp"
#include "pertutils.hpp"

using namespace anatools;

PyObject* instanceCapsule;

//destructor
static void clm_destruct(PyObject* capsule){
    void* ptr=PyCapsule_GetPointer(capsule,"zetfunc");
    Zetafunc* zetptr=static_cast<Zetafunc*>(ptr);
    delete zetptr;
    return;
}

//constructor
static PyObject* clm_init(PyObject* self, PyObject *args)
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
    instanceCapsule=PyCapsule_New(static_cast<void*>(zetfunc),"zetfunc",&clm_destruct);
    
    Py_INCREF(Py_None);
    return Py_None;
}

//evaluate
static PyObject* clm_evaluate(PyObject* self, PyObject* args){
    //get the PyCObject from the args tuple:
    Py_XINCREF(instanceCapsule);
    void* tmpzetfunc=PyCapsule_GetPointer(instanceCapsule,"zetfunc");
    if (PyErr_Occurred()){
        std::cerr << "Some Error occured!" << std::endl;
        return NULL;
    }
    Zetafunc* zetfunc=static_cast< Zetafunc* >(tmpzetfunc);
    
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
    Py_XDECREF(instanceCapsule);
}

#endif
