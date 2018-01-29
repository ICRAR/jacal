/// @file CubeBuilder.cc
///
/// @abstract
/// Derived from DaliugeApplication
/// @ details
/// Implements a test method that uses the contents of the the parset to load
/// in a measurement set and print a summary of its contents
///
// for logging
#define ASKAP_PACKAGE_NAME "CubeBuilder"
#include <string>
/// askap namespace
namespace askap {
/// @return version of the package
    std::string getAskapPackageVersion_CubeBuilder() {
        return std::string("CubeBuilder; ASKAPsoft==Unknown");

    }
}
/// The version of the package
#define ASKAP_PACKAGE_VERSION askap::getAskapPackageVersion_CubeBuilder()

#include <vector>
#include <mutex>


#include <daliuge/DaliugeApplication.h>
#include <factory/CubeBuilder.h>
#include <factory/NEUtils.h>



// LOFAR ParameterSet
#include <Common/ParameterSet.h>
// LOFAR Blob
#include <Blob/BlobString.h>
#include <Blob/BlobOBufString.h>
#include <Blob/BlobIBufString.h>
#include <Blob/BlobOStream.h>
#include <Blob/BlobIStream.h>
// ASKAP Logger

#include <askap/AskapLogging.h>
#include <askap/AskapError.h>

// Data accessors
#include <dataaccess/TableConstDataSource.h>
#include <dataaccess/IConstDataIterator.h>
#include <dataaccess/IDataConverter.h>
#include <dataaccess/IDataSelector.h>
#include <dataaccess/IDataIterator.h>
#include <dataaccess/SharedIter.h>

// Image accessors
#include <imageaccess/ImageAccessFactory.h>

// params helpers
#include <measurementequation/SynthesisParamsHelper.h>
#include <measurementequation/ImageParamsHelper.h>
#include <measurementequation/ImageFFTEquation.h>
#include <parallel/GroupVisAggregator.h>


#include <gridding/IVisGridder.h>
#include <gridding/VisGridderFactory.h>


#include <utils/PolConverter.h>

// casacore

#include <casacore/casa/Arrays/IPosition.h>
#include <casacore/coordinates/Coordinates/SpectralCoordinate.h>
#include <casacore/coordinates/Coordinates/DirectionCoordinate.h>
#include <casacore/coordinates/Coordinates/StokesCoordinate.h>
#include <casacore/coordinates/Coordinates/CoordinateSystem.h>
#include <casacore/measures/Measures/Stokes.h>
#include <casacore/images/Images/PagedImage.h>
#include <casacore/casa/Quanta/Unit.h>
#include <casacore/casa/Quanta/QC.h>

#include <fitting/Params.h>


#include <string.h>
#include <sys/time.h>



ASKAP_LOGGER(logger, ".CubeBuilder");

namespace askap {

    CubeBuilder::CubeBuilder(dlg_app_info *raw_app) :
        DaliugeApplication(raw_app)
    {

    }

      boost::shared_ptr<accessors::IImageAccess> CubeBuilder::Construct(const std::string& name) {
        // as long as the cube exists all should be fine
        ASKAPLOG_INFO_STR(logger, "Instantiating Cube Builder with existing cube ");
        boost::shared_ptr<accessors::IImageAccess> itsCube = accessors::imageAccessFactory(this->itsParset);

        vector<string> filenames;
        /// Image name from parset - must start with "image."

        if (itsParset.isDefined("Images.Names")) {
            filenames = itsParset.getStringVector("Images.Names", true);
            itsFilename = filenames[0];
        }
        else if(itsParset.isDefined("Images.name")) {
            itsFilename = itsParset.getString("Images.name");
        }
        else {
            ASKAPLOG_ERROR_STR(logger, "Could not find the image name(s) ");
        }
        ASKAPCHECK(itsFilename.substr(0,5)=="image",
                   "Images.name (Names) must start with 'image' starts with " << itsFilename.substr(0,5));

        // If necessary, replace "image" with _name_ (e.g. "psf", "weights")
        // unless name='restored', in which case we append ".restored"
        if (!name.empty()) {
            if (name == "restored") {
                itsFilename = itsFilename + ".restored";
            } else {
                const string orig = "image";
                const size_t f = itsFilename.find(orig);
                itsFilename.replace(f, orig.length(), name);
            }
        }

        ASKAPLOG_INFO_STR(logger, "Contructing cube instance using existing file " << itsFilename);

        return itsCube;
    }
    boost::shared_ptr<accessors::IImageAccess>  CubeBuilder::Construct(
                             const casa::uInt nchan,
                             const casa::Quantity& f0,
                             const casa::Quantity& inc,
                             const std::string& name)
    {
        ASKAPLOG_INFO_STR(logger, "Instantiating Cube by creating cube file");
          boost::shared_ptr<accessors::IImageAccess> itsCube = accessors::imageAccessFactory(this->itsParset);

        vector<std::string> filenames;


        if (itsParset.isDefined("Images.Names")) {
            filenames = itsParset.getStringVector("Images.Names", true);
            itsFilename = filenames[0];
        }
        else if(itsParset.isDefined("Images.name")) {
            itsFilename = itsParset.getString("Images.name");
        }
        else {
            ASKAPLOG_ERROR_STR(logger, "Could not find the image name(s) ");
        }
        ASKAPCHECK(itsFilename.substr(0,5)=="image",
                   "Images.name (Names) must start with 'image' starts with " << itsFilename.substr(0,5));

        // If necessary, replace "image" with _name_ (e.g. "psf", "weights")
        // unless name='restored', in which case we append ".restored"
        if (!name.empty()) {
            if (name == "restored") {
                itsFilename = itsFilename + ".restored";
            } else {
                const string orig = "image";
                const size_t f = itsFilename.find(orig);
                itsFilename.replace(f, orig.length(), name);
            }
        }

        const std::string restFreqString = itsParset.getString("Images.restFrequency", "-1.");
        if (restFreqString == "HI") {
            itsRestFrequency = casa::QC::HI;
        } else {
            itsRestFrequency = synthesis::SynthesisParamsHelper::convertQuantity(restFreqString, "Hz");
        }


        // Polarisation
        const std::vector<std::string>
            stokesVec = itsParset.getStringVector("Images.polarisation", std::vector<std::string>(1,"I"));
        // there could be many ways to define stokes, e.g. ["XX YY"] or ["XX","YY"] or "XX,YY"
        // to allow some flexibility we have to concatenate all elements first and then
        // allow the parser from PolConverter to take care of extracting the products.
        std::string stokesStr;
        for (size_t i=0; i<stokesVec.size(); ++i) {
            stokesStr += stokesVec[i];
        }  /// Description of the polarisation properties of the output cubes


        itsStokes = scimath::PolConverter::fromString(stokesStr);
        const casa::uInt npol=itsStokes.size();

        // Get the image shape
        const vector<casa::uInt> imageShapeVector = itsParset.getUintVector("Images.shape");
        const casa::uInt nx = imageShapeVector[0];
        const casa::uInt ny = imageShapeVector[1];
        const casa::IPosition cubeShape(4, nx, ny, npol, nchan);

        // Use a tile shape appropriate for plane-by-plane access
        casa::IPosition tileShape(cubeShape.nelements(), 1);
        tileShape(0) = 256;
        tileShape(1) = 256;

        const casa::CoordinateSystem csys = createCoordinateSystem(itsParset, nx, ny, f0, inc);

        ASKAPLOG_INFO_STR(logger, "Creating Cube " << itsFilename <<
                           " with shape [xsize:" << nx << " ysize:" << ny <<
                           " npol:" << npol << " nchan:" << nchan <<
                           "], f0: " << f0.getValue("MHz") << " MHz, finc: " <<
                           inc.getValue("kHz") << " kHz");

        itsCube->create(itsFilename, cubeShape, csys);

        // default flux units are Jy/pixel. If we set the restoring beam
        // later on, can set to Jy/beam
        itsCube->setUnits(itsFilename,"Jy/pixel");

        ASKAPLOG_INFO_STR(logger, "Instantiated Cube Builder by creating cube " << itsFilename);

        return itsCube;
    }


    CubeBuilder::~CubeBuilder() {
    }

    DaliugeApplication::ShPtr CubeBuilder::createDaliugeApplication(dlg_app_info *raw_app)
    {
        return CubeBuilder::ShPtr(new CubeBuilder(raw_app));
    }

    int CubeBuilder::init(const char ***arguments) {

        // Argument parsing is not working as yet

        char *parset_filename = 0;
        while (1) {

            const char **param = *arguments;

            // Sentinel
            if (param == NULL) {
                break;
            }
            // any params I might need go here:
            // filename:
            // no longer required as input comes from daliuge now
            //if (strcmp(param[0], "parset_filename") == 0) {
            //    parset_filename = strdup(param[1]);
            //}

            arguments++;
        }


        return 0;
    }

    int CubeBuilder::run() {


#ifndef ASKAP_PATCHED
        static std::mutex safety;
#endif // ASKAP_PATCHED

        // Lets get the key-value-parset
        ASKAP_LOGGER(logger, ".run");
        char buf[64*1024];

        size_t n_read = input("Config").read(buf, 64*1024);

        LOFAR::ParameterSet parset(true);
        parset.adoptBuffer(buf);

        this->itsParset = parset.makeSubset("Cimager.");

        // we need to fill the local parset with parameters that maybe missing
        //
        try {
#ifndef ASKAP_PATCHED
            std::lock_guard<std::mutex> guard(safety);
#endif // ASKAP_PATCHED
            this->itsParset = NEUtils::addMissingParameters(this->itsParset);
        }
        catch (std::runtime_error)
        {
            return -1;
        }

        // sort out the cube ....
        // get this from the parset?
        casa::Double baseFrequency = 1E9;
        casa::Double chanWidth = 1E5;
        casa::Int nchanCube = 8;
        // The above are all fake until I find a way to get them.

        casa::Quantity f0(baseFrequency,"Hz");
    /// The width of a channel. THis does <NOT> take account of the variable width
    /// of Barycentric channels
        casa::Quantity freqinc(chanWidth,"Hz");



        std::string img_name = "image";
        std::string psf_name = "psf";
        std::string residual_name = "residual";
        std::string weights_name = "weights";


        ASKAPLOG_DEBUG_STR(logger,"Configuring Spectral Cube");
        ASKAPLOG_DEBUG_STR(logger,"nchan: " << nchanCube << " base f0: " << f0.getValue("MHz") << " MHz "
        << " width: " << freqinc.getValue("MHz"));

        itsImageCube = this->Construct(nchanCube, f0, freqinc,img_name);
        itsPSFCube = this->Construct(nchanCube, f0, freqinc, psf_name);
        itsResidualCube = this->Construct(nchanCube, f0, freqinc, residual_name);
        itsWeightsCube = this->Construct(nchanCube, f0, freqinc, weights_name);


        return 0;
    }


    void CubeBuilder::data_written(const char *uid, const char *data, size_t n) {
        dlg_app_running();
    }

    void CubeBuilder::drop_completed(const char *uid, drop_status status) {
        dlg_app_done(APP_FINISHED);
    }

    casa::CoordinateSystem CubeBuilder::createCoordinateSystem(const LOFAR::ParameterSet& parset,
                                        const casa::uInt nx,
                                        const casa::uInt ny,
                                        const casa::Quantity& f0,
                                        const casa::Quantity& inc)
    {
        casa::CoordinateSystem coordsys;
        const vector<string> dirVector = parset.getStringVector("Images.direction");
        const vector<string> cellSizeVector = parset.getStringVector("Images.cellsize");


        // Direction Coordinate
        {
            casa::Matrix<casa::Double> xform(2, 2);
            xform = 0.0;
            xform.diagonal() = 1.0;
            const casa::Quantum<casa::Double> ra = asQuantity(dirVector.at(0), "deg");
            const casa::Quantum<casa::Double> dec = asQuantity(dirVector.at(1), "deg");
            ASKAPLOG_DEBUG_STR(logger, "Direction: " << ra.getValue() << " degrees, "
                               << dec.getValue() << " degrees");

            const casa::Quantum<casa::Double> xcellsize = asQuantity(cellSizeVector.at(0), "arcsec") * -1.0;
            const casa::Quantum<casa::Double> ycellsize = asQuantity(cellSizeVector.at(1), "arcsec");
            ASKAPLOG_DEBUG_STR(logger, "Cellsize: " << xcellsize.getValue()
                               << " arcsec, " << ycellsize.getValue() << " arcsec");

            casa::MDirection::Types type;
            casa::MDirection::getType(type, dirVector.at(2));
            const casa::DirectionCoordinate radec(type, casa::Projection(casa::Projection::SIN),
                                            ra, dec, xcellsize, ycellsize,
                                            xform, nx / 2, ny / 2);

            coordsys.addCoordinate(radec);
        }

        // Stokes Coordinate
        {

            // To make a StokesCoordinate, need to convert the StokesTypes
            // into integers explicitly
            casa::Vector<casa::Int> stokes(itsStokes.size());
            for(unsigned int i=0;i<stokes.size();i++){
                stokes[i] = itsStokes[i];
            }
            const casa::StokesCoordinate stokescoord(stokes);
            coordsys.addCoordinate(stokescoord);

        }
        // Spectral Coordinate
        {
            const casa::Double refPix = 0.0;  // is the reference pixel
            const bool barycentre = parset.getBool("barycentre",false);
            casa::MFrequency::Types freqRef=casa::MFrequency::TOPO;
            if (barycentre){
                freqRef = casa::MFrequency::BARY;
            }
            casa::SpectralCoordinate sc(freqRef, f0, inc, refPix);

            // add rest frequency, but only if requested, and only for
            // image.blah, residual.blah, image.blah.restored
            if (itsRestFrequency.getValue("Hz") > 0.) {
                if ((itsFilename.find("image.") != string::npos) ||
                        (itsFilename.find("residual.") != string::npos)) {

                    if (!sc.setRestFrequency(itsRestFrequency.getValue("Hz"))) {
                        ASKAPLOG_ERROR_STR(logger, "Could not set the rest frequency to " <<
                                           itsRestFrequency.getValue("Hz") << "Hz");
                    }
                }
            }

            coordsys.addCoordinate(sc);
        }

        return coordsys;
    }


} // namespace
