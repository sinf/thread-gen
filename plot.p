
set style line 1 \
    linecolor rgb '#0060ad' \
    linetype 1 linewidth 2 \
    pointtype 7 pointsize 0.5

set size 1.0, 1.0
set terminal postscript portrait enhanced mono dashed lw 1 "Helvetica" 14 
set output "vertices.ps"

plot 'vertices.txt' with linespoints linestyle 1


