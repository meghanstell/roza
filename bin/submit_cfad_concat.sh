#!/bin/bash
#PBS -N RzCM
#PBS -A P48500028
#PBS -l select=1:ncpus=2:mem=2GB
#PBS -l walltime=24:00:00
#PBS -q casper
##PBS -J 0-5
#PBS -j oe
#PBS -o /glade/derecho/scratch/meghan/Roza/qsub/logs
#PBS -m abe
#PBS -M meghan@ucar.edu
##PBS -l place=scatter

#------------------------------------------------------------------------------------------------------------
# Set TMPDIR
#------------------------------------------------------------------------------------------------------------
 
 export TMPDIR="/glade/derecho/scratch/meghan/tmp"
 mkdir -p ${TMPDIR}

 export QSUB_STASH="/glade/derecho/scratch/meghan/Roza/qsub/logs"
 mkdir -p ${QSUB_STASH}

#-----------------------------
# modules
 module load ncl
 module load nco
#-----------------------------
cd /glade/derecho/scratch/meghan/Roza

#------------------------------------------------------------------------------------------------------------
# set run, year, and month
#------------------------------------------------------------------------------------------------------------
GREEN="\x1b[;32m"
MAGENTA="\x1b[;35m"
CYAN="\x1b[;36m"
WHITE="\x1b[;37m"
RESET="\x1b[;0m"
outDir="/glade/derecho/scratch/meghan/Roza/data/cfad/${REGION}"
#------------------------------------------------------------------------------------------------------------
# Main
#------------------------------------------------------------------------------------------------------------
function _info(){
    context=$1
    msg=$2
    echo -e "${WHITE}$(date -Iseconds)${RESET} :: ${CYAN}INFO${RESET}    :: ${MAGENTA}${context}${RESET} :: ${msg}"
}
function _success(){
    context=$1
    msg=$2
    echo -e "${WHITE}$(date -Iseconds)${RESET} :: ${GREEN}SUCCESS${RESET} :: ${MAGENTA}${context}${RESET} :: ${msg}"
}
function concat_masked_catfiles(){
    _info "${REGION}" "Concatenating all masked months"
    ncrcat ${outDir}/lw_T_mask_*.nc ${outDir}/../lw_T_mask_${REGION}.nc
    _success "${REGION}" "Masked Site NC File located at ${outDir}/../lw_T_mask_${REGION}.nc"
}
concat_masked_catfiles
#----------------------------------------------------------------------------------
# qsub -v REGION=BumpingRidge ./bin/submit_cfad_concat.sh
# qsub -v REGION=CayusePass   ./bin/submit_cfad_concat.sh
# qsub -v REGION=GrouseCamp   ./bin/submit_cfad_concat.sh
# qsub -v REGION=MeadowsPass  ./bin/submit_cfad_concat.sh
# qsub -v REGION=SasseRidge   ./bin/submit_cfad_concat.sh
#----------------------------------------------------------------------------------
# NEW SNOTELS 20250304
#----------------------------------------------------------------------------------



# qsub -v REGION=BlewettPass      ./bin/submit_cfad_concat.sh
# qsub -v REGION=BurntMountain    ./bin/submit_cfad_concat.sh
# qsub -v REGION=CorralPass       ./bin/submit_cfad_concat.sh
# qsub -v REGION=CougarMountain   ./bin/submit_cfad_concat.sh
# qsub -v REGION=FishLake         ./bin/submit_cfad_concat.sh

# ncrcat lw_T_mask_*.nc ../lw_T_mask_BlewettPass.nc     |
# ncrcat lw_T_mask_*.nc ../lw_T_mask_BurntMountain.nc   |
# ncrcat lw_T_mask_*.nc ../lw_T_mask_CorralPass.nc      |
# ncrcat lw_T_mask_*.nc ../lw_T_mask_CougarMountain.nc  |
# ncrcat lw_T_mask_*.nc ../lw_T_mask_FishLake.nc

# qsub -v REGION=GreenLake        ./bin/submit_cfad_concat.sh
# qsub -v REGION=HuckleberryCreek ./bin/submit_cfad_concat.sh
# qsub -v REGION=IndianRock       ./bin/submit_cfad_concat.sh
# qsub -v REGION=LonePine         ./bin/submit_cfad_concat.sh
# qsub -v REGION=LostHorse        ./bin/submit_cfad_concat.sh

# qsub -v REGION=LynnLake         ./bin/submit_cfad_concat.sh
# qsub -v REGION=MorseLake        ./bin/submit_cfad_concat.sh
# qsub -v REGION=MountGardner     ./bin/submit_cfad_concat.sh
# qsub -v REGION=Mowich           ./bin/submit_cfad_concat.sh
# qsub -v REGION=OlallieMeadows   ./bin/submit_cfad_concat.sh

# qsub -v REGION=Paradise         ./bin/submit_cfad_concat.sh
# qsub -v REGION=PepperCreek      ./bin/submit_cfad_concat.sh
# qsub -v REGION=PigtailPeak      ./bin/submit_cfad_concat.sh
# qsub -v REGION=PintoRock        ./bin/submit_cfad_concat.sh
# qsub -v REGION=PotatoHill       ./bin/submit_cfad_concat.sh
# qsub -v REGION=RexRiver         ./bin/submit_cfad_concat.sh

# qsub -v REGION=SatusPass        ./bin/submit_cfad_concat.sh
# qsub -v REGION=SawmillRidge     ./bin/submit_cfad_concat.sh
# qsub -v REGION=SkateCreek       ./bin/submit_cfad_concat.sh
# qsub -v REGION=SpencerMeadow    ./bin/submit_cfad_concat.sh
# qsub -v REGION=StampedePass     ./bin/submit_cfad_concat.sh

# qsub -v REGION=SurpriseLakes    ./bin/submit_cfad_concat.sh
# qsub -v REGION=TinkhamCreek     ./bin/submit_cfad_concat.sh
# qsub -v REGION=Trough           ./bin/submit_cfad_concat.sh
# qsub -v REGION=UpperWheeler     ./bin/submit_cfad_concat.sh
# qsub -v REGION=WhitePassES      ./bin/submit_cfad_concat.sh

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------
