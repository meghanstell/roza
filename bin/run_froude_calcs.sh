#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
froude_script="${SCRIPT_DIR}/output_froude.ncl"
# froude_script="${SCRIPT_DIR}/output_froude_normal.ncl"

# region=${1}

# dataDir="/glade/campaign/ral/hap/cweeks/lemhi/data/model/CONUS404/3d"
# outDir="/glade/campaign/ral/hap/meghan/Montana/cfad/${region}"
# catDir="/glade/campaign/ral/hap/meghan/Montana/cfads/cat"
# maskDir=${SCRIPT_DIR}
# maskFile=${maskDir}/${region}.nc

# mkdir -p -m 777 ${outDir} ${catDir}

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
    ## Generic INFO logging function
    ## Inputs:
    ##   - context : functional/logical details
    ##   - msg : string to log
    ##
    ## Example:
    ##   _info "${region}" "Using Maskfile: ${maskFile}"
    ##
    ## Output:
    ##   2024-04-22T03:04:39-06:00 :: INFO    :: basincreek :: Using Maskfile: /glade/derecho/scratch/meghan/Montana/Montana_Masks/scripts/../masks/generators/generator_BasinCreek_avg.nc

    context=$1
    msg=$2
    echo -e "${WHITE}$(date -Iseconds)${RESET} :: ${CYAN}INFO${RESET}    :: ${MAGENTA}${context}${RESET} :: ${msg}"
}

function _warn(){
    ## Generic WARNING logging function
    ## Inputs:
    ##   - context : functional/logical details
    ##   - msg : string to log
    ##
    ## Example:
    ##   _warn "${region}.${year}.${month}" "${catfile} already exists. Checking masked output..."
    ##
    ## Output:
    ##   2024-04-22T03:17:20-06:00 :: WARNING :: basincreek.1987.01 :: /glade/derecho/scratch/meghan/Montana/masks/basincreek/../seedvars/seedvars_1987_01.nc already exists. Checking masked output...

    context=$1
    msg=$2
    echo -e "${WHITE}$(date -Iseconds)${RESET} :: ${YELLOW}WARNING${RESET} :: ${MAGENTA}${context}${RESET} :: ${msg}"
}

function _error(){
    ## Generic ERROR logging function
    ## Inputs:
    ##   - context : functional/logical details
    ##   - msg : string to log
    ##
    ## Example:
    ##   _error "${region}.${year}.${month}" "Failed to add mask"
    ##
    ## Output:
    ##   2024-04-22T03:22:09-06:00 :: ERROR   :: basincreek.1987.01 :: Failed to add mask

    context=$1
    msg=$2
    echo -e "${WHITE}$(date -Iseconds)${RESET} :: ${RED}ERROR${RESET}   :: ${MAGENTA}${context}${RESET} :: ${msg}"
}

function _success(){
    ## Generic SUCCESS logging function
    ## Inputs:
    ##   - context : functional/logical details
    ##   - msg : string to log
    ##
    ## Example:
    ##   _error "${region}.${year}.${month}" "Failed to add mask"
    ##
    ## Output:
    ##   2024-04-22T03:23:50-06:00 :: SUCCESS :: basincreek :: Masked Site NC File located at /glade/derecho/scratch/meghan/Montana/masks/basincreek/../basincreek.nc

    context=$1
    msg=$2
    echo -e "${WHITE}$(date -Iseconds)${RESET} :: ${GREEN}SUCCESS${RESET} :: ${MAGENTA}${context}${RESET} :: ${msg}"
}


YEAR=${1}
MONTH=${2}

function handle_froude_year_month(){
   _info "${YEAR}.${MONTH}" "Launching Froude Script"
   ncl "year=${YEAR}" "mm=${MONTH}" ${froude_script}
   _success "${YEAR}.${MONTH}" "Done!"
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

function handle_froude_year(){
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
    #   handle_froude_year_month ${year} ${month} &
      handle_froude_year_month ${year} ${month}
   done


}

function concat_year_month(){
    _info "${YEAR}.${MONTH}" "Concatenating hourly froude files"
    ncrcat /glade/derecho/scratch/meghan/Roza/froude/stability_${YEAR}-${MONTH}-*.nc /glade/derecho/scratch/meghan/Roza/froude_monthly/froude_${YEAR}_${MONTH}.nc
    _info "${YEAR}.${MONTH}" "Done"
}

function handle_froude(){
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
    # for year in `seq 2019 2021`; do
        # handle_froude_year $year &
        handle_froude_year $year
        # wait
    done
    # wait
    # concat_masked_catfiles
}

handle_froude_year_month
# concat_year_month
# handle_froude
# handle_region_year_month_day 1980 11 01