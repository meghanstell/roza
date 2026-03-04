#!/bin/bash
# SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# sv_script="${SCRIPT_DIR}/output_seedingcriteria_roza.ncl"

INDIR3D="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cut"
outdir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cat_wrf_ar/${YEAR}/${MONTH}"
monthlyDir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cat_wrf_ar/monthly"
ar_dir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/SC_ROLLUP_AR_CRIT/hourly"
mkdir -p -m 777 ${outdir} ${monthlyDir}

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

var3d="P,TK,U,V,W,Z,XTIME,QVAPOR,QCLOUD,QRAIN,QICE,QSNOW,QGRAUP,REFL_10CM"
qvars=("QVAPOR" "QCLOUD" "QRAIN" "QICE" "QSNOW" "QGRAUP")
function handle_3d_file(){
    infile=$1
    outdir_3d="${outdir}"
    outfile=$(basename ${infile})
    outpath="${outdir_3d}/${outfile}"

    ar_file="${outfile/wrf3d_d01/SLW_AIR_CRITMASK}"
    ar_file="${ar_file//:}"
    ar_path=$(find ${ar_dir} -name $ar_file)

    if [ ! -f ${outpath} ]; then
        # _info "handle_3d.${YEAR}.${MONTH}" "3D input file: ${YELLOW}${infile}${RESET}"
        
        ncks -A -x ${infile} ${outpath}
        ncks -A -v${var3d} ${infile} ${outpath}
        ncks -A -vARDT ${ar_path} ${outpath}

        # _info "handle_3d.${YEAR}.${MONTH}" "Output file: ${YELLOW}${outpath}${RESET}"
        for qVar in ${qvars[@]}; do
            ncatted -a _FillValue,${qVar},c,d,-999. ${outpath}
            ncap2 -A -v -s "${qVar}_AR=0.0*${qVar};where(ARDT==1) ${qVar}_AR=${qVar};elsewhere ${qVar}_AR=${qVar}@_FillValue;" ${outpath} ${outpath}
            
            # ncatted -a _FillValue,QCLOUD,c,d,-999. ${outpath}
            # ncrename -h -v${curVar}_avg,${curVar} ${outpath}
        done

        # remove global atts
        ncatted -h -O -a,global,d,, ${outpath} ${outpath}
        #----------------- Compress file -----------------------#
        ncks -h -O -4 -L 5 ${outpath} ${outpath}
    else
        _warn "handle_3d.${YEAR}.${MONTH}" "Output already exists: ${YELLOW}${outpath}${RESET}"
    fi
}

function handle_3d(){
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
        handle_3d_file ${infile}
    done
    _success "handle_3d.${YEAR}.${MONTH}" "Done"
}

function concat_wrf_files_year_month(){
    cat_cmd="ncrcat --hst"
    outFile=${monthlyDir}/wrf3d_${YEAR}_${MONTH}.nc

    _info    "concat_wrf_files_year_month.${YEAR}.${MONTH}" "Concatenating WRF Files for Year ${year}, Month ${month}"
    
    ${cat_cmd} ${outdir}/wrf3d_d01_${YEAR}-${MONTH}-*.nc ${outFile}
    
    _success "concat_wrf_files_year_month.${YEAR}.${MONTH}" "Year.Month WRF File located at ${outFile}"
}

handle_3d
concat_wrf_files_year_month ${YEAR} ${MONTH}
