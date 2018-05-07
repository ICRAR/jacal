/// @file NEUtils.h

/// @brief set of static utility functions for the NE manipulation
/// @details just wanted some place to put some common functions to
/// avoid replication




#ifndef ASKAP_FACTORY_NEUTILS_H
#define ASKAP_FACTORY_NEUTILS_H

#include <daliuge/DaliugeApplication.h>

#include <boost/shared_ptr.hpp>
// LOFAR ParameterSet
#include <Common/ParameterSet.h>
#include <fitting/ImagingNormalEquations.h>
#include <fitting/Params.h>

#include <casacore/casa/BasicSL.h>
#include <casacore/casa/aips.h>
#include <casacore/casa/OS/Timer.h>
#include <casacore/ms/MeasurementSets/MeasurementSet.h>
#include <casacore/ms/MeasurementSets/MSColumns.h>
#include <casacore/ms/MSOper/MSReader.h>
#include <casacore/casa/Arrays/ArrayIO.h>
#include <casacore/casa/iostream.h>
#include <casacore/casa/namespace.h>
#include <casacore/casa/Quanta/MVTime.h>


namespace askap {

    static inline
    unsigned long usecs(struct timeval *start, struct timeval *end)
    {
      return (end->tv_sec - start->tv_sec) * 1000000 + (end->tv_usec - start->tv_usec);
    }

    /// @brief A set of static utilities
    /// @details These are just a set of static functions I use more than once
    class NEUtils

    {

    public:



        NEUtils() = delete;
        ~NEUtils() = delete;

        // gets an NE from an app input and puts it into the ShPtr
        static void receiveNE(askap::scimath::ImagingNormalEquations::ShPtr, dlg_input_info &input);
        // Same for Params
        static void receiveParams(askap::scimath::Params::ShPtr, dlg_input_info &input);
        // Needs a sendNE

        static void sendNE(askap::scimath::ImagingNormalEquations::ShPtr itsNe, dlg_output_info &output);

        static void sendParams(askap::scimath::Params::ShPtr params, dlg_output_info &output);

        // add parameters that may be missing from a configuration file
        static LOFAR::ParameterSet addMissingParameters(LOFAR::ParameterSet& parset);

        static std::vector<std::string> getDatasets(const LOFAR::ParameterSet& parset);

        static int getInput(dlg_app_info *app, const char * tag);

        static vector<int> getInputs(dlg_app_info *app, const char* tag);

        static int getOutput(dlg_app_info *app, const char * tag);

        static int getChan(char *uid);

        static int getNChan(LOFAR::ParameterSet& parset);

        static double getFrequency(LOFAR::ParameterSet& parset, int chan=0, bool barycentre=false);

        // these are from Synparallel.

        /// @brief read the models a parset file to the given params object
        /// @details The model can be composed from both images and components. This
        /// method populates Params object by adding model data read from the parset file.
        /// The model is given by shared pointer because the same method can be used for both
        /// simulations and calibration (the former populates itsModel, the latter populates
        /// itsPerfectModel)
        /// @param[in] parset reference to a LOFAR parameter set
        /// @param[in] pModel shared pointer to the params object (must exist)

        static void readModels(const LOFAR::ParameterSet& parset, const scimath::Params::ShPtr &pModel);

        private:





    };

} // namespace askap


#endif //
