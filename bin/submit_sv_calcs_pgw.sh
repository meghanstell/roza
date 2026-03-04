#!/bin/bash
#PBS -N RSP
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

#-----------------------------
# modules
 module load ncl
 module load nco
#-----------------------------
cd /glade/derecho/scratch/meghan/

#------------------------------------------------------------------------------------------------------------
# set run, year, and month
#------------------------------------------------------------------------------------------------------------
export YEAR=${YEAR:-1984}
months=("11" "12" "01" "02" "03" "04")

export MONTH=${months[$PBS_ARRAY_INDEX]}

#------------------------------------------------------------------------------------------------------------
# Main
#------------------------------------------------------------------------------------------------------------

/glade/derecho/scratch/meghan/Roza/roza/bin/run_sv_calcs_pgw.sh ${YEAR} ${MONTH}

#----------------------------------------------------------------------------------
# qsub -v YEAR=2018 ./bin/submit_sv_calcs_pgw.sh
#
# for year in `seq 1979 2022`; do qsub -v YEAR=${year} ./bin/submit_sv_calcs_pgw.sh ; done
#----------------------------------------------------------------------------------
