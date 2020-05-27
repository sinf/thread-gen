#!/bin/sh
mkdir -p ex
for m in M3 M4 M5 M6; do
	for l in 20 30 40; do
		./thread.py -t $m -l $l ex/${m}x${l}.stl
		./thread.py -t $m -l $l -i ex/${m}x${l}i.stl
	done
done

