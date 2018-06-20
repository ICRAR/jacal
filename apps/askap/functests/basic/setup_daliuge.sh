#cleanup

killall dlg

if [ $# -gt 0 ]; then
    cd $1
    source activate daliuge
    cd $OLDPWD
elif [ -n "${DALIUGE_VENV}" ]; then
    source ${DALIUGE_VENV}/bin/activate
else
    echo "Assuming dlg is already available"
fi

dlg nm -v --no-dlm &
dlg dim -N localhost &
