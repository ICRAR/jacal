/// @file LoadParset.h

/// @brief Load a LOFAR Parameter Set in the DaliugeApplication Framework
/// @details The fitst ASKAP example in the Daliuge framework that actually
/// performs an ASKAP related task.
/// We load a parset into memory from either a file or another Daliuge drop_status

#ifndef ASKAP_FACTORY_LOADPARSET_H
#define ASKAP_FACTORY_LOADPARSET_H

#include <daliuge/DaliugeApplication.h>

#include <boost/shared_ptr.hpp>



namespace askap {
    /// @brief Loads a configuration
    /// @details Loads a configuration from a file drop and generates a LOFAR::ParameterSet
    class LoadParset : public DaliugeApplication

    {

    public:

        typedef boost::shared_ptr<LoadParset> ShPtr;

        LoadParset();

        static inline std::string ApplicationName() { return "LoadParset";}

        virtual ~LoadParset();

        static DaliugeApplication::ShPtr createDaliugeApplication(const std::string &name);

        virtual int init(dlg_app_info *app, const char ***arguments);

        virtual int run(dlg_app_info *app);

        virtual void data_written(dlg_app_info *app, const char *uid,
            const char *data, size_t n);

        virtual void drop_completed(dlg_app_info *app, const char *uid,
            drop_status status);

        private:

    };

} // namespace askap


#endif //
