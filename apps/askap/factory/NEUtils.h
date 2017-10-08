/// @file NEUtils.h

/// @brief set of static utility functions for the NE manipulation
/// @details just wanted some place to put some common functions to
/// avoid replication




#ifndef ASKAP_FACTORY_NEUTILS_H
#define ASKAP_FACTORY_NEUTILS_H

#include <daliuge/DaliugeApplication.h>

#include <boost/shared_ptr.hpp>

#include <fitting/ImagingNormalEquations.h>


namespace askap {

    class NEUtils

    {

    public:



        NEUtils() { std::cout << "NEUtils default constructor - not expecting this to ever be called"
                              << std::endl;} ;
        ~NEUtils() { std::cout << "NEUtils default destructor - not expecting this to ever be called"
                              << std::endl;};

        // gets an NE from an app input and puts it into the ShPtr
        static void receiveNE(askap::scimath::ImagingNormalEquations::ShPtr, dlg_app_info *app);

        // Needs a sendNE


        private:





    };

} // namespace askap


#endif //
