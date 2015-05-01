//
//  PyClm.h
//  modules
//
//  Created by Thorsten Kurth on 28.04.15.
//
//

#ifndef _PYCLM
#define _PYCLM

#include <boost/python.hpp>
#include "mathutils.hpp"
#include "pertutils.hpp"

using namespace anatools;
using namespace boost::python;

/** to-python convert to complex<double> */
struct dcomplex_to_python_object
{
    static PyObject* convert(dcomplex const& comp)
    {
        if(fabs(comp.im())<std::numeric_limits<double>::epsilon()){
            boost::python::object result=boost::python::object(complex<double>(comp.re(),comp.im()));
            return boost::python::incref(result.ptr());
        }
        else{
            boost::python::object result=boost::python::object(comp.re());
            return boost::python::incref(result.ptr());
        }
    }
};


#endif
