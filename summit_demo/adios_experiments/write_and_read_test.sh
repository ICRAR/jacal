#/bin/bash

mpirun -n 10 python parallel_writer_test.py
if [ ! -d my_table ]; then
	echo "No table written, failing"
	exit 1
fi

min=`taql 'SELECT gmin(MY_FLOAT_COLUMN) FROM my_table' | grep '^0$'`
max=`taql 'SELECT gmax(MY_FLOAT_COLUMN) FROM my_table' | grep '^99$'`
echo "Min/Max: $min $max"

if [ $min = 0 -a $max = 99 ]; then
	echo "All is good"
	exit 0
fi

echo "Invalid values for min/max"
exit 1
