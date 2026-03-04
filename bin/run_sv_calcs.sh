#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
sv_script="${SCRIPT_DIR}/output_seedingcriteria_roza.ncl"

# region=${1}

# dataDir="/glade/campaign/ral/hap/cweeks/lemhi/data/model/CONUS404/3d"
# outDir="/glade/campaign/ral/hap/meghan/Montana/cfad/${region}"
# catDir="/glade/campaign/ral/hap/meghan/Montana/cfads/cat"
# maskDir=${SCRIPT_DIR}
# maskFile=${maskDir}/${region}.nc

# mkdir -p -m 777 ${outDir} ${catDir}



YEAR=${1}
MONTH=${2}

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

function handle_sv_year_month(){
    year=${1}
    month=${2}
    _year=$(( $year ))
    _month=$(( $month ))
    if [[ ${_year} -eq 1979 ]]; then
        if [[ ${_month} -lt 11 ]]; then
            _info "${year}.${month}" "Skipping ${year}.${month}"
        else
            _info "${year}.${month}" "Launching sv script"
            ncl "year=${year}" "mm=${month}" ${sv_script}
            _success "${year}.${month}" "Done!"
        fi
    elif [[ ${_year} -eq 2022 ]]; then
        if [[ ${_month} -gt 4 ]]; then
            _info "${year}.${month}" "Skipping ${year}.${month}"
        else
            _info "${year}.${month}" "Launching sv script"
            ncl "year=${year}" "mm=${month}" ${sv_script}
            _success "${year}.${month}" "Done!"
        fi
    else
        _info "${year}.${month}" "Launching sv script"
        ncl "year=${year}" "mm=${month}" ${sv_script}
        _success "${year}.${month}" "Done!"
    fi
}

# function concat_masked_catfiles(){
#     _info "${region}" "Concatenating all masked months"
#     ncrcat ${outDir}/lw_T_mask_*.nc ${outDir}/../lw_T_mask_${region}.nc
#     _success "${region}" "Masked Site NC File located at ${outDir}/../lw_T_mask_${region}.nc"
# }

function handle_sv_year(){
   months=("01" "02" "03" "04" "11" "12")
   year=$1
   if [ $year -lt 1980 ] ; then 
        months=("11" "12")
    fi
    if [ $year -gt 2021 ] ; then 
        months=("01" "02" "03" "04")
    fi
   for month in ${months[@]}; do
      handle_sv_year_month ${year} ${month}
   done


}

# function handle_sv(){
#     for year in `seq 1979 2022`; do
#         handle_sv_year $year &
#     done
#     wait
#     # concat_masked_catfiles
# }

handle_sv_year_month ${YEAR} ${MONTH}
# handle_sv
# handle_region_year_month_day 1980 11 01