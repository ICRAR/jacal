/// @file SpectralCube.h
/// @brief Build an output image cube
/// @details This drop will be able to build an output cube of any format
/// supported by ASKAPSoft



#ifndef ASKAP_FACTORY_SPECTRALCUBE_H
#define ASKAP_FACTORY_SPECTRALCUBE_H

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


    /*!
    * \brief Build the output image cube
    * \details This class builds the output cube is whatever format specified
    * by the parset.
    * \par EAGLE_START
    * \param gitrepo $(GIT_REPO)
    * \param version $(PROJECT_VERSION)
    * \param category DynlibApp
    * \param[in] port/Config/LOFAR::ParameterSet
    *     /~English ParameterSet descriptor for the image solver
    *     /~Chinese
    * \param[in] port/Model/scimath::Params
    *     /~English Params of solved normal equations
    *     /~Chinese
    * \param[out] port/Cube/undefined
    *     /~English
    *     /~Chinese
    * \par EAGLE_END
    */
    class SpectralCube : public DaliugeApplication
    {
    public:

        typedef boost::shared_ptr<SpectralCube> ShPtr;

        SpectralCube(dlg_app_info *raw_app);

        static inline std::string ApplicationName() { return "SpectralCube";}

        virtual ~SpectralCube();

        static DaliugeApplication::ShPtr createDaliugeApplication(dlg_app_info *raw_app);

        virtual int init(const char ***arguments);

        virtual int run();

        virtual void data_written(const char *uid, const char *data, size_t n);

        virtual void drop_completed(const char *uid, drop_status status);

        void handleImageParams();

        private:
            /// The model
            scimath::Params::ShPtr itsModel;

            //! @brief Parameter set
            //! @details key value list of configuration options
            LOFAR::ParameterSet itsParset;

            boost::shared_ptr<cp::CubeBuilder> itsImageCube;
            boost::shared_ptr<cp::CubeBuilder> itsPSFCube;
            boost::shared_ptr<cp::CubeBuilder> itsResidualCube;
            boost::shared_ptr<cp::CubeBuilder> itsWeightsCube;
            boost::shared_ptr<cp::CubeBuilder> itsPSFimageCube;
            boost::shared_ptr<cp::CubeBuilder> itsRestoredCube;

            int itsChan;

    };

} // namespace askap


#endif //
