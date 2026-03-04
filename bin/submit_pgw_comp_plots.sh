#!/bin/bash
#PBS -N RzCP
#PBS -A P48500028
#PBS -l select=1:ncpus=2:mem=20GB
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

# /glade/derecho/scratch/meghan/Roza/roza/bin/make_3d_analysis_files_roza.sh ${YEAR} ${MONTH}
# /glade/work/meghan/miniforge3/envs/dorn/bin/python -u MT_Season_LWC.py
/glade/work/meghan/miniforge3/envs/dorn/bin/python -u bin/conus_pgw_comparison_frequency_bargraphs.py

#----------------------------------------------------------------------------------
# qsub ./bin/submit_pgw_comp_plots.sh
#----------------------------------------------------------------------------------
