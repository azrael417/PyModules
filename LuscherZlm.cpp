//
//  PyModules.cpp
//  modules
//
//  Created by Thorsten Kurth on 28.04.15.
//
//

#include "LuscherZlm.hpp"

/** to-python convert to complex<double> */
struct dcomplex_to_python_object
{
    static PyObject* convert(dcomplex const& comp)
    {
        PyObject* result;
        if(std::abs(comp.im())<=std::numeric_limits<double>::epsilon()){
            result=PyFloat_FromDouble(comp.re());
        }
        else{
            result=PyComplex_FromDoubles(comp.re(),comp.im());
        }
        Py_INCREF(result);
        return result;
    }
};

//raw constructor
boost::python::object Zetafunc_init(boost::python::tuple args, boost::python::dict kwargs) {
    // strip off self
    boost::python::object self = args[0];
    args = boost::python::tuple(args.slice(1,_));
    
    // call appropriate C++ constructor
    // depending on raw arguments, these
    // C++ constructors must be exposed to
    // Python through .def(init<...>())
    // declarations
    unsigned int l=0;
    int m=0;
    
    if (len(args)==2) {
        l = boost::python::extract<unsigned int>(args[0]);
        m = boost::python::extract<int>(args[1]);
    }
    
    if (kwargs.contains("l")){
        l = boost::python::extract<unsigned int>(kwargs["l"]);
    }
    if (kwargs.contains("m")){
        m = boost::python::extract<int>(kwargs["m"]);
    }
    if(std::abs(m)>l){
        std::cerr << "Error, m is not allowed to be bigger than l! Resetting l and m to zero!" << std::endl;
        l=m=0;
    }
    
    return self.attr("__init__")(l,m);
}


BOOST_PYTHON_MODULE(threevecd)
{
    boost::python::class_< threevec<double> >("threevecd",init<double,double,double>());
}

BOOST_PYTHON_MODULE(LuscherZlm)
{
    boost::python::class_<Zetafunc>("LuscherZlm",no_init)
    .def("__init__",raw_function(Zetafunc_init), "Raw Constructor")
    .def(init<int,int, optional<double,threevec<double>,double,int> >())
    .def("__call__",&Zetafunc::operator(),return_value_policy<return_by_value>(),"Evaluate Zeta-function at value x");
    boost::python::to_python_converter<dcomplex,dcomplex_to_python_object>();
}
