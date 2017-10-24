// expose the member functions to the outside world as C functions
// If Daliuge changes its API - you will have to change these functions
// but hopefully all the issues will be hidden behind the structures

#include<iostream>

#include<daliuge/DaliugeApplication.h>
#include<factory/DaliugeApplicationFactory.h>
#include<factory/Interface.h>

#include<string.h>

struct DaliugeApplicationWrapper {
	askap::DaliugeApplication::ShPtr daliuge_app;
};

static inline
askap::DaliugeApplication::ShPtr unpack(dlg_app_info *app) {
	return static_cast<DaliugeApplicationWrapper *>(app->data)->daliuge_app;
}

//! @file The actual interface functions
//! @details These are the C functions that are exposed to the Daliuge pipeline. Everytime the Dynlib is unsigned
//! it has a name which is one of the Daliuge applications supported by the factory.
//! the process is simple. It checks the app->name for the name of the application then instantiates
//! the class for that name - then runs its method.

int init(dlg_app_info *app, const char ***arguments) {
    // this means we have to instantiate an application
    // and call its init
    bool got_name = false;
    while (1) {

        // Sentinel
        if (*arguments == NULL) {
            break;
        }

        const char **param = arguments[0];
        if (strcmp(param[0], "name") == 0) {
            app->appname = strdup(param[1]);
            got_name = true;
            std::cout << "init - Found " << app->appname <<  " in params" << std::endl;
        }

        arguments++;
    }
    if (got_name == false) {
        app->appname = strdup("LoadParset");
    }
    // need to set the app->appname here .... from the arguments ....
    askap::DaliugeApplication::ShPtr thisApp = askap::DaliugeApplicationFactory::make(app);

    // Save the pointer in the raw dlg_app_info for later retrieval
    auto wrapper = new DaliugeApplicationWrapper();
    wrapper->daliuge_app = thisApp;
    app->data = wrapper;

    return thisApp->init(arguments);
}

int run(dlg_app_info *app) {
	unpack(app)->run();
}

void data_written(dlg_app_info *app, const char *uid, const char *data, size_t n) {
	unpack(app)->data_written(uid, data, n);
}

void drop_completed(dlg_app_info *app, const char *uid, drop_status status) {
	unpack(app)->drop_completed(uid, status);
}
