/// @file CubeBuilder.h
/// @brief Build an output image cube
/// @details This drop will be able to build an output cube of any format
/// supported by ASKAPSoft



#ifndef ASKAP_FACTORY_CUBEBUILDER_H
#define ASKAP_FACTORY_CUBEBUILDER_H

#include <daliuge/DaliugeApplication.h>

#include <imageaccess/ImageAccessFactory.h>

#include <boost/shared_ptr.hpp>

// LOFAR ParameterSet
#include <Common/ParameterSet.h>


#include <casacore/images/Images/PagedImage.h>
#include <casacore/lattices/Lattices/PagedArray.h>
#include <casacore/casa/Arrays/Array.h>
#include <casacore/coordinates/Coordinates/CoordinateSystem.h>
#include <casacore/casa/Quanta.h>


namespace askap {

    /// @brief Build the output image cube
    /// @details This class builds the output cube is whatever format specified
    /// by the parset.
    ///

    class CubeBuilder : public DaliugeApplication

    {

    public:

        typedef boost::shared_ptr<CubeBuilder> ShPtr;

        CubeBuilder(dlg_app_info *raw_app);

        static inline std::string ApplicationName() { return "CubeBuilder";}

        virtual ~CubeBuilder();

        static DaliugeApplication::ShPtr createDaliugeApplication(dlg_app_info *raw_app);

        boost::shared_ptr<accessors::IImageAccess> Construct(
                    const casa::uInt nchan,
                    const casa::Quantity& f0,
                    const casa::Quantity& inc,
                    const std::string& name = "");

        boost::shared_ptr<accessors::IImageAccess> Construct(const std:: string& name);


        virtual int init(const char ***arguments);

        virtual int run();

        virtual void data_written(const char *uid, const char *data, size_t n);

        virtual void drop_completed(const char *uid, drop_status status);



        private:


            //! @brief Parameter set
            //! @details key value list of configuration options
            LOFAR::ParameterSet itsParset;

            boost::shared_ptr<accessors::IImageAccess> itsImageCube;
            boost::shared_ptr<accessors::IImageAccess> itsPSFCube;
            boost::shared_ptr<accessors::IImageAccess> itsResidualCube;
            boost::shared_ptr<accessors::IImageAccess> itsWeightsCube;
            boost::shared_ptr<accessors::IImageAccess> itsPSFimageCube;
            boost::shared_ptr<accessors::IImageAccess> itsRestoredCube;


            /// Rest frequency to be written to the cubes
            casa::Quantum<double> itsRestFrequency;

            std::string itsFilename;

            casa::Vector<casa::Stokes::StokesTypes> itsStokes;

            casa::CoordinateSystem
            createCoordinateSystem(const LOFAR::ParameterSet& parset,
                                   const casa::uInt nx,
                                   const casa::uInt ny,
                                   const casa::Quantity& f0,
                                   const casa::Quantity& inc);

    };

} // namespace askap


#endif //
