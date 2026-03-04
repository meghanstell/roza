#!/bin/bash
#
# Project: IDWR
#
# Purpose: Create vertical profiles of LW and TW within masked regions
#
# Usage: ./make_LW_profiles_IDWR.csh afton 2000 01 CTRL
#
# Last modified: courtney karkkainen 18 Nov 2021
#
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# module load nco

region=${1}
YEAR=${2}
MONTH=${3}
# set region   = ${argv[1]}
# set yy       = ${argv[2]}
# set mm	     = ${argv[3]}

# dataDir="/glade/campaign/collections/rda/data/d559000"
# /glade/campaign/ral/hap/meghan/Roza/data/CONUS404
# dataDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cut"
dataDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cat_wrf_ar"
outDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cfad_q/${region}"
catDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cfad_q/cat"
maskDir=${SCRIPT_DIR}/../masks
maskFile=${maskDir}/${region}.nc

mkdir -p -m 777 ${outDir} ${catDir}

## ANSI escape codes for colorful logging
RED="\x1b[;31m"
GREEN="\x1b[;32m"
YELLOW="\x1b[;33m"
BLUE="\x1b[;34m"
MAGENTA="\x1b[;35m"
CYAN="\x1b[;36m"
WHITE="\x1b[;37m"
RESET="\x1b[;0m"

function _info(){
    context=$1
    msg=$2
    echo -e "${WHITE}$(date -Iseconds)${RESET} :: ${CYAN}INFO${RESET}    :: ${MAGENTA}${context}${RESET} :: ${msg}"
}

function _warn(){
    context=$1
    msg=$2
    echo -e "${WHITE}$(date -Iseconds)${RESET} :: ${YELLOW}WARNING${RESET} :: ${MAGENTA}${context}${RESET} :: ${msg}"
}

function _error(){
    context=$1
    msg=$2
    echo -e "${WHITE}$(date -Iseconds)${RESET} :: ${RED}ERROR${RESET}   :: ${MAGENTA}${context}${RESET} :: ${msg}"
}

function _success(){
    context=$1
    msg=$2
    echo -e "${WHITE}$(date -Iseconds)${RESET} :: ${GREEN}SUCCESS${RESET} :: ${MAGENTA}${context}${RESET} :: ${msg}"
}


_info "${region}" "Using Maskfile: ${maskFile}"

function get_ndays_for_year_month(){
   year=${1}
   month=${2}
   if [[ ${month} == 10 || ${month} == 12 || ${month} == 01 || ${month} == 03 || ${month} == 05 || ${month} == 07 || ${month} == 08 ]]; then 
      nDays=31
   else
      nDays=30
   fi

   if [[ ${month} == 02 ]]; then
      if ! ((year % 4)); then
         nDays=29
      else
         nDays=28
      fi
   fi

   echo "nDays = ${nDays}"
}

# QICE_AR
# QSNOW_AR
# QVAPOR_AR
# QRAIN_AR
# QICE_AR
# QGRAUP_AR
# QCLOUD_AR
qvarnames="QVAPOR,QCLOUD,QRAIN,QICE,QSNOW,QGRAUP,QVAPOR_AR,QCLOUD_AR,QRAIN_AR,QICE_AR,QSNOW_AR,QGRAUP_AR,Z"
vars=("QVAPOR" "QCLOUD" "QRAIN" "QICE" "QSNOW" "QGRAUP" "QVAPOR_AR" "QCLOUD_AR" "QRAIN_AR" "QICE_AR" "QSNOW_AR" "QGRAUP_AR" "Z")
qvars=("QVAPOR" "QCLOUD" "QRAIN" "QICE" "QSNOW" "QGRAUP")
function handle_region_year_month_day(){
   year=${1}
   month=${2}
   daystr=${3}
   catfile=${catDir}/hydromet_${year}${month}${daystr}.nc 
   outfile=${outDir}/lw_mask_${year}${month}${daystr}_${region}_daily.nc
   _info "${region}.${year}.${month}.${daystr}" "catfile: ${catfile}; outfile: ${outfile}"
   _info "${region}.${year}.${month}.${daystr}" "Check catfile"
   
   if [ ! -f ${catfile} ]; then
      _warn "${region}.${year}.${month}.${daystr}" "catfile not found... making it"
      _dir=$(find ${dataDir} -iname "wrf3d*${year}-${month}-${daystr}*" -exec dirname {} \; | sort | uniq)
      
      _info "${region}.${year}.${month}.${daystr}" "DataDir: ${_dir}"
      ncrcat -h -v${qvarnames},TK ${_dir}/wrf3d*${year}-${month}-${daystr}* ${catfile}

      _info "${region}.${year}.${month}.${daystr}" "ncap2 lw/tw"
      for var in ${vars[@]}; do
         ncatted -a _FillValue,${var},o,d,-999.  ${catfile}
      done

      _info "${region}.${year}.${month}.${daystr}" "ncap2 mask & avg"
      ncap2 -A -s 'TC=TK-273.15' ${catfile} ${catfile}
      ncks -O -x -v TK ${catfile} ${catfile}
      ncap2 -A -s 'Zhalf[$Time,$bottom_top,$south_north,$west_east] =0.5*( Z(:,0:49:,:,:)+Z(:,1:,:,:))' ${catfile} ${catfile}
      ncks -O -x -v Z ${catfile} ${catfile}
      ncrename -v Zhalf,Z ${catfile}
      ncatted -a _FillValue,Z,o,d,-999.  ${catfile}
      ncap2 -A -s 'lw_sub0=0.0*QCLOUD;where(TC<-6) lw_sub0=QCLOUD;elsewhere lw_sub0=QCLOUD@_FillValue' ${catfile} ${catfile}
      ncap2 -A -s 'lw_ar_sub0=0.0*QCLOUD_AR;where(TC<-6) lw_ar_sub0=QCLOUD_AR;elsewhere lw_ar_sub0=QCLOUD_AR@_FillValue' ${catfile} ${catfile}
      ncks -O -x -vTC ${catfile} ${catfile}
      ncrename -vlw_sub0,lw ${catfile}
      ncrename -vlw_ar_sub0,lw_ar ${catfile}
      ncatted -a _FillValue,lw,o,d,-999.  ${catfile}
      ncatted -a _FillValue,lw_ar,o,d,-999.  ${catfile}
   fi 

   _info "${region}.${year}.${month}.${daystr}" "add ${region} mask"
   # ncks -O -x -vmask ${catfile} ${catfile}
   ncks -h -A -C -vmask ${maskFile} ${catfile}

   for var in ${vars[@]}; do
      ncap2 -A -v -s "*${var}_mask=0.0*${var};where(mask==1) ${var}_mask=${var};elsewhere ${var}_mask=${var}@_FillValue; ${var}_avg=${var}_mask.avg(\$south_north,\$west_east)" ${catfile} ${outfile}
      ncrename -h -v${var}_avg,${var} ${outfile}   
   done

   ncap2 -A -v -s "*lw_mask=0.0*lw;where(mask==1) lw_mask=lw;elsewhere lw_mask=lw@_FillValue; lw_avg=lw_mask.avg(\$south_north,\$west_east)" ${catfile} ${outfile}
   ncrename -h -vlw_avg,lw ${outfile}
   ncap2 -A -v -s "*lw_ar_mask=0.0*lw_ar;where(mask==1) lw_ar_mask=lw_ar;elsewhere lw_ar_mask=lw_ar@_FillValue; lw_ar_avg=lw_ar_mask.avg(\$south_north,\$west_east)" ${catfile} ${outfile}
   ncrename -h -vlw_ar_avg,lw_ar ${outfile}
   ncks -O -x -vmask ${catfile} ${catfile}
   _success "${region}" "Done. ${outfile}"
}


function _handle_region_year_month_day_avg(){
   # catfile=${catDir}/hydromet_${year}${month}${daystr}.nc 
   catfile=${dataDir}/wrf3d_Season_avg.nc
   outfile=${outDir}/../q_mask_${region}.nc
   # ncks -A -vmask ${maskFile} ${catfile}
   ncks -A -v${qvarnames} ${catfile} ${outfile}
   ncatted -a _FillValue,Z,c,d,-999.  ${outfile}
   ncks -h -A -C -vmask ${maskFile} ${outfile}
   for qVar in ${qvars[@]}; do
      # ncap2 -A -s '*qice_ar_mask=0.0*QICE_AR;where(mask==1) qice_ar_mask=QICE_AR;elsewhere qice_ar_mask=QICE_AR@_FillValue; qice_ar_avg=qice_ar_mask.avg($south_north,$west_east);' ${catfile} ${outfile}
      ncap2 -A -v -s "*${qVar}_mask=0.0*${qVar};where(mask==1) ${qVar}_mask=${qVar};elsewhere ${qVar}_mask=${qVar}@_FillValue; ${qVar}_avg=${qVar}_mask.avg(\$south_north,\$west_east)" ${outfile} ${outfile}
      # ncrename -h -v${qVar}_avg,${qVar} ${outfile}
      ncap2 -A -v -s "*${qVar}_AR_mask=0.0*${qVar}_AR;where(mask==1) ${qVar}_AR_mask=${qVar}_AR;elsewhere ${qVar}_AR_mask=${qVar}@_FillValue; ${qVar}_AR_avg=${qVar}_AR_mask.avg(\$south_north,\$west_east)" ${outfile} ${outfile}
      # ncrename -h -v${qVar}_AR_avg,${qVar}_AR ${outfile}
      
   done
   ncap2 -A -v -s "*Z_mask=0.0*Z;where(mask==1) Z_mask=Z;elsewhere Z_mask=Z@_FillValue; Z_avg=Z_mask.avg(\$south_north,\$west_east)" ${outfile} ${outfile}
   _success "${region}" "Done. ${outfile}"
}


function _handle_region_year_month_day(){
   year=${1}
   month=${2}
   daystr=${3}

   catfile=${catDir}/hydromet_${year}${month}${daystr}.nc 
   outfile=${outDir}/lw_mask_${year}${month}${daystr}_${region}_daily.nc
   _info "${region}.${year}.${month}.${daystr}" "catfile: ${catfile}; outfile: ${outfile}"
   _info "${region}.${year}.${month}.${daystr}" "Check catfile"
   if [ ! -f ${catfile} ]; then
      _warn "${region}.${year}.${month}.${daystr}" "catfile not found... making it"
      _dir=$(find ${dataDir} -iname "wrf3d*${year}-${month}-${daystr}*" -exec dirname {} \; | sort | uniq)
      _info "${region}.${year}.${month}.${daystr}" "DataDir: ${_dir}"

      ncrcat -h -vTK,Z,QCLOUD ${_dir}/wrf3d*${year}-${month}-${daystr}* ${catfile}
      # ncks -A -vXLAT,XLONG wrfconstants_conus404_IDWR.nc  ${catfile}

      _info "${region}.${year}.${month}.${daystr}" "ncap2 lw/tw"
      ncatted -a _FillValue,Z,c,d,-999.  ${catfile}
      ncatted -a _FillValue,TK,c,d,-999. ${catfile} 
      ncatted -a _FillValue,QCLOUD,c,d,-999. ${catfile}

      _info "${region}.${year}.${month}.${daystr}" "ncap2 mask & avg"
      ncap2 -A -s 'TC=TK-273.15' ${catfile} ${catfile}
      ncks -O -x -v TK ${catfile} ${catfile}
      ncap2 -A -s 'Zhalf[$Time,$bottom_top,$south_north,$west_east] =0.5*( Z(:,0:49:,:,:)+Z(:,1:,:,:))' ${catfile} ${catfile}
      ncks -O -x -v Z ${catfile} ${catfile}
      ncrename -v Zhalf,Z ${catfile}
      ncatted -a _FillValue,Z,c,d,-999.  ${catfile}
      ncap2 -A -s 'lw_sub0=0.0*QCLOUD;where(TC<-6) lw_sub0=QCLOUD;elsewhere lw_sub0=QCLOUD@_FillValue' ${catfile} ${catfile}
      ncks -O -x -vQCLOUD,TC ${catfile} ${catfile}
      ncrename -vlw_sub0,lw ${catfile}
   fi 
   _info "${region}.${year}.${month}.${daystr}" "add ${region} mask"
   # ncks -A -vmask ${maskFile} ${catfile}
   ncks -h -A -C -vmask ${maskFile} ${catfile}
   
   ncap2 -A -s '*lw_mask=0.0*lw;*Z_mask=0.0*Z;where(mask==1) lw_mask=lw;elsewhere lw_mask=lw@_FillValue; lw_avg=lw_mask.avg($south_north,$west_east);where(mask==1) Z_mask=Z;elsewhere Z_mask=Z@_FillValue; Z_avg=Z_mask.avg($south_north,$west_east)' ${catfile} ${outfile}
   _success "${region}.${year}.${month}.${daystr}" "Done. ${outfile}"
}


function handle_region_year_month(){

   year=${1}
   month=${2}

   if [[ ${month} == 10 || ${month} == 12 || ${month} == 01 || ${month} == 03 || ${month} == 05 || ${month} == 07 || ${month} == 08 ]]; then 
      nDays=31
   else
      nDays=30
   fi

   if [[ ${month} == 02 ]]; then
      if ! ((year % 4)); then
         nDays=29
      else
         nDays=28
      fi
   fi

   _info "${region}.${year}.${month}" "${nDays} days"
   for day in `seq -f "%02g" 1 $nDays`; do
      handle_region_year_month_day ${year} ${month} ${day} &
      # handle_region_year_month_day ${year} ${month} ${day}
   done
   wait

   ncrcat -O -v${qvarnames},lw,lw_ar ${outDir}/lw_mask_${year}${month}*${region}_daily.nc ${outDir}/lw_T_mask_${year}${month}_${region}.nc && ncatted -hO -a ,global,d,, ${outDir}/lw_T_mask_${year}${month}_${region}.nc && rm ${outDir}/lw_mask_${year}${month}*${region}_daily.nc && _success "${region}.${year}.${month}" "Created ${outDir}/lw_T_mask_${year}${month}_${region}.nc" || _error "${region}.${year}.${month}" "Problem creating ${outDir}/lw_T_mask_${year}${month}_${region}.nc"
}

function concat_masked_catfiles(){
    ## Concatenate all merged and masked nc files from mask_region_year_month
    ## into one combined masked data file for the entire timespan masked to the region
    ##
    ## Inputs:
    ##  - N/A
    ##
    ## Outputs:
    ##  - Concatenated NC file at ${outDir}/../${region}.nc

    _info "${region}" "Concatenating all masked months"
    ncrcat ${outDir}/lw_T_mask_*.nc ${outDir}/../lw_T_mask_${region}.nc
    _success "${region}" "Masked Site NC File located at ${outDir}/../lw_T_mask_${region}.nc"
}

function handle_region_year(){
   ## Iterate over the Season months of the specified year and call 
   ## mask_region_year_month accordingly
   ##
   ## Input:
   ##  - year
   ##
   ## Output:
   ##  - N/A

   months=("01" "02" "03" "04" "11" "12")
   year=$1
   if [ $year -lt 1980 ] ; then 
      months=("11" "12")
   fi
   if [ $year -gt 2021 ] ; then 
      months=("01" "02" "03" "04")
   fi
   for month in ${months[@]}; do
      handle_region_year_month ${year} ${month}
   done
}

function handle_region(){
    ## Iterate over the CONUS404 years and call 
    ## mask_region_year accordingly.
    ## Then call concat_masked_catfiles to combine all the masked data
    ##
    ## Input:
    ##  - N/A
    ##
    ## Output:
    ##  - N/A

    for year in `seq 1979 2022`; do
      #   handle_region_year $year &
        handle_region_year $year
    done
   #  wait
    concat_masked_catfiles
}

# handle_region
# handle_region_year_month_day 1980 11 01
if [ ${YEAR} -lt 1980 ] ; then 
   if [ ${MONTH} -lt 11 ] ; then
      _success "${region}" "Invalid YEAR.MONTH :: ${YELLOW}${YEAR}.${MONTH}${RESET}"
   else
      handle_region_year_month ${YEAR} ${MONTH}
   fi
elif [ ${YEAR} -gt 2021 ] ; then 
   if [ ${MONTH} -gt 4 ] ; then
      _success "${region}" "Invalid YEAR.MONTH :: ${YELLOW}${YEAR}.${MONTH}${RESET}"
   else
      handle_region_year_month ${YEAR} ${MONTH}
   fi
else
   handle_region_year_month ${YEAR} ${MONTH}
fi

# handle_region_year_month_day

function _clean(){
    _region=${1}
    cd ${_region}
    rm *.tmp
    ncrcat lw_T_mask_*.nc ../lw_T_mask_${_region}.nc
    cd ..
}


# for _region in "BumpingRidge" "CayusePass" "BlewettPass" "BurntMountain" "CorralPass" "CougarMountain" "FishLake" "GrouseCamp" "MeadowsPass" "SasseRidge" "SkateCreek" "PotatoHill"; do echo "${_region}" ; _clean ${_region} ; done
# for _region in "BumpingRidge" "CayusePass" "BlewettPass" "BurntMountain" "CorralPass" "CougarMountain" "FishLake" "GrouseCamp" "MeadowsPass" "SasseRidge" "SkateCreek" "PotatoHill"; do echo "${_region}" ; ./bin/make_LW_profiles_subfreezing.sh ${_region} ; done