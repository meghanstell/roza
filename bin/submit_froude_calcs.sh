#!/bin/bash
#PBS -N RzFr
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

export WORK_DIR="/glade/derecho/scratch/meghan/Roza/roza"

#-----------------------------
# modules
 module load ncl
 module load nco
#-----------------------------
cd ${WORK_DIR}
. /glade/work/meghan/miniforge3/etc/profile.d/mamba.sh
. /glade/work/meghan/miniforge3/etc/profile.d/conda.sh
mamba activate dorn

#------------------------------------------------------------------------------------------------------------
# set run, year, and month
#------------------------------------------------------------------------------------------------------------
# export YEAR=${YEAR:-1984}
# export MONTH=$(printf "%02d" ${PBS_ARRAY_INDEX})
months=("11" "12" "01" "02" "03" "04")
month=${months[$PBS_ARRAY_INDEX]}

#------------------------------------------------------------------------------------------------------------
# Main
#------------------------------------------------------------------------------------------------------------

./bin/run_froude_calcs.sh ${YEAR} ${month}
# ./mask_froude_calcs_con.sh genE AnacondaWest ${YEAR} ${month}

#----------------------------------------------------------------------------------
# 
# for year in `seq 1979 2022`; do qsub -v YEAR=${year} ./bin/submit_froude_calcs.sh ; done
#----------------------------------------------------------------------------------
