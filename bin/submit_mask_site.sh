#!/bin/bash
#PBS -N RzMS
#PBS -A P48500028
#PBS -l select=1:ncpus=2:mem=25GB
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
cd /glade/derecho/scratch/meghan/Roza/roza
. /glade/work/meghan/miniforge3/etc/profile.d/mamba.sh
. /glade/work/meghan/miniforge3/etc/profile.d/conda.sh
mamba activate dorn

#------------------------------------------------------------------------------------------------------------
# set run, year, and month
#------------------------------------------------------------------------------------------------------------
export REGION=${REGION:-BlewettPass}
export YEAR=${YEAR:-1984}
months=("11" "12" "01" "02" "03" "04")

export MONTH=${months[$PBS_ARRAY_INDEX]}

#------------------------------------------------------------------------------------------------------------
# Main
#------------------------------------------------------------------------------------------------------------

./bin/make_site.sh ${REGION} ${YEAR} ${MONTH}

#----------------------------------------------------------------------------------
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=BlewettPass ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=BumpingRidge ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=BurntMountain ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=CayusePass ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=CorralPass ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=CougarMountain ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=FishLake ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=GreenLake ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=GrouseCamp ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=HuckleberryCreek ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=IndianRock ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=LonePine ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=LostHorse ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=LynnLake ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=MeadowsPass ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=MorseLake ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=MountGardner ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=Mowich ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=OlallieMeadows ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=Paradise ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=PepperCreek ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=PigtailPeak ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=PintoRock ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=PotatoHill ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=RexRiver ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=SasseRidge ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=SatusPass ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=SawmillRidge ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=SkateCreek ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=SpencerMeadow ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=StampedePass ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=SurpriseLakes ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=TinkhamCreek ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=Trough ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=UpperWheeler ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=WhitePassES ./bin/submit_mask_site.sh ; done
#----------------------------------------------------------------------------------
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=Rainier ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=RainierWest ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=RainierEast ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=NachesEast ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=NachesWest ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=NachesRiver ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=UpperYakimaNorth ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=UpperYakimaSouth ./bin/submit_mask_site.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=WestUpperYakima ./bin/submit_mask_site.sh ; done
