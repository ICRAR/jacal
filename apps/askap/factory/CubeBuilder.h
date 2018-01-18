/// @file CubeBuilder.h
/// @brief Build an output image cube
/// @details This drop will be able to build an output cube of any format
/// supported by ASKAPSoft



#ifndef ASKAP_FACTORY_CUBEBUILDER_H
#define ASKAP_FACTORY_CUBEBUILDER_H

#include <daliuge/DaliugeApplication.h>



#include <boost/shared_ptr.hpp>

// LOFAR ParameterSet
#include <Common/ParameterSet.h>





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

        virtual int init(const char ***arguments);

        virtual int run();

        virtual void data_written(const char *uid, const char *data, size_t n);

        virtual void drop_completed(const char *uid, drop_status status);



        private:


            //! @brief Parameter set
            //! @details key value list of configuration options
            LOFAR::ParameterSet itsParset;

          






    };

} // namespace askap


#endif //
