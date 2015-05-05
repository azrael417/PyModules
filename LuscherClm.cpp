//
//  PyModules.cpp
//  modules
//
//  Created by Thorsten Kurth on 28.04.15.
//
//

#include "LuscherClm.hpp"

/** to-python convert to complex<double> */
struct dcomplex_to_python_object
{
    static PyObject* convert(dcomplex const& comp)
    {
        boost::python::object result=boost::python::object(complex<double>(comp.re(),comp.im()));
        return boost::python::incref(result.ptr());
    }
};

//raw constructor
boost::python::object Zetafunc_init(tuple args, dict kwargs) {
    // strip off self
    boost::python::object self = args[0];
    args = tuple(args.slice(1,_));
    
    // call appropriate C++ constructor
    // depending on raw arguments, these
    // C++ constructors must be exposed to
    // Python through .def(init<...>())
    // declarations
    unsigned int l=0;
    int m=0;
    
    if (len(args)==2) {
        l = extract<unsigned int>(args[0]);
        m = extract<int>(args[1]);
    }
    
    if (kwargs.contains("l")){
        l = extract<unsigned int>(kwargs["l"]);
    }
    if (kwargs.contains("m")){
        l = extract<int>(kwargs["m"]);
    }
    if(abs(m)>l){
        std::cerr << "Error, m is not allowed to be bigger than l! Resetting l and m to zero!" << std::endl;
        l=m=0;
    }
    
    return self.attr("__init__")(l,m);
}


BOOST_PYTHON_MODULE(threevecd)
{
    class_< threevec<double> >("threevecd",init<double,double,double>());
}

BOOST_PYTHON_MODULE(LuscherClm)
{
    class_<Zetafunc>("LuscherClm",no_init)
    .def("__init__",raw_function(Zetafunc_init), "Raw Constructor")
    .def(init<int,int, optional<double,threevec<double>,double,int> >())
    .def("__call__",&Zetafunc::operator(),return_value_policy<return_by_value>(),"Evaluate clm at value x");
    boost::python::to_python_converter<dcomplex,dcomplex_to_python_object>();
}
