#!/bin/sh

set -x
mkdir -pv tolerance_test
rm -f tolerance_test/*.stl

eval "$(head -n2 tolerance_test.scad | sed 's/\[/"/;s/\]/"/;s/,//g')"

for tr in $tol_radial; do
	for tl in $tol_layer; do
		./thread.py -tm6 -x$tl -y$tr -z -i -s200 -l5 "tolerance_test/m6-${tr}-${tl}.stl"
	done
done

