if [ $# -gt 0 ]; then
    echo "have argument"
    source activate daliuge
else
    source ${WORKSPACE}/daliuge_env/bin/activate
fi

dlg nm -v --no-dlm &
dlg dim -N localhost &
dlg lgweb -d ${WORKSPACE}/jacal/apps/askap/functests/basic  -t /tmp &

