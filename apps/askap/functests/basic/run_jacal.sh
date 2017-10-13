dlg unroll-and-partition -L ${WORKSPACE}/jacal/apps/askap/functests/basic//basic_image.json | dlg map  -N localhost,localhost -i 1 | dlg submit -H localhost -p 8001
