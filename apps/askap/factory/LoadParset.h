/// @file LoadParset.h

/// @brief Load a LOFAR Parameter Set in the DaliugeApplication Framework
/// @details The fitst ASKAP example in the Daliuge framework that actually
/// performs an ASKAP related task.
/// We load a parset into memory from either a file or another Daliuge drop_status

#ifndef ASKAP_FACTORY_LOADPARSET_H
#define ASKAP_FACTORY_LOADPARSET_H

#include "rename.h"

#include <daliuge/DaliugeApplication.h>

#include <boost/shared_ptr.hpp>



namespace askap {
    /*!
    * \brief Loads a configuration
    * \details Loads a configuration from a file drop and generates a LOFAR::ParameterSet
    * \par EAGLE_START
    * \param gitrepo $(GIT_REPO)
    * \param version $(PROJECT_VERSION)
    * \param category DynlibApp
    * \param[in] port/Config/LOFAR::ParameterSet
    *     /~English ParameterSet descriptor for the image solver
    *     /~Chinese
    * \param[out] port/Config/LOFAR::ParameterSet
    * \param[out] port/Config/LOFAR::ParameterSet
    * \par EAGLE_END
    */
    class LoadParset : public DaliugeApplication
    {
    public:

        typedef boost::shared_ptr<LoadParset> ShPtr;

        LoadParset(dlg_app_info *raw_app);

        static inline std::string ApplicationName() { return "LoadParset";}

        virtual ~LoadParset();

        static DaliugeApplication::ShPtr createDaliugeApplication(dlg_app_info *raw_app);

        virtual int init(const char ***arguments);

        virtual int run();

        virtual void data_written(const char *uid, const char *data, size_t n);

        virtual void drop_completed(const char *uid, drop_status status);

        private:

    };

} // namespace askap


#endif //
