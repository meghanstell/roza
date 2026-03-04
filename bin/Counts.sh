
# COUNT FOR WRF2D FILES
for year in `seq 1979 2022`; do 
    _in_count=$(find /glade/campaign/collections/rda/data/d559000 -name "wrf2d_d01_${year}*.nc" | grep -E "wrf2d_d01_${year}-(01|02|03|04|11|12)-.*.nc" | wc -l)
    _out_count=$(find /glade/derecho/scratch/meghan/Roza/data/CONUS404/cut -name "wrf2d_d01_${year}*.nc" | wc -l)
    _in_ii=$(( $_in_count ))
    _out_ii=$(( $_out_count ))
    _diff=$(( $_in_ii - $_out_ii ))
    _pcnt=$(echo "scale=2 ; $_out_ii*100 / $_in_count" | bc)
    echo "2D Year: ${year}, InputCount: ${_in_count}, OutputCount: ${_out_count}, Diff: ${_diff}, Percent Complete: ${_pcnt}%"
done



# COUNT FOR WRF3D FILES
# for year in `seq 1979 2022`; do 
for year in `seq 2016 2022`; do 
    _in_count=$(find /glade/campaign/collections/rda/data/d559000 -name "wrf3d_d01_${year}*.nc" | grep -E "wrf3d_d01_${year}-(01|02|03|04|11|12)-.*.nc" | wc -l)
    _out_count=$(find /glade/derecho/scratch/meghan/Roza/data/CONUS404/cut -name "wrf3d_d01_${year}*.nc" | wc -l)
    _in_ii=$(( $_in_count ))
    _out_ii=$(( $_out_count ))
    _diff=$(( $_in_ii - $_out_ii ))
    _pcnt=$(echo "scale=2 ; $_out_ii*100 / $_in_count" | bc)
    echo "3D Year: ${year}, InputCount: ${_in_count}, OutputCount: ${_out_count}, Diff: ${_diff}, Percent Complete: ${_pcnt}%"
done
