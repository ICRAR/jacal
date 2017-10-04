// expose the member functions to the outside world as C functions
// If Daliuge changes its API - you will have to change these functions
// but hopefully all the issues will be hidden behind the structures

#include<iostream>

#include<daliuge/DaliugeApplication.h>
#include<factory/DaliugeApplicationFactory.h>
#include<factory/Interface.h>

#include<string.h>


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
    askap::DaliugeApplication::ShPtr thisApp = askap::DaliugeApplicationFactory::make(app->appname);
    return thisApp->init(app, arguments);
}
int run(dlg_app_info *app) {
    askap::DaliugeApplication::ShPtr thisApp = askap::DaliugeApplicationFactory::make(app->appname);
    return thisApp->run(app);
}
void data_written(dlg_app_info *app, const char *uid,
    const char *data, size_t n) {
        askap::DaliugeApplication::ShPtr thisApp = askap::DaliugeApplicationFactory::make(app->appname);
        thisApp->data_written(app, uid, data, n);
    }
    void drop_completed(dlg_app_info *app, const char *uid,
        drop_status status) {
            askap::DaliugeApplication::ShPtr thisApp = askap::DaliugeApplicationFactory::make(app->appname);
            thisApp->drop_completed(app, uid, status);
        }
