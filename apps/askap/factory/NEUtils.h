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


namespace askap {

    struct app_data {
      LOFAR::ParameterSet *parset;
    };

    static inline
    struct app_data *to_app_data(dlg_app_info *app)
    {
      return (struct app_data *)app->data;
    }

    static inline
    unsigned long usecs(struct timeval *start, struct timeval *end)
    {
      return (end->tv_sec - start->tv_sec) * 1000000 + (end->tv_usec - start->tv_usec);
    }

    class NEUtils

    {

    public:



        NEUtils() { std::cout << "NEUtils default constructor - not expecting this to ever be called"
                              << std::endl;} ;
        ~NEUtils() { std::cout << "NEUtils default destructor - not expecting this to ever be called"
                              << std::endl;};

        // gets an NE from an app input and puts it into the ShPtr
        static void receiveNE(askap::scimath::ImagingNormalEquations::ShPtr, dlg_app_info *app, int input=0);
        // Same for Params
        static void receiveParams(askap::scimath::Params::ShPtr, dlg_app_info *app, int input=0);
        // Needs a sendNE

        static void sendNE(askap::scimath::ImagingNormalEquations::ShPtr itsNe, dlg_app_info *app, int output=0);

        static void sendParams(askap::scimath::Params::ShPtr params,dlg_app_info *app, int output=0);

        // add parameters that may be missing from a configuration file
        static LOFAR::ParameterSet addMissingParameters(LOFAR::ParameterSet& parset);

        static std::vector<std::string> getDatasets(const LOFAR::ParameterSet& parset);

        static int getInput(dlg_app_info *app, const char * tag);

        static int getOutput(dlg_app_info *app, const char * tag);

        private:





    };

} // namespace askap


#endif //
