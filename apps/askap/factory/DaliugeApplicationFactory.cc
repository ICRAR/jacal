/// @file DaliugeApplicationFactory.cc
///
/// @abstract
/// Factory class that registers and manages the different possible instances of
/// of a DaliugeApplication.
/// @ details
/// Maintains a registry of possible applications and selects - based upon a name
/// which one will be instantiated.
///

#include <string>
#define ASKAP_PACKAGE_NAME "DaliugeApplicationFactory"
/// askap namespace
namespace askap {
	/// @return version of the package
    std::string getAskapPackageVersion_DaliugeApplicationFactory() {
        return std::string("DaliugeApplicationFactory");
    }

} // namespace askap

/// The version of the package
#define ASKAP_PACKAGE_VERSION askap::getAskapPackageVersion_DaliugeApplicationFactory()
#include <askap/askap/AskapLogging.h>
#include <askap/askap/AskapError.h>



// ASKAPsoft includes

#include <askap/askap/AskapError.h>
#include <casacore/casa/OS/DynLib.h>        // for dynamic library loading
#include <casacore/casa/BasicSL/String.h>   // for downcase
#include <boost/program_options.hpp>

// Local package includes

#include <daliuge/DaliugeApplication.h>
#include <factory/DaliugeApplicationFactory.h>

// Apps need to be here - or can we register them from Somewhere else

#include <factory/LoadParset.h>
#include <factory/LoadVis.h>
#include <factory/MajorCycle.h>
#include <factory/LoadNE.h>
#include <factory/SolveNE.h>
#include <factory/RestoreSolver.h>
#include <factory/CalcNE.h>
#include <factory/OutputParams.h>
#include <factory/SpectralCube.h>
#include <factory/NESpectralCube.h>
#include <factory/InitSpectralCube.h>
#include <factory/JacalBPCalibrator.h>


//

#include <mutex>
#include <string>


namespace askap {


  // Define the static registry.
  std::map<std::string, DaliugeApplicationFactory::DaliugeApplicationCreator*>
  DaliugeApplicationFactory::theirRegistry;

  // Define the registry lock
  std::recursive_mutex DaliugeApplicationFactory::registry_lock;

  DaliugeApplicationFactory::DaliugeApplicationFactory() {
  }

  void DaliugeApplicationFactory::registerDaliugeApplication (const std::string& name,
                                           DaliugeApplicationFactory::DaliugeApplicationCreator* creatorFunc)
  {
    ASKAP_LOGGER(logger, ".registerDaliugeApplication");
    ASKAPLOG_INFO_STR(logger, "Adding " << name.c_str() << " to the application registry");
    {
        std::lock_guard<std::recursive_mutex> _(registry_lock);
        theirRegistry[name] = creatorFunc;
    }
  }

  DaliugeApplication::ShPtr DaliugeApplicationFactory::createDaliugeApplication (dlg_app_info *dlg_app)
  {

	ASKAP_LOGGER(logger, ".registerDaliugeApplication");
	const std::string name = dlg_app->appname;

	ASKAPLOG_INFO_STR(logger, "Attempting to find " <<  name << " in the registry");

    // It's a kind-of-long operation, but who cares, let's try at least to be
    // thread-safe
    std::lock_guard<std::recursive_mutex> _(registry_lock);

    std::map<std::string,DaliugeApplicationCreator*>::const_iterator it = theirRegistry.find (name);
    if (it == theirRegistry.end()) {
      // Unknown Application. Try to load from a dynamic library
      // with that lowercase name (without possible template extension).
      std::string libname(casacore::downcase(name));
      const std::string::size_type pos = libname.find_first_of (".<");
      if (pos != std::string::npos) {
        libname = libname.substr (0, pos);      // only take before . or <
      }
      // Try to load the dynamic library and execute its register function.
      // Do not dlclose the library.
      ASKAPLOG_INFO_STR(logger, "Application " << name.c_str() << " is not in the Daliuge Application registry, attempting to load it dynamically");

      casacore::DynLib dl(libname, string("libaskap_"), "register_"+libname, false);
      if (dl.getHandle()) {
        // Successfully loaded. Get the creator function.
        ASKAPLOG_INFO_STR(logger, "Dynamically loaded ASKAP/Daliuge Application " << name.c_str());
        // the first thing the Application in the shared library is supposed to do is to
        // register itself. Therefore, its name will appear in the registry.
        it = theirRegistry.find (name);
      }
    }
    if (it == theirRegistry.end()) {
      ASKAPTHROW(AskapError, "factory - Unknown Application " << name);
    }
    // Execute the registered function.
    return it->second(dlg_app);
  }


static std::once_flag initial_population_called;
void DaliugeApplicationFactory::initial_population() {

	ASKAP_LOGGER(logger, ".initial_population");

	std::lock_guard<std::recursive_mutex> _(registry_lock);

	if (theirRegistry.size() == 0) {
		// this is the first call of the method, we need to fill the registry with
		// all pre-defined applications
		ASKAPLOG_INFO_STR(logger, "Filling the registry with predefined applications");
		addPreDefinedDaliugeApplication<LoadParset>();
		addPreDefinedDaliugeApplication<LoadVis>();
		addPreDefinedDaliugeApplication<LoadNE>();
		addPreDefinedDaliugeApplication<SolveNE>();
		addPreDefinedDaliugeApplication<OutputParams>();
		addPreDefinedDaliugeApplication<CalcNE>();
    addPreDefinedDaliugeApplication<SpectralCube>();
    addPreDefinedDaliugeApplication<NESpectralCube>();
    addPreDefinedDaliugeApplication<InitSpectralCube>();
    addPreDefinedDaliugeApplication<JacalBPCalibrator>();
    addPreDefinedDaliugeApplication<MajorCycle>();
    addPreDefinedDaliugeApplication<RestoreSolver>();

  }
}

static std::once_flag init_logging_flag;
void init_logging() {
	ASKAPLOG_INIT("");
}

DaliugeApplication::ShPtr DaliugeApplicationFactory::make(dlg_app_info *dlg_app) {

	std::call_once(init_logging_flag, init_logging);
	std::call_once(initial_population_called, initial_population);

    // buffer for the result
    DaliugeApplication::ShPtr App = createDaliugeApplication(dlg_app);
    ASKAPASSERT(App); // if a App of that name is in the registry it will be here

    return App;
}



} // namespace askap
