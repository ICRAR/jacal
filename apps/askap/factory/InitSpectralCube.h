/// @file InitSpectralCube.h
/// @brief Build an output image cube
/// @details This drop will be able to build an output cube of any format
/// supported by ASKAPSoft



#ifndef ASKAP_FACTORY_INITSPECTRALCUBE_H
#define ASKAP_FACTORY_INITSPECTRALCUBE_H

#include "rename.h"
#include <daliuge/DaliugeApplication.h>

#include <imageaccess/ImageAccessFactory.h>

#include "distributedimager/CubeBuilder.h"


#include <boost/shared_ptr.hpp>

// LOFAR ParameterSet
#include <Common/ParameterSet.h>


#include <casacore/images/Images/PagedImage.h>
#include <casacore/lattices/Lattices/PagedArray.h>
#include <casacore/casa/Arrays/Array.h>
#include <casacore/coordinates/Coordinates/CoordinateSystem.h>
#include <casacore/casa/Quanta.h>
#include <fitting/Params.h>


namespace askap {

    /// @brief Build the output image cube
    /// @details This class builds the output cube is whatever format specified
    /// by the parset.
    ///

    class InitSpectralCube : public DaliugeApplication

    {

    public:

        typedef boost::shared_ptr<InitSpectralCube> ShPtr;

        InitSpectralCube(dlg_app_info *raw_app);

        static inline std::string ApplicationName() { return "InitSpectralCube";}

        virtual ~InitSpectralCube();

        static DaliugeApplication::ShPtr createDaliugeApplication(dlg_app_info *raw_app);

        virtual int init(const char ***arguments);

        virtual int run();

        virtual void data_written(const char *uid, const char *data, size_t n);

        virtual void drop_completed(const char *uid, drop_status status);

      

        private:
            /// The model
            scimath::Params::ShPtr itsModel;

            //! @brief Parameter set
            //! @details key value list of configuration options
            LOFAR::ParameterSet itsParset;

            boost::shared_ptr<cp::CubeBuilder<casacore::Float> > itsImageCube;
            boost::shared_ptr<cp::CubeBuilder<casacore::Float> > itsPSFCube;
            boost::shared_ptr<cp::CubeBuilder<casacore::Float> > itsResidualCube;
            boost::shared_ptr<cp::CubeBuilder<casacore::Float> > itsWeightsCube;
            boost::shared_ptr<cp::CubeBuilder<casacore::Float> > itsPSFimageCube;
            boost::shared_ptr<cp::CubeBuilder<casacore::Float> > itsRestoredCube;

            int itsChan;

    };

} // namespace askap


#endif //
