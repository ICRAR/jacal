
JACAL_HOME=/group/pawsey0245/software/jacal

source /group/pawsey0245/software/daliuge/bin/activate
dlg unroll-and-partition -L $JACAL_HOME/deploy/athena/askap_LoadVis_athena.json\
 | dlg map -N localhost,localhost -i 1 | dlg submit -H localhost -p 8001
