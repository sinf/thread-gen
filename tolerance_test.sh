#!/bin/sh

set -x
mkdir -pv tolerance_test

tol_radial="10 30 60 100"
tol_layer="50 70 90 110 150 170 200 220"

for tr in $tol_radial; do
	for tl in $tol_layer; do
		./thread.py -tm6 -x$tl -y$tr -z -i -s200 -l5 "tolerance_test/m6-${tr}-${tl}.stl"
	done
done

