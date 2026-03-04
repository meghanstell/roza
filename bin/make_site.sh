#!/bin/bash


## HOW TO RUN
## Example:
##   For maskfile `./masks/generators/generator_BarkerLakes_avg.nc`
##   ./make_site.sh barkerlakes
##
## Will generate year_month masked data nc files at `/glade/derecho/scratch/meghan/Montana/masks/barkerlakes`
## and a combined masked nc file for entire timespan at `/glade/derecho/scratch/meghan/Montana/masks/barkerlakes.nc`


## Find the directory where this script resides
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

region=${1}
YEAR=${2}
MONTH=${3}

dataDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/SeedingVariables"
# outDir="/glade/work/meghan/Montana/masks/${region}"
outDir="/glade/derecho/scratch/meghan/Roza/masks/${region}"
maskDir="${SCRIPT_DIR}/../masks"
maskFile=`find ${maskDir} -iname "*${region}*" `

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


_info "${region}" "Using Maskfile: ${maskFile}"


function mask_region_year_month(){
    ## Concatenate all the source seeding variable nc files for year and month
    ## Apply the regional mask
    ## Mask all the variables
    ## Average over the mask
    ##
    ## Inputs:
    ##  - year
    ##  - month
    ##
    ## Output:
    ##  - nc file at ${outDir}/arealavg_mask_${year}_${month}_${region}.nc 
    ##    containing the variables from source nc files of entire specified year+month 
    ##    masked for the region
 

    year=$1
    month=$2
    varNames="AS_LWC,AS_LWC_CRIT,AS_Tc,AS_Tc_CRIT,AS_IWC,AS_SLW_CRIT,AS_U,AS_V,GS_LWC,GS_LWC_CRIT,GS_Tc,GS_Tc_CRIT,GS_IWC,GS_SLW_CRIT,GS_U,GS_V,GS_LWC2,GS_LWC2_CRIT,GS_Tc2,GS_Tc2_CRIT,GS_IWC2,GS_SLW2_CRIT,GS_U2,GS_V2,Tc_250MB,U_250MB,V_250MB,Z_250MB,Tc_500MB,U_500MB,V_500MB,Z_500MB,Tc_700MB,U_700MB,V_700MB,Z_700MB,Tc_850MB,U_850MB,V_850MB,Z_850MB"
    vars=("AS_LWC" "AS_LWC_CRIT" "AS_Tc" "AS_Tc_CRIT" "AS_IWC" "AS_SLW_CRIT" "AS_U" "AS_V" "GS_LWC" "GS_LWC_CRIT" "GS_Tc" "GS_Tc_CRIT" "GS_IWC" "GS_SLW_CRIT" "GS_U" "GS_V" "GS_LWC2" "GS_LWC2_CRIT" "GS_Tc2" "GS_Tc2_CRIT" "GS_IWC2" "GS_SLW2_CRIT" "GS_U2" "GS_V2" "Tc_250MB" "U_250MB" "V_250MB" "Z_250MB" "Tc_500MB" "U_500MB" "V_500MB" "Z_500MB" "Tc_700MB" "U_700MB" "V_700MB" "Z_700MB" "Tc_850MB" "U_850MB" "V_850MB" "Z_850MB")
    catfile=${outDir}/../seedvars/seedvars_${year}_${month}.nc
    outfile=${outDir}/arealavg_mask_${year}_${month}_${region}.nc
    _info "${region}.${year}.${month}" "catfile: ${catfile}; outfile: ${outfile}"
    mkdir -p ${outDir} ${outDir}/../seedvars
    if [ ! -f ${catfile} ]; then
        ncrcat -h -v${varNames} ${dataDir}/Seeding_criteria_*${year}-${month}-*.nc ${catfile}
        # ncatted -a _FillValue,PREC_ACC_NC,c,d,-999. ${catfile}
    else
        _warn "${region}.${year}.${month}" "${catfile} already exists. Checking masked output..."
    fi
    _info "${region}.${year}.${month}" "add mask:"
    ncks -A -vmask ${maskFile} ${catfile}

    if [ ! -f {$outfile} ]; then
        _info "${region}.${year}.${month}" "ncap2 mask & avg:"
        for curVar in ${vars[@]}; do
                ncap2 -A -v -s "*${curVar}_mask=0.0*${curVar};where(mask==1) ${curVar}_mask=${curVar};elsewhere ${curVar}_mask=${curVar}@_FillValue; ${curVar}_avg=${curVar}_mask.avg(\$south_north,\$west_east)" ${catfile} ${outfile}
                ncrename -h -v${curVar}_avg,${curVar} ${outfile}
        done
    else
            _warn "${region}.${year}.${month}" "${outfile} already exists. Moving to next file..."
    fi
    _info "${region}.${year}.${month}" "Done."

}
function mask_region_year(){
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
    if [ $year -gt 2020 ] ; then 
        months=("01" "02" "03" "04")
    fi
    for month in ${months[@]}; do
        # mask_region_year_month ${year} ${month} &
        mask_region_year_month ${year} ${month}
    done
    # wait

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
    ncrcat ${outDir}/arealavg_mask_*.nc ${outDir}/../${region}.nc
    _success "${region}" "Masked Site NC File located at ${outDir}/../${region}.nc"
}

function mask_region(){
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
        mask_region_year $year &
        # mask_region_year $year 
    done
    wait
    concat_masked_catfiles
}

# mask_region
mask_region_year_month ${YEAR} ${MONTH}
# ncrcat arealavg_mask_*.nc ../${region}.nc
# rm *1979_01*.tmp *1979_02*.tmp *1979_03*.tmp *1979_04*.tmp *2022_11*.tmp *2022_12*.tmp

function _clean(){
    _region=${1}
    cd ${_region}
    rm *.tmp
    ncrcat arealavg_mask_*.nc ../${_region}.nc
    cd ..
}

# regions=("CorralPass" "CougarMountain" "FishLake" "GreenLake" "GrouseCamp" "HuckleberryCreek" "IndianRock" "LonePine" "LostHorse" "LynnLake" "MeadowsPass" "MorseLake" "MountGardner" "Mowich" "OlallieMeadows" "Paradise" "PepperCreek" "PigtailPeak" "PintoRock" "PotatoHill" "RexRiver" "SasseRidge" "SatusPass" "SawmillRidge" "SkateCreek" "SpencerMeadow" "StampedePass" "SurpriseLakes" "TinkhamCreek" "Trough" "UpperWheeler" "WhitePassES")
# for region in ${regions[@]}; do echo ${region} ; _clean ${region} ; done