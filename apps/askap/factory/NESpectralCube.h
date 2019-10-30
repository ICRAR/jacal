/// @file NESpectralCube.h
/// @brief Build an output image cube from Normal Equations - not Params. SO dont assume we know the names of the slices
/// @details This drop will be able to build an output cube of any format
/// supported by ASKAPSoft



#ifndef ASKAP_FACTORY_NESPECTRALCUBE_H
#define ASKAP_FACTORY_NESPECTRALCUBE_H

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
#include <fitting/ImagingNormalEquations.h>



namespace askap {

    /// @brief Build an output image cube from input NormalEquations
    /// @details This class builds the output cube is whatever format specified
    /// by the parset.
    ///

    class NESpectralCube : public DaliugeApplication

    {

    public:

        typedef boost::shared_ptr<NESpectralCube> ShPtr;

        NESpectralCube(dlg_app_info *raw_app);

        static inline std::string ApplicationName() { return "NESpectralCube";}

        virtual ~NESpectralCube();

        static DaliugeApplication::ShPtr createDaliugeApplication(dlg_app_info *raw_app);

        virtual int init(const char ***arguments);

        virtual int run();

        virtual void data_written(const char *uid, const char *data, size_t n);

        virtual void drop_completed(const char *uid, drop_status status);

        void handleImageParams();

        private:


            //! @brief Parameter set
            //! @details key value list of configuration options
            LOFAR::ParameterSet itsParset;

            // The Normal Equations

            scimath::ImagingNormalEquations::ShPtr itsNe;

            boost::shared_ptr<cp::CubeBuilder> itsNECube;

            int itsChan;

    };

} // namespace askap


#endif //
