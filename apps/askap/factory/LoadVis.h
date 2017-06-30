/// @file LoadVis.h

/// @brief Load a CASA Measurement Set in the DaliugeApplication Framework
/// @details We will build on the LoadParset structure - but use the contents
/// of the parset to load a measurement set.



#ifndef ASKAP_FACTORY_LOADVIS_H
#define ASKAP_FACTORY_LOADVIS_H

#include <daliuge/DaliugeApplication.h>

#include <boost/shared_ptr.hpp>



namespace askap {

    class LoadVis : public DaliugeApplication

    {

    public:

        typedef boost::shared_ptr<LoadVis> ShPtr;

        LoadVis();

        static inline std::string ApplicationName() { return "LoadVis";}

        virtual ~LoadVis();

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
