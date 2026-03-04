#!/bin/bash
# SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# sv_script="${SCRIPT_DIR}/output_seedingcriteria_roza.ncl"


catDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cat_wrf_ar"
monthlyDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cat_wrf_ar/monthly_avg"

mkdir -p -m 777 ${catDir} ${monthlyDir}

## ANSI escape codes for colorful logging
RED="\x1b[;31m"
GREEN="\x1b[;32m"
YELLOW="\x1b[;33m"
BLUE="\x1b[;34m"
MAGENTA="\x1b[;35m"
CYAN="\x1b[;36m"
WHITE="\x1b[;37m"
RESET="\x1b[;0m"

MONTH=${1}

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


function concat_wrf_files_month(){
    cat_cmd="ncrcat --hst"
    outFile=${catDir}/wrf3d_${MONTH}.nc

    _info    "concat_wrf_files_month.${MONTH}" "Concatenating WRF Files for Month ${MONTH}"
    
    ${cat_cmd} ${monthlyDir}/wrf3d_*_${MONTH}_avg.nc ${outFile}
    
    _success "concat_wrf_files_month.${MONTH}" "Month WRF File located at ${outFile}"
}

function avg_wrf_files_month(){
    avg_cmd="ncra"
    outFile=${catDir}/wrf3d_${MONTH}_avg.nc

    _info    "avg_wrf_files_month.${MONTH}" "Averaging WRF Files for Month ${MONTH}"
    
    ${avg_cmd} ${catDir}/wrf3d_${MONTH}.nc ${outFile}
    
    _success "avg_wrf_files_month.${MONTH}" "Month WRF File located at ${outFile}"
}

concat_wrf_files_month
avg_wrf_files_month
