/// @file LoadVis.h

/// @brief Load a CASA Measurement Set in the DaliugeApplication Framework
/// @details We will build on the LoadParset structure - but use the contents
/// of the parset to load a measurement set.



#ifndef ASKAP_FACTORY_LOADVIS_H
#define ASKAP_FACTORY_LOADVIS_H

#include <daliuge/DaliugeApplication.h>

#include <boost/shared_ptr.hpp>

// LOFAR ParameterSet
#include <Common/ParameterSet.h>
// ASKAPSoft data accessor
#include <dataaccess/TableDataSource.h>

#include <fitting/Params.h>



namespace askap {

    class LoadVis : public DaliugeApplication

    {

    public:

        typedef boost::shared_ptr<LoadVis> ShPtr;

        LoadVis();

        static inline std::string ApplicationName() { return "LoadVis";}

        virtual ~LoadVis();

        static DaliugeApplication::ShPtr createDaliugeApplication(const std::string &name);

        virtual int init(dlg_app_info *app, const char ***arguments);

        virtual int run(dlg_app_info *app);

        virtual void data_written(dlg_app_info *app, const char *uid,
            const char *data, size_t n);

        virtual void drop_completed(dlg_app_info *app, const char *uid,
            drop_status status);

        private:

            /// The model
            askap::scimath::Params::ShPtr itsModel;

            // Parameter set
            LOFAR::ParameterSet itsParset;

            // utiliy to get datasets from parset ....



            std::vector<std::string> getDatasets();

            // Its channel of data

            casa::IPosition freqInterval;

            //

            casa::IPosition timeInterval;
            // utility to build an Imaging Normal Equation from a parset
            // void buildNE();

            // these are the steps required by buildNE




    };

} // namespace askap


#endif //
