#!/bin/bash
# SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# sv_script="${SCRIPT_DIR}/output_seedingcriteria_roza.ncl"

catDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cat_wrf_ar"
monthlyDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cat_wrf_ar/monthly"

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

function concat_scfiles_season(){
    # Seeding_criteria_2003-03-19_230000.nc
    cat_cmd="ncrcat --hst"
    outFile=${catDir}/wrf3d_Season.nc

    _info    "concat_scfiles_season" "Concatenating WRF Files for Season"
    
    ${cat_cmd} ${catDir}/wrf3d_11_avg.nc ${catDir}/wrf3d_12_avg.nc ${catDir}/wrf3d_01_avg.nc ${catDir}/wrf3d_02_avg.nc ${catDir}/wrf3d_03_avg.nc ${catDir}/wrf3d_04_avg.nc ${outFile}
    
    _success "concat_wrf_files_season" "Season WRF File located at ${outFile}"
}

function avg_wrf_files_season(){
    avg_cmd="ncra"
    outFile=${catDir}/wrf3d_Season_avg.nc

    _info    "avg_wrf_files_season" "Averaging WRF Files for Season"
    
    ${avg_cmd} ${catDir}/wrf3d_Season.nc ${outFile}
    
    _success "avg_wrf_files_season" "Season WRF File located at ${outFile}"
}

concat_scfiles_season
avg_wrf_files_season
