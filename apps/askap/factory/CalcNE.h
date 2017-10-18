/// @file LoadVis.h

/// @brief Load a CASA Measurement Set in the DaliugeApplication Framework
/// @details We will build on the LoadParset structure - but use the contents
/// of the parset to load a measurement set.



#ifndef ASKAP_FACTORY_CALCNE_H
#define ASKAP_FACTORY_CALCNE_H

#include <daliuge/DaliugeApplication.h>

#include <casacore/casa/Quanta/MVDirection.h>

#include <boost/shared_ptr.hpp>

// LOFAR ParameterSet
#include <Common/ParameterSet.h>
// ASKAPSoft data accessor
#include <dataaccess/TableDataSource.h>

#include <fitting/Params.h>



namespace askap {

    /// @brief Calculates the Normal Equations
    /// @details This class encorporates all the tasks to read from a measurement set;
    /// subtract a model; grid residual visibilities and FFT the grid

    class CalcNE : public DaliugeApplication

    {

    public:

        typedef boost::shared_ptr<CalcNE> ShPtr;

        CalcNE();

        static inline std::string ApplicationName() { return "CalcNE";}

        virtual ~CalcNE();

        static DaliugeApplication::ShPtr createDaliugeApplication(const std::string &name);

        virtual int init(dlg_app_info *app, const char ***arguments);

        virtual int run(dlg_app_info *app);

        virtual void data_written(dlg_app_info *app, const char *uid,
            const char *data, size_t n);

        virtual void drop_completed(dlg_app_info *app, const char *uid,
            drop_status status);





        private:

            //! @brief The model
            //! @details contains a set of parameters - essentially the solution of the NE
            askap::scimath::Params::ShPtr itsModel;

            //! @brief Parameter set
            //! @details key value list of configuration options
            LOFAR::ParameterSet itsParset;

            // Its channel of data

            casa::IPosition freqInterval; ///< which channel range of the measurement set we are interested in


            casa::IPosition timeInterval;  ///< the time range we are interested in

            // Its tangent point
            std::vector<casa::MVDirection> itsTangent; ///< the tangent point of the current grid


            // utility to build an Imaging Normal Equation from a parset
            // void buildNE();

            // these are the steps required by buildNE




    };

} // namespace askap


#endif //
