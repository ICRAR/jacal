/// @file LoadVis.h

/// @brief Load a CASA Measurement Set in the DaliugeApplication Framework
/// @details We will build on the LoadParset structure - but use the contents
/// of the parset to load a measurement set.



#ifndef ASKAP_FACTORY_LOADVIS_H
#define ASKAP_FACTORY_LOADVIS_H

#include "rename.h"

#include <daliuge/DaliugeApplication.h>

#include <casacore/casa/Quanta/MVDirection.h>

#include <boost/shared_ptr.hpp>

// LOFAR ParameterSet
#include <Common/ParameterSet.h>
// ASKAPSoft data accessor
#include <dataaccess/TableDataSource.h>

#include <fitting/Params.h>



namespace askap {
  /// @brief Loads visibility set
  /// @details Loads a configuration from a file drop and a visibility set from a casacore::Measurement Set
    class LoadVis : public DaliugeApplication

    {

    public:

        typedef boost::shared_ptr<LoadVis> ShPtr;

        LoadVis(dlg_app_info *raw_app);

        static inline std::string ApplicationName() { return "LoadVis";}

        virtual ~LoadVis();

        static DaliugeApplication::ShPtr createDaliugeApplication(dlg_app_info *raw_app);

        virtual int init(const char ***arguments);

        virtual int run();

        virtual void data_written(const char *uid, const char *data, size_t n);

        virtual void drop_completed(const char *uid, drop_status status);

        static std::vector<std::string> getDatasets(const LOFAR::ParameterSet& parset);


        private:

            /// The model
            askap::scimath::Params::ShPtr itsModel;

            // Parameter set
            LOFAR::ParameterSet itsParset;

            // Its channel of data

            casacore::IPosition freqInterval;


            casacore::IPosition timeInterval;

            // Its tangent point
            std::vector<casacore::MVDirection> itsTangent;

            int itsChan;


            // utility to build an Imaging Normal Equation from a parset
            // void buildNE();

            // these are the steps required by buildNE




    };

} // namespace askap


#endif //
