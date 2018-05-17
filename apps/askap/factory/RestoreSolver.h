/// @file RestoreSolver.h

/// @brief Solve an Normal Equation provided by a Daliuge Drop
/// @details We will simply load in a NormalEquation from
/// a daliuge drop and solve it via a minor cycle deconvolution.




#ifndef ASKAP_FACTORY_RestoreSolver_H
#define ASKAP_FACTORY_RestoreSolver_H

#include <daliuge/DaliugeApplication.h>
#include <factory/NEUtils.h>

#include <casacore/casa/Quanta/MVDirection.h>

#include <boost/shared_ptr.hpp>

#include <fitting/Params.h>
#include <fitting/Solver.h>

// params helpers
#include <measurementequation/SynthesisParamsHelper.h>
#include <measurementequation/ImageParamsHelper.h>

namespace askap {

  /// @brief Implements an ASKAP Solver
  /// @details This takes a configuration and a set of normal equations and uses the Solver requested in
  /// in the ParameterSet to produce an ouput model.

    class RestoreSolver : public DaliugeApplication

    {

    public:

        typedef boost::shared_ptr<RestoreSolver> ShPtr;

        RestoreSolver(dlg_app_info *raw_app);

        static inline std::string ApplicationName() { return "RestoreSolver";}

        virtual ~RestoreSolver();

        static DaliugeApplication::ShPtr createDaliugeApplication(dlg_app_info *raw_app);

        virtual int init(const char ***arguments);

        virtual int run();

        virtual void data_written(const char *uid, const char *data, size_t n);

        virtual void drop_completed(const char *uid, drop_status status);



        private:

          /// The model
          scimath::Params::ShPtr itsModel;

          // Parameter set
          LOFAR::ParameterSet itsParset;

          // The Normal Equations

          scimath::ImagingNormalEquations::ShPtr itsNe;

          // Its Solver

          scimath::Solver::ShPtr itsSolver;

            // utility to build an Imaging Normal Equation from a parset
            // void buildNE();

            // these are the steps required by buildNE




    };

} // namespace askap


#endif //
