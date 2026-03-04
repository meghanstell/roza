#!/bin/bash
#
## Project : Roza CONSU404
#
## Purpose : Make subset of CONUS404 output files. Resulting files contain only a set of select
#           variables.
#
# Usage : ./make_3d_analysis_files.csh YYYY MM
# 
#
# Last modified : Meghan Stell 2024
#
#

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
    echo -e "${WHITE}$(date -u +"%Y-%m-%dT%H:%M:%S")${RESET} :: ${CYAN}INFO${RESET}    :: ${MAGENTA}${context}${RESET} :: ${msg}"
}

function _warn(){
    context=$1
    msg=$2
    echo -e "${WHITE}$(date -u +"%Y-%m-%dT%H:%M:%S")${RESET} :: ${YELLOW}WARNING${RESET} :: ${MAGENTA}${context}${RESET} :: ${msg}"
}

function _error(){
    context=$1
    msg=$2
    echo -e "${WHITE}$(date -u +"%Y-%m-%dT%H:%M:%S")${RESET} :: ${RED}ERROR${RESET}   :: ${MAGENTA}${context}${RESET} :: ${msg}"
}

function _success(){
    context=$1
    msg=$2
    echo -e "${WHITE}$(date -u +"%Y-%m-%dT%H:%M:%S")${RESET} :: ${GREEN}SUCCESS${RESET} :: ${MAGENTA}${context}${RESET} :: ${msg}"
}

#-----------------------------------------------------------------------------------------------
# COMMAND LINE PARAMETERS
#-----------------------------------------------------------------------------------------------

YEAR=${1}
MONTH=${2}
# MONTH=$(printf "%02d" ${2})



INDIR3D="/glade/campaign/ncar/USGS_Water/CONUS404_PGW"
outdir="/glade/campaign/ral/hap/meghan/Roza/data/PGW/cut/${YEAR}/${MONTH}"
CONST="/glade/campaign/ral/hap/cweeks/montana/data/model/PGW/wrfconstants_d01_1979-10-01_00:00:00.nc4"
#-----------------------------------------------------------------------------------------------
# List of variables to save
#-----------------------------------------------------------------------------------------------
var3d="Times,P,TK,W,Z,QVAPOR,QSNOW,QCLOUD,QRAIN,QGRAUP,QICE"
varConst="XLAT,XLONG,HGT,SINALPHA,COSALPHA"
var2d="T2,Q2,U10,V10,PREC_ACC_NC,SNOW_ACC_NC,totalIce,totalLiq"

# | ---------------- BOUNDS ------------------ | #
# |  Frame   |   Lower-Left   |   Upper-Right  |
# | -------- | -------------- | -------------- |
# | Lon, Lat | (-122.5, 45.5) | (-119.0, 47.9) |
# | ii , jj  | ( 200  , 720 ) | ( 320  , 850 ) |
# | -------- | -------------- | -------------- |
# ilonLL=214
# ilonUR=295
ilonLL=200
ilonUR=320
ilonUR_stag=321

# jlatLL=759
# jlatUR=797
jlatLL=720
jlatUR=850
jlatUR_stag=851

_info "root.${YEAR}.${MONTH}" "Input: ${YELLOW}${INDIR3D}${RESET} Output: ${YELLOW}${outdir}${RESET}"

function handle_3d_file(){
    infile=$1
    outdir_3d="${outdir}"
    outfile=$(basename ${infile})
    outpath="${outdir_3d}/${outfile}"
    if [ ! -f ${outpath} ]; then
        # _info "handle_3d.${YEAR}.${MONTH}" "3D input file: ${YELLOW}${infile}${RESET}"
        
        ncks -A -x ${infile} ${outpath}
        
        ncks -A -dsouth_north,${jlatLL},${jlatUR} -dwest_east,${ilonLL},${ilonUR} -v${var3d} ${infile} ${outpath}
        ncks -A -dsouth_north,${jlatLL},${jlatUR} -dwest_east_stag,${ilonLL},${ilonUR_stag} -vU ${infile} ${outpath}
        ncks -A -dsouth_north_stag,${jlatLL},${jlatUR_stag} -dwest_east,${ilonLL},${ilonUR} -vV ${infile} ${outpath}

        # _info "handle_3d.${YEAR}.${MONTH}" "Output file: ${YELLOW}${outpath}${RESET}"

        # remove global atts
        ncatted -h -O -a,global,d,, ${outpath} ${outpath}
        #----------------- Compress file -----------------------#
        ncks -O -4 -L 1 ${outpath} ${outpath}
    else
        _warn "handle_3d.${YEAR}.${MONTH}" "Output already exists: ${YELLOW}${outpath}${RESET}"
    fi
}


function handle_3d(){
    outdir_3d="${outdir}"
    mkdir -p ${outdir_3d}
    _total=$(find ${INDIR3D} -name "wrf3d_d01_${YEAR}-${MONTH}-*" | wc -l)
    _count=0
    for infile in `find ${INDIR3D} -name "wrf3d_d01_${YEAR}-${MONTH}-*" | sort`; do
        _count=$(( $_count + 1 ))
        if [[ $(( $_count % 10 )) -eq 0 ]]; then
            _pcnt=$(echo "scale=2 ; $_count*100 / $_total" | bc)
            _info "handle_3d.${YEAR}.${MONTH}" "${CYAN}3D${RESET} ${YELLOW}-->${RESET} ${GREEN}${_pcnt}%${RESET}"
        fi
        handle_3d_file ${infile}
    done
    _success "handle_3d.${YEAR}.${MONTH}" "Done"
}

function handle_2d_file(){
    infile=$1
    outdir_2d="${outdir}/2d"
    outfile=$(basename ${infile})
    outpath="${outdir_2d}/${outfile}"
    if [ ! -f ${outpath} ]; then
        # _info "handle_2d.${YEAR}.${MONTH}" "2D input file: ${YELLOW}${infile}${RESET}"
        # _info "handle_2d.${YEAR}.${MONTH}" "Output file: ${YELLOW}${outpath}${RESET}"

        ncks -A -x ${infile} ${outpath}
        
        ncks -h -A -dsouth_north,${jlatLL},${jlatUR} -dwest_east,${ilonLL},${ilonUR} -v${var2d} ${infile} ${outpath}

        # remove global atts
        # ncatted -h -O -a,global,d,, ${outpath} ${outpath}
        #----------------- Compress file -----------------------#
        ncks -h -O -4 -L 1 ${outpath} ${outpath}
    else
        _warn "handle_2d.${YEAR}.${MONTH}" "Output already exists: ${YELLOW}${outpath}${RESET}"
    fi
}

function handle_2d(){
    outdir_2d="${outdir}/2d"
    mkdir -p ${outdir_2d}
    _total=$(find ${INDIR3D} -name "wrf2d_d01_${YEAR}-${MONTH}-*" | wc -l)
    _count=0
    for infile in `find ${INDIR3D} -name "wrf2d_d01_${YEAR}-${MONTH}-*" | sort`; do
        _count=$(( $_count + 1 ))
        if [[ $(( $_count % 10 )) -eq 0 ]]; then
            _pcnt=$(echo "scale=2 ; $_count*100 / $_total" | bc)
            _info "handle_2d.${YEAR}.${MONTH}" "${CYAN}2D${RESET} ${YELLOW}-->${RESET} ${GREEN}${_pcnt}%${RESET}"
        fi
        handle_2d_file ${infile}
    done
    _success "handle_2d.${YEAR}.${MONTH}" "Done"
}


function handle_const(){
    infile=${CONST}
    outdir_const="${outdir}"
    outfile="wrfconstants_pgw_roza.nc"
    outpath="${outdir_const}/${outfile}"
    if [ ! -f ${outfile} ]; then
        _info "handle_const.${YEAR}.${MONTH}" "Constants input file: ${YELLOW}${infile}${RESET}"
        _info "handle_const.${YEAR}.${MONTH}" "Output file: ${YELLOW}${outpath}${RESET}"

        ncks -h -A -dsouth_north,${jlatLL},${jlatUR} -dwest_east,${ilonLL},${ilonUR} -v${varConst} ${infile} ${outpath}

        # ncatted -h -O -a,global,d,, ${outpath} ${outpath}
        #----------------- Compress file -----------------------#
        ncks -O -4 -L 1 ${outpath} ${outpath}
    else
        _warn "handle_const.${YEAR}.${MONTH}" "Output already exists: ${YELLOW}${outpath}${RESET}"
    fi
}

function add_globals_to_3d(){
    infile=$1
    outdir_3d="${outdir}"
    outfile=$(basename ${infile})
    outpath="${outdir_3d}/${outfile}"
    ncks -A -x ${infile} ${outpath}
}

function handle_3d_globals(){
    outdir_3d="${outdir}"
    mkdir -p ${outdir_3d}
    _total=$(find ${INDIR3D} -name "wrf3d_d01_${YEAR}-${MONTH}-*.nc" | wc -l)
    _count=0
    for infile in `find ${INDIR3D} -name "wrf3d_d01_${YEAR}-${MONTH}-*.nc" | sort`; do
        _count=$(( $_count + 1 ))
        if [[ $(( $_count % 10 )) -eq 0 ]]; then
            _pcnt=$(echo "scale=2 ; $_count*100 / $_total" | bc)
            _info "handle_3d.${YEAR}.${MONTH}" "${CYAN}3D${RESET} ${YELLOW}-->${RESET} ${GREEN}${_pcnt}%${RESET}"
        fi
        add_globals_to_3d ${infile}
    done
    _success "handle_3d.${YEAR}.${MONTH}" "Done"
}

function run(){
    
    handle_3d 
    # handle_3d_globals
    # handle_3d &
    # handle_2d &
    handle_2d 
    handle_const
    # wait
    
    _success "run.${YEAR}.${MONTH}" "Done!"
}

_begin=$(date -u +"%Y-%m-%dT%H:%M:%S")
_begin_unix=$(date +%s)

run

_end=$(date -u +"%Y-%m-%dT%H:%M:%S")
_end_unix=$(date +%s)

_duration_seconds=$(( $_end_unix - $_begin_unix ))
_duration_string=$(python -u -c "import datetime; print(datetime.timedelta(seconds=${_duration_seconds}))")

_success "root.${YEAR}.${MONTH}" "Done! (begin: ${_begin}, end: ${_end}, duration_seconds: ${_duration_seconds}, duration_string: ${_duration_string})"
