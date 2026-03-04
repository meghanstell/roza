#!/bin/bash
# SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# sv_script="${SCRIPT_DIR}/output_seedingcriteria_roza.ncl"

# dataDir="/glade/derecho/scratch/meghan/Roza/data/CONUS404/SeedingVariables"
# dataDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/SeedingVariables/"
dataDir="/glade/campaign/ral/hap/meghan/Roza/data/PGW/SeedingVariables"
# catDir="/glade/derecho/scratch/meghan/Roza/data/CONUS404/cat"
# catDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cat"
catDir="/glade/campaign/ral/hap/meghan/Roza/data/PGW/cat"
# monthlyDir="/glade/derecho/scratch/meghan/Roza/data/CONUS404/cat/monthly"
# monthlyDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cat/monthly"
monthlyDir="/glade/campaign/ral/hap/meghan/Roza/data/PGW/cat/monthly"

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
    outFile=${catDir}/SV_Season.nc

    _info    "concat_scfiles_season" "Concatenating Seeding Criteria Files for Season"
    
    ${cat_cmd} ${catDir}/SV_11.nc ${catDir}/SV_12.nc ${catDir}/SV_01.nc ${catDir}/SV_02.nc ${catDir}/SV_03.nc ${catDir}/SV_04.nc ${outFile}
    
    _success "concat_scfiles_season" "Month SV File located at ${outFile}"
}

concat_scfiles_season
