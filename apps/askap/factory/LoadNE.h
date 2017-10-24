/// @file LoadNE.h

/// @brief Load a NormalEquation from a daliuge drop
/// @details We will simply load in a NormalEquation from
/// a daliuge drop and output the image. This simply tests
/// the NE interface to the daliuge memory drop.



#ifndef ASKAP_FACTORY_LOADNE_H
#define ASKAP_FACTORY_LOADNE_H

#include <daliuge/DaliugeApplication.h>

#include <casacore/casa/Quanta/MVDirection.h>

#include <boost/shared_ptr.hpp>



#include <fitting/Params.h>



namespace askap {
    /// @brief Example calss that simply loads Normal Equations from a drop
    /// @details Just accepts the drop
    class LoadNE : public DaliugeApplication

    {

    public:

        typedef boost::shared_ptr<LoadNE> ShPtr;

        LoadNE(dlg_app_info *raw_app);

        static inline std::string ApplicationName() { return "LoadNE";}

        virtual ~LoadNE();

        static DaliugeApplication::ShPtr createDaliugeApplication(dlg_app_info *raw_app);

        virtual int init(const char ***arguments);

        virtual int run();

        virtual void data_written(const char *uid, const char *data, size_t n);

        virtual void drop_completed(const char *uid, drop_status status);



        private:



            // utility to build an Imaging Normal Equation from a parset
            // void buildNE();

            // these are the steps required by buildNE




    };

} // namespace askap


#endif //
