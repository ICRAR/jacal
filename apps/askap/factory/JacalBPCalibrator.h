/// @file
///
/// JacalBPCalibrator: part of the specialised tool to do optimised bandpass calibration with
/// limited functionality.
///
/// @copyright (c) 2018 CSIRO
/// Australia Telescope National Facility (ATNF)
/// Commonwealth Scientific and Industrial Research Organisation (CSIRO)
/// PO Box 76, Epping NSW 1710, Australia
/// atnf-enquiries@csiro.au
///
/// This file is part of the JACAL software distribution.
///
///
///
/// @author Stephen Ord <stephen.ord@csiro.au>
///
#ifndef ASKAP_FACTORY_BP_CALIBRATOR_H
#define ASKAP_FACTORY_BP_CALIBRATOR_H

#include "rename.h"

// own includes
#include <daliuge/DaliugeApplication.h>
#include "NEUtils.h"

// askap ones
#include <askapparallel/AskapParallel.h>
#include <parallel/MEParallelApp.h>
#include <Common/ParameterSet.h>
#include <gridding/IVisGridder.h>
#include <measurementequation/IMeasurementEquation.h>
#include <dataaccess/SharedIter.h>
#include <calibaccess/ICalSolutionSource.h>
#include <utils/MultiDimPosIter.h>


// std includes
#include <utility>

// boost includes
#include <boost/shared_ptr.hpp>

namespace askap
{
    /*!
    * \brief
    * \details
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
    * \param[out] port/Model/scimath::Params
    *     /~English
    *     /~Chinese
    * \par EAGLE_END
    */
    class JacalBPCalibrator : public DaliugeApplication
    {
      public:

        typedef boost::shared_ptr<JacalBPCalibrator> ShPtr;

        JacalBPCalibrator(dlg_app_info *raw_app);

        static inline std::string ApplicationName() { return "JacalBPCalibrator";}

        static DaliugeApplication::ShPtr createDaliugeApplication(dlg_app_info *raw_app);

        virtual int init(const char ***arguments);

        virtual int run();

        virtual void data_written(const char *uid, const char *data, size_t n);

        virtual void drop_completed(const char *uid, drop_status status);

        // Parameter set
        inline const LOFAR::ParameterSet& parset() const { return itsParset;}

        // set the Meaasurement Set Vector

        inline void setMeasurementSets(const std::vector<std::string>& ms) { itsMs = ms;}

        inline const std::vector<std::string>& measurementSets() const { return itsMs;}



      protected:

      // virtual methods of the abstract base, define them as protected because they
      // are no longer supposed to be called directly from the application level

      /// @brief Calculate the normal equations (runs in workers)
      /// @details Model, either image-based or component-based, is used in conjunction with
      /// CalibrationME to calculate the generic normal equations.
      virtual void calcNE();

      /// @brief Solve the normal equations (runs in workers)
      /// @details Parameters of the calibration problem are solved for here
      virtual void solveNE();

      /// @brief Write the results (runs in master)
      /// @details The solution (calibration parameters) is reported via solution accessor
      /// @param[in] postfix a string to be added to the file name (unused in this class)
	    virtual void writeModel(const std::string &postfix = std::string());

      /// @brief create measurement equation
      /// @details This method initialises itsEquation with shared pointer to a proper type.
      /// It uses internal flags to create a correct type (i.e. polarisation calibration or
      /// just antenna-based gains). Parameters are passed directly to the constructor of
      /// CalibrationME template.
      /// @param[in] dsi data shared iterator
      /// @param[in] perfectME uncorrupted measurement equation
      void createCalibrationME(const accessors::IDataSharedIter &dsi,
                const boost::shared_ptr<synthesis::IMeasurementEquation const> &perfectME);

      /// @brief helper method to rotate all phases
      /// @details This method rotates the phases of all gains in itsModel
      /// to have the phase of itsRefGain exactly 0. This operation does
      /// not seem to be necessary for SVD solvers, however it simplifies
      /// "human eye" analysis of the results (otherwise the phase degeneracy
      /// would make the solution different from the simulated gains).
      /// @note The method throws exception if itsRefGain is not among
      /// the parameters of itsModel
      void rotatePhases();

      /// @brief helper method to extract solution time from NE.
      /// @details To be able to time tag the calibration solutions we add
      /// start and stop times extracted from the dataset as metadata to normal
      /// equations. It allows us to send these times to the master, which
      /// ultimately writes the calibration solution. Otherwise, these times
      /// could only be obtained in workers who deal with the actual data.
      /// @return solution time (seconds since 0 MJD)
      /// @note if no start/stop time metadata are present in the normal equations
      /// this method returns 0.
      double solutionTime() const;

  private:
      /// @brief helper method to remove the dataset name from a parset
      /// @details We deal with multiple measurement sets in a dit different
      /// way from the other synthesis applications (they are not per worker
      /// here). This method allows to remove the string with measurement sets
      /// in the parset passed to base classes and replace it by empty string
      /// @param[in] parset input parset
      /// @return a copy without the dataset keyword
      static LOFAR::ParameterSet emptyDatasetKeyword(const LOFAR::ParameterSet &parset);


      /// @brief read the model from parset file and populate itsPerfectModel
      /// @details This method is common between several classes and probably
      /// should be pushed up in the class hierarchy
      inline void readModels() const { NEUtils::readModels(itsParset,itsPerfectModel); }

      /// @brief number of antennas to solve for
      /// @return number of antennas to solve for
      inline casacore::uInt nAnt() const { return parset().getInt32("nAnt", 36); }

      /// @brief number of beams to solve for
      /// @return number of beams to solve for
      inline casacore::uInt nBeam() const { return parset().getInt32("nBeam", 1); }

      /// @brief number of channels to solve for
      /// @return number of channels to solve for
      inline casacore::uInt nChan() const { return parset().getInt32("nChan", 304); }


      /// @brief number of channels to solve for
      /// @return number of channels per rank
      inline casacore::uInt nChanPerRank() const { return parset().getInt32("nChanPerRank", 54); }

      inline const std::string dataColumn() const { return this->itsParset.getString("datacolumn", "DATA");}

      /// @brief extract current beam/channel pair from the iterator
      /// @details This method encapsulates interpretation of the output of itsWorkUnitIterator.cursor() for workers and
      /// in the serial mode. However, it extracts the current beam and channel info out of the model for the master
      /// in the parallel case. This is done because calibration data are sent to the master asynchronously and there is no
      /// way of knowing what iteration in the worker they correspond to without looking at the data.
      /// @return pair of beam (first) and channel (second) indices
      std::pair<casacore::uInt, casacore::uInt> currentBeamAndChannel() const;

      /// @brief helper method to invalidate current solution
      void invalidateSolution();

      /// @brief verify that the current solution is valid
      /// @details We use a special keywork 'invalid' in the model to
      /// signal that a particular solution failed. for whatever reason.
      /// This flag is checked to avoid writing the solution (which would
      /// automatically set validity flag
      /// @return true, if the current solution is valid
      bool validSolution() const;

      /// Calculate normal equations for one data set, channel and beam
      /// @param[in] ms Name of data set
      /// @param[in] chan channel to work with
      /// @param[in] beam beam to work with
      void calcOne(const std::string& ms, const casacore::uInt chan, const casacore::uInt beam);

      /// @brief send current model to the master
      /// @details This method is supposed to be called from workers in the parallel mode and
      /// sends the current results to the master rank
      void sendModelToMaster();

      /// @brief asynchronously receive model from one of the workers
      /// @details This method is supposed to be used in the master rank in the parallel mode. It
      /// waits until the result becomes available from any of the workers and then stores it
      /// in itsModel.
      void receiveModelFromWorker();
      /// @brief asynchronously receive model from one of the workers
      /// @details This method is supposed to be used in the master rank in the parallel mode. It
      /// waits until the result becomes available from a particular input and then stores it
      /// in itsModel.
      void receiveModelFromWorker(int input);

      /// uncorrupted model
      askap::scimath::Params::ShPtr itsPerfectModel;

      /// @brief reference antenna (index)
      /// @details Negative number means no referencing required
      int itsRefAntenna;

      /// @brief name of the parameter taken as a reference
      /// @details empty string means no referencing is required
      //wasim was here
      /*
      std::string itsRefGain;
      */
      std::string itsRefGainXX;
      std::string itsRefGainYY;

      /// @brief solution source to store the result
      /// @details This object is initialised by the master. It stores the solution
      /// in parset file, casa table or a database.
      boost::shared_ptr<accessors::ICalSolutionSource> itsSolutionSource;

      

      /// @brief shared pointer to measurement equation correspondent to the perfect model
      /// @details It is handy to store the perfect measurement equation, so it is not
      /// recreated every time for each solution interval.
      boost::shared_ptr<synthesis::IMeasurementEquation const> itsPerfectME;

      /// @brief iterator over channels and beams
      /// @details This class allows us to split work domain between a number of workers (=iteration chunks)
      scimath::MultiDimPosIter itsWorkUnitIterator;

      /// @brief solution ID to work with
      /// @details This field should only be used if itsSolutionIDValid is true
      long itsSolutionID;

      /// @brief solution ID validity flag
      bool itsSolutionIDValid;

      // Parameter set
      LOFAR::ParameterSet itsParset;

      // The channel number we are Solving
      int itsChan;

      // The beam we are solving
      int itsBeam;

      // Bool flag for whether we are the Master or Worker. I've kept some of the MPIComms ideas
      // probably not ideal - but it gets us into the drops refPhaseTerm
      bool isMaster;
      bool isWorker;
      bool isParallel;

      // I should use these to make the drop smaller
      casacore::IPosition freqInterval;
      casacore::IPosition timeInterval;

      // the Measurement sets

      std::vector<std::string> itsMs;

      // its Solver
      askap::scimath::Solver::ShPtr itsSolver;

      askap::scimath::Equation::ShPtr itsEquation;

      askap::scimath::Params::ShPtr itsModel;

      askap::scimath::INormalEquations::ShPtr itsNe;

      askap::synthesis::IVisGridder::ShPtr itsGridder;

      vector<int> itsModelInputs;




    };

  }

#endif // #ifndef ASKAP_SYNTHESIS_BP_CALIBRATOR_PARALLEL_H
