#!/bin/bash
# SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# sv_script="${SCRIPT_DIR}/output_seedingcriteria_roza.ncl"

INDIR3D="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cut"
outdir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cat_wrf_ar/${YEAR}/${MONTH}"
monthlyDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cat_wrf_ar/monthly"
monthlyAvgDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cat_wrf_ar/monthly_avg"

mkdir -p -m 777 ${outdir} ${monthlyDir} ${monthlyAvgDir}

## ANSI escape codes for colorful logging
RED="\x1b[;31m"
GREEN="\x1b[;32m"
YELLOW="\x1b[;33m"
BLUE="\x1b[;34m"
MAGENTA="\x1b[;35m"
CYAN="\x1b[;36m"
WHITE="\x1b[;37m"
RESET="\x1b[;0m"

YEAR=${1}
MONTH=${2}

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

function avg_wrf_file_year_month(){
    avg_cmd="ncra"
    outFile=${monthlyAvgDir}/wrf3d_${YEAR}_${MONTH}_avg.nc

    _info    "avg_wrf_files_year_month.${YEAR}.${MONTH}" "Averaging WRF Files for Year ${YEAR}, Month ${MONTH}"
    
    ${avg_cmd} ${monthlyDir}/wrf3d_${YEAR}_${MONTH}.nc ${outFile}
    
    _success "avg_wrf_files_year_month.${YEAR}.${MONTH}" "Year.Month Average WRF File located at ${outFile}"
}

avg_wrf_file_year_month
