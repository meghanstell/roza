# Roza Project Data Science

- [ ] Re-cut domain to: -122.5,-119, 45.5, 47.9
- [ ] South/North: 759,797 and West/East: 214,295.
- [ ] Make seeding variables with new domain data
- [ ] Plot LWC/temp/frequency maps for Roza -monthly and seeding season 

| ---------------- BOUNDS ------------------ |
|  Frame   |   Lower-Left   |   Upper-Right  |
| -------- | -------------- | -------------- |
| Lon, Lat | (-122.5, 45.5) | (-119.0, 47.9) |
| ii , jj  | ( 200  , 720 ) | ( 320  , 850 ) |
| -------- | -------------- | -------------- |

<!-- ## Cut A New Domain from USGS CONUS404
```bash
## Input : /glade/campaign/collections/rda/data/d559000
## Output: /glade/derecho/scratch/meghan/Roza/data/CONUS404/cut
./bin/make_3d_analysis_files_roza.sh

## Input : /glade/derecho/scratch/meghan/Roza/data/CONUS404/cut
## Output: /glade/derecho/scratch/meghan/Colorado/data/CONUS404/Colorado/SeedingVariables
ncl "year=2003" "mm=03" bin/output_seedingcriteria_CC.ncl

## Input : /glade/derecho/scratch/meghan/Colorado/data/CONUS404/Colorado/sv
## Input : /glade/derecho/scratch/meghan/Colorado/data/CONUS404/Colorado/SeedingVariables
## Output: /glade/derecho/scratch/meghan/Colorado/SynopticFinalProject/data/Colorado/sv/cat
./bin/data_cut_cc.sh
``` -->

## Cut CONUS WRF Output to Resized Domain


```bash
qsub -v YEAR=1979 ./bin/submit_output_seedingcriteria_IDWR.sh
for year in `seq 1979 2022`; do
    qsub -v YEAR=${year} ./bin/submit_output_seedingcriteria_IDWR.sh
done
```



## Calculate Seeding Criteria Files from Resized WRF Output Files


```bash
qsub -v YEAR=1979 ./bin/submit_sv_calcs.sh
for year in `seq 1980 2022`; do 
    qsub -v YEAR=${year} ./bin/submit_sv_calcs.sh
done
```


## Concatenate Seeding Criteria Files

```bash
# Use QSUB to concatenate Seeding_criteria_*.nc 
# into aggregate SV*.nc files for Seeding Criteria Analysis
#
# data_root=/glade/derecho/scratch/meghan/Roza/data/CONUS404

## Concatenate all 
##      ${data_dir}/SeedingVariables/Seeding_criteria_${year}-${month}*.nc
##            
## into ${data_dir}/cat/monthly/SV_${year}_${month}.nc files
##
## Input : ${data_dir}/SeedingVariables
## Output: ${data_dir}/cat/monthly/SV_${year}_${month}.nc
for year in `seq 1979 2022`; do 
    qsub -v YEAR=${year} ./bin/submit_cat_sc_year_month.sh
done


# Wait for all the submitted jobs above to complete before proceeding

## Cat all ${data_dir}/cat/monthly/SV_${year}_${month}.nc
##    into ${data_dir}/cat/SV_${month}.nc files
##
## Input : ${data_dir}/cat/monthly/SV_${year}_${month}.nc
## Output: ${data_dir}/cat/SV_${month}.nc
for month in "11" "12" "01" "02" "03" "04"; do 
    qsub -v MONTH=${month} ./bin/submit_cat_sc_month.sh
done



# Wait for all the submitted jobs above to complete before proceeding

## Cat all ${data_dir}/cat/SV_${month}.nc
##    into ${data_dir}/cat/SV_Season.nc
##
## Input : ${data_dir}/cat/SV_${month}.nc
## Output: ${data_dir}/cat/SV_Season.nc
qsub ./bin/submit_cat_sc_season.sh

```
---------------------

## Create Maps

### Create Monthly Maps

Data is aggregated and plotted for the individual months of interest (November - April) over the entire dataset duration

- [x] As_LWC (mean)
- [x] Gs_LWC (mean)
- [x] As_Tc (mean)
- [x] Gs_TC (mean)
- [x] Ground Frequency of Seedable Conditions
    - Where ( -18 < Gs_TC < -6 ) && ( Gs_LWC > 0.01 )
- [x] Air Frequency of Seedable Conditions
    - Where ( -18 < As_TC < -6 ) && ( As_LWC > 0.01 )

All of the above maps are created by running:
```bash
qsub ./bin/submit_monthly_maps.sh
```

- [x] Wind Contour Animation (Monthly)
    - [x] 700mb Wind Contour Animation (Monthly)
    - [x] 850mb Wind Contour Animation (Monthly)

The monthly-scoped Wind Contour Animations are created buy running:
```bash
qsub ./bin/submit_monthly_wind.sh
```


### Create Season Maps

Data is aggregated and plotted for all combined months of interest (November - April) for all years in the dataset (e.g., water years 1980-2022)

- [x] As_LWC (mean)
- [x] Gs_LWC (mean)
- [x] As_Tc (mean)
- [x] Gs_TC (mean)
- [x] Ground Frequency of Seedable Conditions
    - Where ( -18 < Gs_TC < -6 ) && ( Gs_LWC > 0.01 )
- [x] Air Frequency of Seedable Conditions
    - Where ( -18 < As_TC < -6 ) && ( As_LWC > 0.01 )

All of the above maps are created by running:
```bash
qsub ./bin/submit_season_maps.sh
```

- [x] Wind Contour Animations (Season)
    - [x] 700mb Wind Contour Animation (Season)
    - [x] 850mb Wind Contour Animation (Season)

The monthly-scoped Wind Contour Animations are created buy running:
```bash
qsub ./bin/submit_season_wind.sh
```


## Validate the SV files are built correctly

```bash
# Validate the SV_${year}_${month}.nc files are built correctly
for year in `seq 1979 2022`; do 
    for month in "11" "12" "01" "02" "03" "04"; do 
        _in_count=$(find /glade/derecho/scratch/meghan/Roza/data/CONUS404/SeedingVariables -name "Seeding_criteria_${year}-${month}*.nc" | wc -l)
        _out_count=$(ncdump -h /glade/derecho/scratch/meghan/Roza/data/CONUS404/cat/monthly/SV_${year}_${month}.nc | sed 's,(, ,g' | grep currently | awk '{print $6}')
        _in_ii=$(( $_in_count ))
        _out_ii=$(( $_out_count ))
        _diff=$(( $_in_ii - $_out_ii ))
        echo "SV Year.Month: ${year}.${month}, InputCount: ${_in_count}, OutputCount: ${_out_count}, Diff: ${_diff}"
    done
done


# Validate the SV_${month}.nc files are built correctly
for month in "11" "12" "01" "02" "03" "04"; do 
    _in_ii=0
    for year in `seq 1979 2022`; do 
        ff="/glade/derecho/scratch/meghan/Roza/data/CONUS404/cat/monthly/SV_${year}_${month}.nc"
        if [ -e ${ff} ]; then
            _in_count=$(ncdump -h ${ff} | sed 's,(, ,g' | grep currently | awk '{print $6}')
            _in_ii=$(( $_in_ii + $_in_count ))
        fi
    done
    _out_count=$(ncdump -h /glade/derecho/scratch/meghan/Roza/data/CONUS404/cat/SV_${month}.nc | sed 's,(, ,g' | grep currently | awk '{print $6}')
    _out_ii=$(( $_out_count ))
    _diff=$(( $_in_ii - $_out_ii ))
    echo "SV Month: ${month}, InputCount: ${_in_ii}, OutputCount: ${_out_count}, Diff: ${_diff}"
done


# Validate the SV_Season.nc file is built correctly
_in_ii=0
for month in "11" "12" "01" "02" "03" "04"; do 
    _in_count=$(ncdump -h /glade/derecho/scratch/meghan/Roza/data/CONUS404/cat/SV_${month}.nc | sed 's,(, ,g' | grep currently | awk '{print $6}')
    _in_ii=$(( $_in_ii + $_in_count ))
done
_out_count=$(ncdump -h /glade/derecho/scratch/meghan/Roza/data/CONUS404/cat/SV_Season.nc | sed 's,(, ,g' | grep currently | awk '{print $6}')
_out_ii=$(( $_out_count ))
_diff=$(( $_in_ii - $_out_ii ))
echo "SV Season: InputCount: ${_in_ii}, OutputCount: ${_out_count}, Diff: ${_diff}"
```

### Snotels

GrouseCamp  
47.28, -120.49

SasseRidge
 47.38, -121.06

MeadowsPass  
47.28, -121.47

BumpingRidge  
46.81, -121.33

CayusePass 
46.87, -121.53



Season:
    - [x] As_LWC
    - [x] Gs_LWC
    - [x] As_Tc
    - [x] Gs_TC
    - [x] ground frequency
    - [x] air frequency
    - [ ] 700mb Wind
    - [ ] 850mb Wind

Monthly:
    - [x] As_LWC
    - [x] Gs_LWC
    - [x] As_Tc
    - [x] Gs_TC
    - [x] ground frequency
    - [x] air frequency
    - [ ] 700mb Wind
    - [ ] 850mb Wind


```bash
python bin/create_maps.py \
    --sv-file data/ncfiles/sv/SV_2000_03.nc \
    --dom-file data/ncfiles/domain/wrfconstants_usgs404_roza.nc \
    --shp-file data/shapefiles/RozaBasin.shp  \
    cool --all

python bin/create_maps.py \
    --sv-file data/ncfiles/sv/SV_2000_03.nc \
    --dom-file data/ncfiles/domain/wrfconstants_usgs404_roza.nc \
    --shp-file data/shapefiles/RozaBasin.shp  \
    wind --all --mov

python bin/create_maps.py \
    --sv-file data/ncfiles/sv/SV_2000_03.nc \
    --dom-file data/ncfiles/domain/wrfconstants_usgs404_roza.nc \
    --shp-file data/shapefiles/RozaBasin.shp  \
    wind --mb850 --avg --mb250 --mb500 --mb700
```

Wind map - increase font size of all numbers and legends
decrease color a little and increase topo lines a little

temperature - change color bar scale so 0 degrees is about at the white level  levels=np.linspace(-16,10, 21),

Find out what we used to define the airborne layer and ground layer (meters) 

```
h_gmc=1000
delta_hg=50
h_l1 = 2500
h_h1 = 3500

Ground = height < (h_gmc+delta_hg)
Ground = height < 1050

Air = (h_l1-delta_hg) < height < (h_h1+delta_hg)
Air = 2450 < height < 3550
```

Put plots in grid
Topo map
Lwc In increments of 0.01
Wind barb legend bigger 
Check frequency for ground and airborne 

## 20250717
- PGW/Current climate frequency (conus: bar; pgw: line)
- Combined Simultaneous add bar for Air or Ground