/// @file OutputParams.h

/// @brief Solve an Normal Equation provided by a Daliuge Drop
/// @details We will simply load in a NormalEquation from
/// a daliuge drop and solve it via a minor cycle deconvolution.




#ifndef ASKAP_FACTORY_OutputParams_H
#define ASKAP_FACTORY_OutputParams_H

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
  /// @brief Outputs the Params class as images
  /// @details This drop actually generates the output images based upon the contents of the Params object
  
    class OutputParams : public DaliugeApplication

    {

    public:

        typedef boost::shared_ptr<OutputParams> ShPtr;

        OutputParams();

        static inline std::string ApplicationName() { return "OutputParams";}

        virtual ~OutputParams();

        static DaliugeApplication::ShPtr createDaliugeApplication(const std::string &name);

        virtual int init(dlg_app_info *app, const char ***arguments);

        virtual int run(dlg_app_info *app);

        virtual void data_written(dlg_app_info *app, const char *uid,
            const char *data, size_t n);

        virtual void drop_completed(dlg_app_info *app, const char *uid,
            drop_status status);



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
