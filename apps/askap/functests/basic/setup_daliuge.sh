#cleanup

killall dlg

if [ $# -gt 0 ]; then
    cd $1
    source activate daliuge
    cd $WORKSPACE
else
    if [ -e ${WORKSPACE}/daliuge_env/bin/activate ]; then
        source ${WORKSPACE}/daliuge_env/bin/activate
    else
        echo "Cannot find ${WORKSPACE}/daliuge_env/bin/activate"
        exit -1
    fi
fi
cd $RUNDIR
dlg nm -v --no-dlm &
dlg dim -N localhost &
