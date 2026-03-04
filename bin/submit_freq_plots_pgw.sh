#!/bin/bash
#PBS -N RzFB
#PBS -A P48500028
#PBS -l select=1:ncpus=2:mem=10GB
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
# export YEAR=${YEAR:-1984}
# export MONTH=$(printf "%02d" ${PBS_ARRAY_INDEX})

#------------------------------------------------------------------------------------------------------------
# Main
#------------------------------------------------------------------------------------------------------------
export PGW=1
/glade/work/meghan/miniforge3/envs/dorn/bin/python -u bin/frequency_bargraphs.py

#----------------------------------------------------------------------------------
# qsub ./bin/submit_freq_plots_pgw.sh
#----------------------------------------------------------------------------------
