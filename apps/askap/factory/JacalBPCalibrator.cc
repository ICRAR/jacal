/// @file
///
/// JacalBPCalibrator: part of the specialised tool to do optimised bandpass calibration with
/// limited functionality.  This class
///
///      * solves for bandpass only
///      * works only with preaveraging calibration approach
///      * does not support multiple chunks in time (i.e. only one solution is made for the whole dataset)
///      * does not support data distribution except per beam
///      * does not support a distributed model (e.h. with individual workers dealing with individual Taylor terms)
///      * does not require exact match between number of workers and number of channel chunks, data are dealt with
///        serially by each worker with multiple iterations over data, if required.
///      * solves normal equations at the worker level in the parallel case
///
/// This specialised tool is simply all that is required to get bandpass calibration into
/// a Daliuge drop
/// @copyright (c) 2018 CSIRO
/// Australia Telescope National Facility (ATNF)
/// Commonwealth Scientific and Industrial Research Organisation (CSIRO)
/// PO Box 76, Epping NSW 1710, Australia
/// atnf-enquiries@csiro.au
///
/// This file is part of the JACAL software distribution.
///
/// This file is based in part on BPCalibratorParallel.cc from the ASKAP distribution

/// Usage in graphs:
///
/// The assumption is that there will be a scatter over some number of channels
/// at the moment a drop only does a single channel in its allocation - but I might be able to
/// change that.
///
/// The output needs to be attached to a drop outside the scatter - or perhaps talk to Chen about a /// gather

// Include own header file first
#include "JacalBPCalibrator.h"
#include "NEUtils.h"
#include <daliuge/DaliugeApplication.h>
// logging stuff
#include <askap_synthesis.h>
#include <askap/AskapLogging.h>
ASKAP_LOGGER(logger, ".parallel");

// own includes
#include <askap/AskapError.h>
#include <askap/AskapUtil.h>
#include <Blob/BlobIStream.h>
#include <Blob/BlobOStream.h>
#include <profile/AskapProfiler.h>



#include <dataaccess/TableDataSource.h>
#include <dataaccess/ParsetInterface.h>

#include <fitting/LinearSolver.h>
#include <fitting/GenericNormalEquations.h>
#include <fitting/Params.h>

#include <measurementequation/ImageFFTEquation.h>
#include <measurementequation/SynthesisParamsHelper.h>
#include <measurementequation/MEParsetInterface.h>
#include <measurementequation/CalibrationME.h>
#include <measurementequation/PreAvgCalMEBase.h>
#include <measurementequation/ComponentEquation.h>
#include <measurementequation/NoXPolGain.h>
#include <measurementequation/NoXPolFreqDependentGain.h>
#include <measurementequation/NoXPolBeamIndependentGain.h>
#include <measurementequation/ImagingEquationAdapter.h>
#include <measurementequation/IMeasurementEquation.h>
#include <gridding/VisGridderFactory.h>
#include <askapparallel/AskapParallel.h>
#include <Common/ParameterSet.h>
#include <calibaccess/CalParamNameHelper.h>
#include <calibaccess/CalibAccessFactory.h>
#include <calibaccess/ServiceCalSolutionSourceStub.h>
#include <calserviceaccessor/ServiceCalSolutionSource.h>



// casa includes
#include <casacore/casa/aips.h>
#include <casacore/casa/OS/Timer.h>

namespace askap {



/// @brief Constructor for Jacal application
/// @details The parset is used to construct the internal state. We could
/// also support construction from a python dictionary (for example).
/// @param[in] raw_app Daliuge communication object

JacalBPCalibrator::JacalBPCalibrator(dlg_app_info *raw_app) : DaliugeApplication(raw_app),
      itsPerfectModel(new scimath::Params()), itsRefAntenna(-1), itsSolutionID(-1), itsSolutionIDValid(false),itsModel(new scimath::Params()),itsSolver(scimath::Solver::ShPtr(new scimath::Solver)),itsNe(new scimath::ImagingNormalEquations(*itsModel))
{

  this->itsChan = NEUtils::getChan(raw_app->uid);

  if (this->itsChan < 0) { // we are outside a loop

    this->isMaster = true;
    this->isWorker = false;

  }
  else {
    this->isWorker = true;
    this->isMaster = false;

  }
  this->isParallel =  true;




}

DaliugeApplication::ShPtr JacalBPCalibrator::createDaliugeApplication(dlg_app_info *raw_app)
{
    return JacalBPCalibrator::ShPtr(new JacalBPCalibrator(raw_app));
}

int JacalBPCalibrator::init(const char ***arguments) {

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

  //  FIXME:
  //    This should be here but I could not get a boost smart pointer to work
  //    to_app_data(app)->parset.reset( new LOFAR::ParameterSet(parset_filename));
  //

  // FIXME:
  // Arbitrarily setting frequency selection to 1


  this->freqInterval = casa::IPosition(2,0);
  this->timeInterval = casa::IPosition(2,0);

  this->freqInterval[0] = this->itsChan;
  this->freqInterval[1] = this->itsChan+1;

  return 0;
}
int JacalBPCalibrator::run() {
  // Lets get the key-value-parset
  ASKAP_LOGGER(logger, ".run");

  char buf[64*1024];
  size_t n_read = input(0).read(buf, 64*1024);
  if (n_read == 64*1024) {
      n_read--;
  }
  buf[n_read] = 0;

  LOFAR::ParameterSet parset(true);
  parset.adoptBuffer(buf);

  this->itsParset = parset.makeSubset("Cbpcalibrator.");

  ASKAPLOG_INFO_STR(logger, "Bandpass will be solved for using a specialised pipeline");
  if (this->isMaster) {
      // setup solution source (or sink to be exact, because we're writing the solution here)
      itsSolutionSource = accessors::CalibAccessFactory::rwCalSolutionSource(this->itsParset);
      ASKAPASSERT(itsSolutionSource);

      if (this->isParallel) {
          ASKAPLOG_INFO_STR(logger, "The work will be distributed between workers");
      } else {
          ASKAPLOG_INFO_STR(logger, "The work will be done in the serial by the current process");
      }

      // This is sloppy but I need to test whether this is likely to be a service
      // source as I need to reinstantiate the full implementation - as all we get from the factory
      // is a stub.

      const std::string calAccType = this->itsParset.getString("calibaccess","parset");

      if (calAccType == "service") {
        itsSolutionSource.reset(new ServiceCalSolutionSource(this->itsParset));
        ASKAPLOG_INFO_STR(logger,"Obtaining calibration information from service source");
        ASKAPLOG_INFO_STR(logger,"SolutionID determined by ServiceSource");
        itsSolutionIDValid=true;
        // we are only solving for bandpass
        boost::shared_ptr<ServiceCalSolutionSource> src = boost::dynamic_pointer_cast<ServiceCalSolutionSource>(itsSolutionSource);
        src->solveBandpass();

      }

  }
  if (this->isWorker) {
      // set datasets (we cannot rely on the code in base classes because we don't distribute by node here
      setMeasurementSets(itsParset.getStringVector("dataset"));

      /// Create solver in workers
      itsSolver.reset(new scimath::LinearSolver(1e3));
      ASKAPCHECK(itsSolver, "Solver not defined correctly");
      ASKAPCHECK(!parset.isDefined("refgain"), "usage of refgain is deprecated, define reference antenna instead");
      itsRefAntenna = parset.getInt32("refantenna",-1);
      if (itsRefAntenna >= 0) {
          ASKAPLOG_INFO_STR(logger, "Phases will be rotated, so antenna "<<itsRefAntenna<<" has zero phase for all channels and beams in the first polarisation");
          ASKAPCHECK(itsRefAntenna < static_cast<int>(nAnt()), "Requested reference antenna doesn't exist, nAnt="<<nAnt());
      } else {
          ASKAPLOG_INFO_STR(logger, "No phase rotation will be done between iterations");
      }

      // load sky model, populate itsPerfectModel
      readModels();
      if (this->isParallel) {
          // setup work units in the parallel case, make beams the first (fastest to change) parameter to achieve
          // greater benefits if multiple measurement sets are present (more likely to be scheduled for different ranks)
          ASKAPLOG_INFO_STR(logger, "Work for "<<nBeam()<<" beams and "<<nChan()<<" channels will be split between ranks, this one handles a single channel - but we could define a chunk");
          itsWorkUnitIterator.init(casa::IPosition(2, nBeam(), nChan()), 1, this->itsChan);
          ASKAPLOG_INFO_STR(logger, "Initialised iterator");
      }

      ASKAPCHECK((measurementSets().size() == 1) || (measurementSets().size() == nBeam()),
          "Number of measurement sets given in the parset ("<<measurementSets().size()<<
          ") should be either 1 or equal the number of beams ("<<nBeam()<<")");
  }
  if (!this->isParallel) { // not implemented
      // setup work units in the serial case - all work to be done here
      ASKAPLOG_INFO_STR(logger, "All work for "<<nBeam()<<" beams and "<<nChan()<<" channels will be handled by this rank");
      itsWorkUnitIterator.init(casa::IPosition(2, nBeam(), nChan()));
  }

  if (this->isMaster) {
    ASKAPLOG_INFO_STR(logger, "About to set the solution accessor");
    if (!itsSolutionIDValid) {
        // obtain solution ID only once, the results can come in random order and the
        // accessor is responsible for aggregating all of them together. This is done based on this ID.
        //@todo Can probably get rid of this
        itsSolutionID = itsSolutionSource->newSolutionID(solutionTime());
        itsSolutionIDValid = true;
    }
    ASKAPLOG_INFO_STR(logger, "Have set solutionID");
    itsSolAcc = itsSolutionSource->rwSolution(itsSolutionID);
    ASKAPLOG_INFO_STR(logger, "Have set solution accessor");
    ASKAPASSERT(itsSolAcc);
  }

  if (this->itsChan >=0) {
      ASKAPDEBUGASSERT(itsModel);
      const int nCycles = this->parset().getInt32("ncycles", 1);
      ASKAPCHECK(nCycles >= 0, " Number of calibration iterations should be a non-negative number, you have " << nCycles);
      for (itsWorkUnitIterator.origin(); itsWorkUnitIterator.hasMore(); itsWorkUnitIterator.next()) {
           // this will force creation of the new measurement equation for this beam/channel pair
           itsEquation.reset();

           const std::pair<casa::uInt, casa::uInt> indices = currentBeamAndChannel();

           ASKAPLOG_INFO_STR(logger, "Initialise bandpass (unknowns) for "<<nAnt()<<" antennas for beam="<<indices.first<<
                             " and channel="<<indices.second);
           itsModel->reset();
           for (casa::uInt ant = 0; ant<nAnt(); ++ant) {
                itsModel->add(accessors::CalParamNameHelper::paramName(ant, indices.first, casa::Stokes::XX), casa::Complex(1.,0.));
                itsModel->add(accessors::CalParamNameHelper::paramName(ant, indices.first, casa::Stokes::YY), casa::Complex(1.,0.));
           }

           // setup reference gain, if needed
           if (itsRefAntenna >= 0) {
               //itsRefGain = accessors::CalParamNameHelper::paramName(itsRefAntenna, indices.first, casa::Stokes::XX);
         //wasim was here
               itsRefGainXX = accessors::CalParamNameHelper::paramName(itsRefAntenna, indices.first, casa::Stokes::XX);
               itsRefGainYY = accessors::CalParamNameHelper::paramName(itsRefAntenna, indices.first, casa::Stokes::YY);
           } else {
               itsRefGainXX = "";
               itsRefGainYY = "";
           }

           for (int cycle = 0; (cycle < nCycles) && validSolution(); ++cycle) {
                ASKAPLOG_INFO_STR(logger, "*** Starting calibration iteration " << cycle + 1 << " for beam="<<
                              indices.first<<" and channel="<<indices.second<<" ***");
                // iterator is used to access the current work unit inside calcNE

                /// FIXME: I could break this into two pieces as I have for the imaging - instead the BP calibrator
                /// does all it needs to do in a single drop.
                calcNE();
                ///
                solveNE();
           }
           if (this->itsChan >=0) {
               // send the model to the master, add beam and channel tags first
               itsModel->add("beam",static_cast<double>(indices.first));
               itsModel->add("channel",static_cast<double>(indices.second));
               itsModel->fix("beam");
               itsModel->fix("channel");
               sendModelToMaster();
           } else {
               // serial operation, just write the result
               if (validSolution()) {
                   writeModel();
               }
           }
      }
  }
  if (this->isMaster && this->isParallel) {
      const casa::uInt numberOfWorkUnits = nBeam() * nChan();
      for (casa::uInt chunk = 0; chunk < numberOfWorkUnits; ++chunk) {
           // asynchronously receive result from workers
           receiveModelFromWorker();
           if (validSolution()) {
               writeModel();
           }
      }
  }

  // Destroy the accessor, which should call syncCache and write the table out.
  ASKAPLOG_INFO_STR(logger, "Syncing the cached bandpass table to disk");
  itsSolAcc.reset();

}

/// @brief helper method to remove the dataset name from a parset
/// @details We deal with multiple measurement sets in a dit different
/// way from the other synthesis applications (they are not per worker
/// here). This method allows to remove the string with measurement sets
/// in the parset passed to base classes and replace it by empty string
/// @param[in] parset input parset
/// @return a copy without the dataset keyword
LOFAR::ParameterSet JacalBPCalibrator::emptyDatasetKeyword(const LOFAR::ParameterSet &parset)
{
  LOFAR::ParameterSet result(parset.makeSubset(""));
  result.replace("dataset",std::string());
  return result;
}


/// @brief verify that the current solution is valid
/// @details We use a special keywork 'invalid' in the model to
/// signal that a particular solution failed. for whatever reason.
/// This flag is checked to avoid writing the solution (which would
/// automatically set validity flag
/// @return true, if the current solution is valid
bool JacalBPCalibrator::validSolution() const
{
   if (itsModel) {
       return !itsModel->has("invalid");
   }
   return false;
}

/// @brief extract current beam/channel pair from the iterator
/// @details This method encapsulates interpretation of the output of itsWorkUnitIterator.cursor() for workers and
/// in the serial mode. However, it extracts the current beam and channel info out of the model for the master
/// in the parallel case. This is done because calibration data are sent to the master asynchronously and there is no
/// way of knowing what iteration in the worker they correspond to without looking at the data.
/// @return pair of beam (first) and channel (second) indices
std::pair<casa::uInt, casa::uInt> JacalBPCalibrator::currentBeamAndChannel() const
{
  if (this->isMaster && this->isParallel) {
      ASKAPDEBUGASSERT(itsModel);
      ASKAPDEBUGASSERT(itsModel->has("beam") && itsModel->has("channel"));
      const double beam = itsModel->scalarValue("beam");
      const double channel = itsModel->scalarValue("channel");
      ASKAPDEBUGASSERT((beam >= 0.) && (channel >= 0.));
      const std::pair<casa::uInt,casa::uInt> result(static_cast<casa::uInt>(beam), static_cast<casa::uInt>(channel));
      ASKAPDEBUGASSERT(result.first < nBeam());
      ASKAPDEBUGASSERT(result.second < nChan());
      return result;
  } else {
      const casa::IPosition cursor = itsWorkUnitIterator.cursor();
      ASKAPDEBUGASSERT(cursor.nelements() == 2);
      ASKAPDEBUGASSERT((cursor[0] >= 0) && (cursor[1] >= 0));
      const std::pair<casa::uInt,casa::uInt> result(static_cast<casa::uInt>(cursor[0]), static_cast<casa::uInt>(cursor[1]));
      ASKAPDEBUGASSERT(result.first < nBeam());
      ASKAPDEBUGASSERT(result.second < nChan());
      return result;
  }
}

#define BPCALIBRATOR_PARALLEL_BLOB_STREAM_VERSION 1

/// @brief send current model to the master
/// @details This method is supposed to be called from workers in the parallel mode and
/// sends the current results to the master rank
void JacalBPCalibrator::sendModelToMaster()
{


   /* FIXME - send this to the correct OUTPUT */
   /*
   ASKAPDEBUGTRACE("JacalBPCalibrator::sendModelToMaster");
   ASKAPLOG_DEBUG_STR(logger, "Sending results to the master");
   itsComms.notifyMaster();
   ASKAPDEBUGASSERT(itsModel);

   askapparallel::BlobOBufMW bobmw(itsComms, 0);
   LOFAR::BlobOStream out(bobmw);
   out.putStart("calmodel", BPCALIBRATOR_PARALLEL_BLOB_STREAM_VERSION);
   out << *itsModel;
   out.putEnd();
   bobmw.flush();
   */
   NEUtils::sendParams(itsModel,output("Model"));

}

/// @brief asynchronously receive model from one of the workers
/// @details This method is supposed to be used in the master rank in the parallel mode. It
/// waits until the result becomes available from any of the workers and then stores it
/// in itsModel.
void JacalBPCalibrator::receiveModelFromWorker()
{



   itsModel.reset(new scimath::Params);
   NEUtils::receiveParams(itsModel, input("Model"));
   /* FIXME: THis is the old receive once the above works - just remove this
   // wait for the notification
   const int source = itsComms.waitForNotification().first;
   ASKAPLOG_DEBUG_STR(logger, "Receiving results from rank "<<source);

   askapparallel::BlobIBufMW bibmw(itsComms, source);
   LOFAR::BlobIStream in(bibmw);
   const int version = in.getStart("calmodel");
   ASKAPASSERT(version == BPCALIBRATOR_PARALLEL_BLOB_STREAM_VERSION);
   in >> *itsModel;
   in.getEnd();
   */

}



/// @brief Calculate the normal equations (runs in workers)
/// @details Model, either image-based or component-based, is used in conjunction with
/// CalibrationME to calculate the generic normal equations.
void JacalBPCalibrator::calcNE()
{
  ASKAPDEBUGASSERT(this->isWorker);

  // create a new instance of the normal equations class
  boost::shared_ptr<scimath::GenericNormalEquations> gne(new scimath::GenericNormalEquations);
  itsNe = gne;

  // create the gridder too

  itsGridder = askap::synthesis::VisGridderFactory::make(this->itsParset);

  ASKAPDEBUGASSERT(itsNe);
  ASKAPDEBUGASSERT(itsGridder);

  // obtain details on the current iteration, i.e. beam and channel
  ASKAPDEBUGASSERT(itsWorkUnitIterator.hasMore());

  // first is beam, second is channel
  const std::pair<casa::uInt, casa::uInt> indices = currentBeamAndChannel();

  ASKAPDEBUGASSERT((measurementSets().size() == 1) || (indices.first < measurementSets().size()));

  const std::string ms = (measurementSets().size() == 1 ? measurementSets()[0] : measurementSets()[indices.first]);

  // actual computation
  calcOne(ms, indices.second, indices.first);
}

/// @brief helper method to invalidate curremt solution
void JacalBPCalibrator::invalidateSolution() {
   ASKAPDEBUGASSERT(itsModel);
   itsModel->add("invalid",1.);
   itsModel->fix("invalid");
}


/// @brief Solve the normal equations (runs in workers)
/// @details Parameters of the calibration problem are solved for here
void JacalBPCalibrator::solveNE()
{
  if (this->isWorker) {
      ASKAPLOG_INFO_STR(logger, "Solving normal equations");
      ASKAPDEBUGASSERT(itsNe);
      if (itsNe->unknowns().size() == 0) {
          ASKAPLOG_WARN_STR(logger, "Normal equations are empty - no valid data found, flagging the solution as bad");
          invalidateSolution();
          return;
      }
      casa::Timer timer;
      timer.mark();
      scimath::Quality q;
      ASKAPDEBUGASSERT(itsSolver);
      ASKAPDEBUGASSERT(itsModel);
      itsSolver->init();
      itsSolver->addNormalEquations(*itsNe);
      itsSolver->setAlgorithm("SVD");
      itsSolver->solveNormalEquations(*itsModel,q);
      ASKAPLOG_INFO_STR(logger, "Solved normal equations in "<< timer.real() << " seconds ");
      ASKAPLOG_INFO_STR(logger, "Solution quality: "<<q);

      const unsigned int minRank = this->parset().getUint32("minrank",15u);
      if (q.rank() < minRank) {
          ASKAPLOG_WARN_STR(logger, "Solution failed - minimum rank is "<<minRank<<", normal matrix has rank = "<<q.rank());
          invalidateSolution();
          return;
      }

      //wasim was here
      /*
      if (itsRefGain != "") {
          ASKAPLOG_INFO_STR(logger, "Rotating phases to have that of "<<itsRefGain<<" equal to 0");
          rotatePhases();
      }
      */
      if (itsRefGainXX != "") {
	      if (itsRefGainXX == itsRefGainYY){
		       ASKAPLOG_INFO_STR(logger, "Rotating both XX and YY phases to have that of "<<
                  itsRefGainXX<<" equal to 0");
	      } else{
		       ASKAPLOG_INFO_STR(logger, "Rotating XX phases to have that of "<<
                  itsRefGainXX<<" equal to 0 and YY phases to have that of "<<
                  itsRefGainYY<<" equal to 0");
	      }
          rotatePhases();
      }
  }
}

/// @brief Write the results (runs in master)
/// @details The solution (calibration parameters) is reported via solution accessor
void JacalBPCalibrator::writeModel(const std::string &)
{
  ASKAPDEBUGASSERT(this->isMaster);

  const std::pair<casa::uInt, casa::uInt> indices = currentBeamAndChannel();

  ASKAPLOG_DEBUG_STR(logger, "Writing results of the calibration for beam="<<indices.first<<" channel="<<indices.second);

  ASKAPCHECK(itsSolutionSource, "Solution source has to be defined by this stage");

  ASKAPASSERT(itsSolAcc);

  ASKAPDEBUGASSERT(itsModel);
  std::vector<std::string> parlist = itsModel->freeNames();
  for (std::vector<std::string>::const_iterator it = parlist.begin(); it != parlist.end(); ++it) {
       const casa::Complex val = itsModel->complexValue(*it);
       const std::pair<accessors::JonesIndex, casa::Stokes::StokesTypes> paramType =
             accessors::CalParamNameHelper::parseParam(*it);
       // beam is also coded in the parameters, although we don't need it because the data are partitioned
       // just cross-check it
       ASKAPDEBUGASSERT(static_cast<casa::uInt>(paramType.first.beam()) == indices.first);
       itsSolAcc->setBandpassElement(paramType.first, paramType.second, indices.second, val);
  }
}

/// @brief create measurement equation
/// @details This method initialises itsEquation with shared pointer to a proper type.
/// It uses internal flags to create a correct type (i.e. polarisation calibration or
/// just antenna-based gains). Parameters are passed directly to the constructor of
/// CalibrationME template.
/// @param[in] dsi data shared iterator
/// @param[in] perfectME uncorrupted measurement equation
void JacalBPCalibrator::createCalibrationME(const accessors::IDataSharedIter &dsi,
                const boost::shared_ptr<synthesis::IMeasurementEquation const> &perfectME)
{
   ASKAPDEBUGASSERT(itsModel);
   ASKAPDEBUGASSERT(perfectME);

   // it is handy to have a shared pointer to the base type because it is
   // not templated
   boost::shared_ptr<synthesis::PreAvgCalMEBase> preAvgME;
   // solve as normal gains (rather than bandpass) because only one channel is supposed to be selected
   // this also opens a possibility to use several (e.g. 54 = coarse resolution) channels to get one gain
   // solution which is then replicated to all channels involved. We can also add frequency-dependent leakage, if
   // tests show it is required (currently it is not in the calibration model)
   preAvgME.reset(new synthesis::CalibrationME<synthesis::NoXPolGain, synthesis::PreAvgCalMEBase>());
   ASKAPDEBUGASSERT(preAvgME);

   ASKAPDEBUGASSERT(dsi.hasMore());
   preAvgME->accumulate(dsi,perfectME);
   itsEquation = preAvgME;

   // this is just because we bypass setting the model for the first major cycle
   // in the case without pre-averaging
   itsEquation->setParameters(*itsModel);
}

/// @brief helper method to rotate all phases
/// @details This method rotates the phases of all gains in itsModel
/// to have the phase of itsRefGain exactly 0. This operation does
/// not seem to be necessary for SVD solvers, however it simplifies
/// "human eye" analysis of the results (otherwise the phase degeneracy
/// would make the solution different from the simulated gains).
/// @note The method throws exception if itsRefGain is not among
/// the parameters of itsModel
void JacalBPCalibrator::rotatePhases()
{
  // the intention is to rotate phases in worker (for this class)
  ASKAPDEBUGASSERT(this->isWorker);
  ASKAPDEBUGASSERT(itsModel);
  //wasim was here
 /*
  ASKAPCHECK(itsModel->has(itsRefGain), "phase rotation to `"<<itsRefGain<<
             "` is impossible because this parameter is not present in the model");
  casa::Complex  refPhaseTerm = casa::polar(1.f,-arg(itsModel->complexValue(itsRefGain)));
 */
  ASKAPCHECK(itsModel->has(itsRefGainXX), "phase rotation to `"<<itsRefGainXX<<
             "` is impossible because this parameter is not present in the model");
  ASKAPCHECK(itsModel->has(itsRefGainYY), "phase rotation to `"<<itsRefGainYY<<
             "` is impossible because this parameter is not present in the model");
  casa::Complex  refPhaseTermXX = casa::polar(1.f,-arg(itsModel->complexValue(itsRefGainXX)));
  casa::Complex  refPhaseTermYY = casa::polar(1.f,-arg(itsModel->complexValue(itsRefGainYY)));
  std::vector<std::string> names(itsModel->freeNames());
  for (std::vector<std::string>::const_iterator it=names.begin(); it!=names.end();++it)  {
       const std::string parname = *it;
       //wasim was here
       /*if (parname.find("gain") != std::string::npos) {
           itsModel->update(parname, itsModel->complexValue(parname) * refPhaseTerm);
       } */
       if (parname.find("gain.g11") != std::string::npos) {
           itsModel->update(parname, itsModel->complexValue(parname) * refPhaseTermXX);
       }
       else if (parname.find("gain.g22") != std::string::npos) {
           itsModel->update(parname, itsModel->complexValue(parname) * refPhaseTermYY);
       }
  }
}

/// @brief helper method to extract solution time from NE.
/// @details To be able to time tag the calibration solutions we add
/// start and stop times extracted from the dataset as metadata to normal
/// equations. It allows us to send these times to the master, which
/// ultimately writes the calibration solution. Otherwise, these times
/// could only be obtained in workers who deal with the actual data.
/// @return solution time (seconds since 0 MJD)
/// @note if no start/stop time metadata are present in the normal equations
/// this method returns 0.
double JacalBPCalibrator::solutionTime() const
{
  // use the earliest time corresponding to the data used to make this calibration solution
  // to tag the solution. A request for any latest time than this would automatically
  // extract this solution as most recent.
  ASKAPASSERT(itsNe);

  boost::shared_ptr<scimath::GenericNormalEquations> gne = boost::dynamic_pointer_cast<scimath::GenericNormalEquations>(itsNe);
  if (gne) {
      const scimath::Params& metadata = gne->metadata();
      if (metadata.has("min_time")) {
          return metadata.scalarValue("min_time");
      }
  }
  return 0.;
}

/// Calculate normal equations for one data set, channel and beam
/// @param[in] ms Name of data set
/// @param[in] chan channel to work with
/// @param[in] beam beam to work with
void JacalBPCalibrator::calcOne(const std::string& ms, const casa::uInt chan, const casa::uInt beam)
{
  casa::Timer timer;
  timer.mark();
  ASKAPLOG_INFO_STR(logger, "Calculating normal equations for " << ms <<" channel "<<chan<<" beam "<<beam);
  // First time around we need to generate the equation
  if (!itsEquation) {
      ASKAPLOG_INFO_STR(logger, "Creating measurement equation" );
      accessors::TableDataSource ds(ms, accessors::TableDataSource::DEFAULT, dataColumn());
      /// FIXME: Not sure I need this
      ///ds.configureUVWMachineCache(uvwMachineCacheSize(),uvwMachineCacheTolerance());

      accessors::IDataSelectorPtr sel=ds.createSelector();
      sel << this->parset();
      sel->chooseChannels(1,chan);
      sel->chooseFeed(beam);
      accessors::IDataConverterPtr conv=ds.createConverter();
      conv->setFrequencyFrame(casa::MFrequency::Ref(casa::MFrequency::TOPO), "Hz");
      conv->setDirectionFrame(casa::MDirection::Ref(casa::MDirection::J2000));
      // ensure that time is counted in seconds since 0 MJD
      conv->setEpochFrame();
      accessors::IDataSharedIter it=ds.createIterator(sel, conv);
      ASKAPCHECK(it.hasMore(), "No data seem to be available for channel "<<chan<<" and beam "<<beam);

      ASKAPCHECK(itsModel, "Initial assumption of parameters is not defined");

      if (!itsPerfectME) {
          ASKAPLOG_INFO_STR(logger, "Constructing measurement equation corresponding to the uncorrupted model");
          ASKAPCHECK(itsPerfectModel, "Uncorrupted model not defined");
          if (synthesis::SynthesisParamsHelper::hasImage(itsPerfectModel)) {
              ASKAPCHECK(!synthesis::SynthesisParamsHelper::hasComponent(itsPerfectModel),
                         "Image + component case has not yet been implemented");
              // have to create an image-specific equation
              boost::shared_ptr<synthesis::ImagingEquationAdapter> ieAdapter(new synthesis::ImagingEquationAdapter);
              ASKAPCHECK(itsGridder, "Gridder not defined");
              ieAdapter->assign<synthesis::ImageFFTEquation>(*itsPerfectModel, itsGridder);
              itsPerfectME = ieAdapter;
          } else {
              // model is a number of components, don't need an adapter here

              // it doesn't matter which iterator is passed below. It is not used
              boost::shared_ptr<synthesis::ComponentEquation>
                  compEq(new synthesis::ComponentEquation(*itsPerfectModel,it));
              itsPerfectME = compEq;
          }
      }
      // now we could've used class data members directly instead of passing them to createCalibrationME
      createCalibrationME(it,itsPerfectME);
      ASKAPCHECK(itsEquation, "Equation is not defined");
  } else {
      ASKAPLOG_INFO_STR(logger, "Reusing measurement equation" );
      // we need to update the model held by measurement equation
      // because it has been cloned at construction
      ASKAPCHECK(itsEquation, "Equation is not defined");
      ASKAPCHECK(itsModel, "Model is not defined");
      itsEquation->setParameters(*itsModel);
  }
  ASKAPCHECK(itsNe, "NormalEquations are not defined");
  itsEquation->calcEquations(*itsNe);
  ASKAPLOG_INFO_STR(logger, "Calculated normal equations for "<< ms << " channel "<<chan<<" beam " <<beam<<" in "<< timer.real()
                     << " seconds ");
}
void JacalBPCalibrator::data_written(const char *uid, const char *data, size_t n) {
    dlg_app_running();
}

void JacalBPCalibrator::drop_completed(const char *uid, drop_status status) {

    dlg_app_done(APP_FINISHED);
}



} // namespace askap
