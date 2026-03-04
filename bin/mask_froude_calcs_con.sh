#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

calDir="/glade/derecho/scratch/meghan/Roza/froude/froude_hourly"
maskDir="/glade/derecho/scratch/meghan/Roza/roza/masks"

region=${1}
YEAR=${2}
MONTH=${3}

outDir="/glade/derecho/scratch/meghan/Roza/froude/masked/froude_${region}"
catDir="/glade/derecho/scratch/meghan/Roza/froude/froude_monthly"

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

_info "${region}.${YEAR}.${MONTH}" "Using Maskfile: ${maskFile}"
froudeVar="FR"
_info "${region}.${YEAR}.${MONTH}" "Using Variable: ${froudeVar}"

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

    catfile=${catDir}/froude_${year}_${month}.nc
    outfile=${outDir}/arealavg_masked_froude_${year}_${month}_${region}.nc
    # varNames="FrA,FrB"
    # vars=("FrA" "FrB")
    varNames="FR"
    vars=("FR")

    _info "${region}.${year}.${month}" "catfile: ${catfile}; outfile: ${outfile}"
    mkdir -p ${outDir} ${catDir}
    
    if [ ! -f ${catfile} ]; then
        ncrcat -h -v${varNames} ${calDir}/stability_${year}-${month}-*.nc ${catfile}
    else
        _warn "${region}.${year}.${month}" "${catfile} already exists. Checking masked output..."
    fi
    
    

    if [ ! -f {$outfile} ]; then
        if [ $((`ncdump -h ${catfile} | grep "double mask"|wc -l`)) -gt 0 ]; then 
            _warn "${region}.${year}.${month}" "Removing mask from ${catfile}"
            ncks -h -O -x -vmask ${catfile} ${catfile}
        fi 
        _info "${region}.${year}.${month}" "add mask:"
        ncks -A -vmask ${maskFile} ${catfile}

        _info "${region}.${year}.${month}" "ncap2 mask & avg:"
        for curVar in ${vars[@]}; do
            ncap2 -A -v -s "*${curVar}_mask=0.0*${curVar};where(mask==1) ${curVar}_mask=${curVar};elsewhere ${curVar}_mask=${curVar}@_FillValue; ${curVar}_avg=${curVar}_mask.avg(\$south_north,\$west_east)" ${catfile} ${outfile}
            ncrename -h -v${curVar}_avg,${curVar} ${outfile}
        done
        ncks -h -O -x -vmask ${catfile} ${catfile}
        # ncrename -h -vFrB,FrE ${outfile}
    else
        _warn "${region}.${year}.${month}" "${outfile} already exists. Moving to next file..."
    fi

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
    ncrcat ${outDir}/arealavg_masked_*.nc ${outDir}/froude_${region}_${range}.nc
    cp ${outDir}/froude_${region}_${range}.nc ${outDir}/../froude_${region}_${range}.nc
    _success "${region}" "Masked Site NC File located at ${outDir}/froude_${region}_${range}.nc"
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

    for year in `seq 1979 2021`; do
        mask_region_year $year &
        # mask_region_year $year 
    done

    wait
    concat_masked_catfiles
}


_info "${region}.${YEAR}.${MONTH}" "BEGIN"
if [ $(( $YEAR )) -eq 1979 ]; then
    if [ $(( $MONTH )) -gt 9 ]; then
        mask_region_year_month ${YEAR} ${MONTH}
    else
        _info "${region}.${YEAR}.${MONTH}" "Skipping ${YEAR}.${MONTH}"
    fi
elif [ $(( $YEAR )) -eq 2022 ]; then
    if [ $(( $MONTH )) -lt 6 ]; then
        mask_region_year_month ${YEAR} ${MONTH}
    else
        _info "${region}.${YEAR}.${MONTH}" "Skipping ${YEAR}.${MONTH}"
    fi
else
    mask_region_year_month ${YEAR} ${MONTH}
fi
_info "${region}.${YEAR}.${MONTH}" "END"



function _clean(){
    _region=${1}
    ncrcat ${_region}/arealavg_mask*.nc ./${_region}.nc
}

# if [ "${froudeVar}+x" = "x" ] ; then 
#     echo "Froude Variable not found!"
# else 
#     _info "${region}" "Froude Variable: $froudeVar"
    # mask_region
    # mask_region_year_month 1980 01
    # mask_region_year_month 1979 11 &
    # mask_region_year_month 1979 12 &
# mask_region_year_month ${YEAR} ${MONTH}
# fi


# ncrcat arealavg_masked_*.nc froude_genE_AnacondaWest.nc