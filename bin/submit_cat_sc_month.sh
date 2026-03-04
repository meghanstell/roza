#!/bin/bash
#PBS -N RzCM
#PBS -A P48500028
#PBS -l select=1:ncpus=2:mem=2GB
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
cd /glade/derecho/scratch/meghan/Roza

#------------------------------------------------------------------------------------------------------------
# set run, year, and month
#------------------------------------------------------------------------------------------------------------
export MONTH=${MONTH:-1}
export MONTH=$(printf "%02d" ${MONTH})

#------------------------------------------------------------------------------------------------------------
# Main
#------------------------------------------------------------------------------------------------------------

/glade/derecho/scratch/meghan/Roza/roza/bin/cat_sc_files_month.sh ${MONTH}

#----------------------------------------------------------------------------------
# qsub -v MONTH=11 ./bin/submit_cat_sc_month.sh
#
# for month in "11" "12" "01" "02" "03" "04"; do qsub -v MONTH=${month} ./bin/submit_cat_sc_month.sh ; done
#----------------------------------------------------------------------------------




