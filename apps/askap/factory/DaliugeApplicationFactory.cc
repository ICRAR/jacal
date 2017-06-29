/// @file DaliugeApplicationFactory.cc
///
/// @abstract
/// Factory class that registers and manages the different possible instances of
/// of a DaliugeApplication.
/// @ details
/// Maintains a registry of possible applications and selects - based upon a name
/// which one will be instantiated.
///

// ASKAPsoft includes


#include <askap/AskapError.h>
#include <casacore/casa/OS/DynLib.h>        // for dynamic library loading
#include <casacore/casa/BasicSL/String.h>   // for downcase
#include <boost/program_options.hpp>

// Local package includes

#include <daliuge/DaliugeApplication.h>
#include <factory/DaliugeApplicationFactory.h>

// Apps need to be here - or can we register them from Somewhere else
#include <factory/Example.h>
#include <factory/LoadParset.h>
//

#include<string>

namespace askap {


  // Define the static registry.
  std::map<std::string, DaliugeApplicationFactory::DaliugeApplicationCreator*>
  DaliugeApplicationFactory::theirRegistry;


  DaliugeApplicationFactory::DaliugeApplicationFactory() {
  }

  void DaliugeApplicationFactory::registerDaliugeApplication (const std::string& name,
                                           DaliugeApplicationFactory::DaliugeApplicationCreator* creatorFunc)
  {
    fprintf(stdout, "\t factory - Adding %s to the application registry\n", name.c_str());
    theirRegistry[name] = creatorFunc;
  }

  DaliugeApplication::ShPtr DaliugeApplicationFactory::createDaliugeApplication (const std::string& name)
  {
    fprintf(stdout, "\t factory - Attempting to find %s in the registry\n",name.c_str());
    std::map<std::string,DaliugeApplicationCreator*>::const_iterator it = theirRegistry.find (name);
    if (it == theirRegistry.end()) {
      // Unknown Application. Try to load from a dynamic library
      // with that lowercase name (without possible template extension).
      std::string libname(casa::downcase(name));
      const std::string::size_type pos = libname.find_first_of (".<");
      if (pos != std::string::npos) {
        libname = libname.substr (0, pos);      // only take before . or <
      }
      // Try to load the dynamic library and execute its register function.
      // Do not dlclose the library.
      fprintf(stdout, "\t factory - Application %s is not in the Daliuge Application registry, attempting to load it dynamically\n", name.c_str());
      casa::DynLib dl(libname, string("libaskap_"), "register_"+libname, false);
      if (dl.getHandle()) {
        // Successfully loaded. Get the creator function.
        fprintf(stdout, "\t factory - Dynamically loaded ASKAP/Daliuge Application %s\n", name.c_str());
        // the first thing the Application in the shared library is supposed to do is to
        // register itself. Therefore, its name will appear in the registry.
        it = theirRegistry.find (name);
      }
    }
    if (it == theirRegistry.end()) {
      ASKAPTHROW(AskapError, "\t factory - Unknown Application " << name);
    }
    // Execute the registered function.
    return it->second(name);
  }

  // Make the Primary Beam object for the Primary Beam given in the parset file.
  // Currently the standard Beams are still handled by this function.
  // In the (near) future it should be done by putting creator functions
  // for these Beams in the registry and use that.

DaliugeApplication::ShPtr DaliugeApplicationFactory::make(const std::string &name) {

    if (theirRegistry.size() == 0) {
        // this is the first call of the method, we need to fill the registry with
        // all pre-defined applications
        fprintf(stdout, "\t factory - Filling the registry with predefined applications\n");
        addPreDefinedDaliugeApplication<Example>();
        addPreDefinedDaliugeApplication<LoadParset>();



    }

    // buffer for the result
    DaliugeApplication::ShPtr App;

    App = createDaliugeApplication (name);

    ASKAPASSERT(App); // if a App of that name is in the registry it will be here

    return App;
}



} // namespace askap
