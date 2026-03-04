#!/bin/bash
#PBS -N RzSM
#PBS -A P48500028
#PBS -l select=1:ncpus=2:mem=500GB
#PBS -l walltime=24:00:00
#PBS -q casper
##PBS -J 1-12
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
cd /glade/derecho/scratch/meghan/Roza/roza
. /glade/work/meghan/miniforge3/etc/profile.d/mamba.sh
. /glade/work/meghan/miniforge3/etc/profile.d/conda.sh
mamba activate dorn

#------------------------------------------------------------------------------------------------------------
# set run, year, and month
#------------------------------------------------------------------------------------------------------------

#------------------------------------------------------------------------------------------------------------
# Main
#------------------------------------------------------------------------------------------------------------

# COLUMNS=200 /glade/work/meghan/miniforge3/envs/dorn/bin/python -u bin/create_maps.py cool --all
COLUMNS=200 /glade/work/meghan/miniforge3/envs/dorn/bin/python -u bin/create_maps.py --sv-file /glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cat/SV_Season.nc lwc

#----------------------------------------------------------------------------------
# qsub ./bin/submit_season_lwc.sh
#----------------------------------------------------------------------------------
