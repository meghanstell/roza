#!/bin/bash
# SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# sv_script="${SCRIPT_DIR}/output_seedingcriteria_roza.ncl"

# dataDir="/glade/derecho/scratch/meghan/Roza/data/CONUS404/SeedingVariables"
dataDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/SeedingVariables/"
# catDir="/glade/derecho/scratch/meghan/Roza/data/CONUS404/cat"
catDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cat"
# monthlyDir="/glade/derecho/scratch/meghan/Roza/data/CONUS404/cat/monthly"
monthlyDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cat/monthly"

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


function concat_scfiles_year_month(){
    # Seeding_criteria_2003-03-19_230000.nc
    year=${1}
    month=${2}
    cat_cmd="ncrcat --hst"
    outFile=${monthlyDir}/SV_${year}_${month}.nc

    _info    "concat_scfiles_year_month.${year}.${month}" "Concatenating Seeding Criteria Files for Year ${year}, Month ${month}"
    
    ${cat_cmd} ${dataDir}/Seeding_criteria_${year}-${month}-*.nc ${outFile}
    
    _success "concat_scfiles_year_month.${year}.${month}" "Year.Month SV File located at ${outFile}"
}

concat_scfiles_year_month ${YEAR} ${MONTH}
