#!/bin/bash
#PBS -N RzCYM
#PBS -A P48500028
#PBS -l select=1:ncpus=2:mem=2GB
#PBS -l walltime=24:00:00
#PBS -q casper
#PBS -J 0-5
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

export WORKDIR="/glade/derecho/scratch/meghan/Roza/roza"

#-----------------------------
# modules
 module load ncl
 module load nco
#-----------------------------
cd ${WORKDIR}

#------------------------------------------------------------------------------------------------------------
# set run, year, and month
#------------------------------------------------------------------------------------------------------------
export YEAR=${YEAR:-1984}
months=("11" "12" "01" "02" "03" "04")

export MONTH=${months[$PBS_ARRAY_INDEX]}

#------------------------------------------------------------------------------------------------------------
# Main
#------------------------------------------------------------------------------------------------------------

./bin/avg_wrf_files_year_month.sh ${YEAR} ${MONTH}

#----------------------------------------------------------------------------------
# qsub -v YEAR=1979 ./bin/submit_avg_wrf_year_month.sh
#
# for year in `seq 1979 2022`; do qsub -v YEAR=${year} ./bin/submit_avg_wrf_year_month.sh ; done
#----------------------------------------------------------------------------------
