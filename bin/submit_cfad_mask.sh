#!/bin/bash
#PBS -N RzCM
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

#------------------------------------------------------------------------------------------------------------
# set run, year, and month
#------------------------------------------------------------------------------------------------------------
# regions=("BumpingRidge" "CayusePass" "GrouseCamp" "MeadowsPass" "SasseRidge")
# export REGION=${regions[$PBS_ARRAY_INDEX]}
export YEAR=${YEAR:-1982}
months=("11" "12" "01" "02" "03" "04")

export MONTH=${months[$PBS_ARRAY_INDEX]}

#------------------------------------------------------------------------------------------------------------
# Main
#------------------------------------------------------------------------------------------------------------

./bin/make_LW_profiles_subfreezing.sh ${REGION} ${YEAR} ${MONTH}

#----------------------------------------------------------------------------------
# qsub -v REGION=BumpingRidge ./bin/submit_cfad_mask.sh
#
#----------------------------------------------------------------------------------
# qsub -v YEAR=1979,REGION=BumpingRidge ./bin/submit_cfad_mask.sh 
# qsub -v YEAR=1980,REGION=BumpingRidge ./bin/submit_cfad_mask.sh 
# qsub -v YEAR=1982,REGION=BumpingRidge ./bin/submit_cfad_mask.sh 
# qsub -v YEAR=2003,REGION=BumpingRidge ./bin/submit_cfad_mask.sh 
#----------------------------------------------------------------------------------
# for year in `seq 1980 2022`; do qsub -v YEAR=${year},REGION=BumpingRidge     ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=CayusePass       ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=GrouseCamp       ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=MeadowsPass      ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=SasseRidge       ./bin/submit_cfad_mask.sh ; done
#----------------------------------------------------------------------------------
# NEW SNOTELS 20250304
#----------------------------------------------------------------------------------

# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=BlewettPass      ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=BurntMountain    ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=CorralPass       ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=CougarMountain   ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=FishLake         ./bin/submit_cfad_mask.sh ; done

#----------------------------------------------------------------------------------

# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=GreenLake        ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=HuckleberryCreek ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=IndianRock       ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=LonePine         ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=LostHorse        ./bin/submit_cfad_mask.sh ; done

#----------------------------------------------------------------------------------

# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=LynnLake         ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=MorseLake        ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=MountGardner     ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=Mowich           ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=OlallieMeadows   ./bin/submit_cfad_mask.sh ; done

#----------------------------------------------------------------------------------

# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=Paradise         ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=PepperCreek      ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=PigtailPeak      ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=PintoRock        ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=PotatoHill       ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=RexRiver         ./bin/submit_cfad_mask.sh ; done

# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=SatusPass        ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=SawmillRidge     ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=SkateCreek       ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=SpencerMeadow    ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=StampedePass     ./bin/submit_cfad_mask.sh ; done

# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=SurpriseLakes    ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=TinkhamCreek     ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=Trough           ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=UpperWheeler     ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=WhitePassES      ./bin/submit_cfad_mask.sh ; done

#----------------------------------------------------------------------------------
#----------------------------------------------------------------------------------

# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=BumpingRidge     ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=CayusePass       ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=BlewettPass      ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=BurntMountain    ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=CorralPass       ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=CougarMountain   ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=FishLake         ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=GrouseCamp       ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=MeadowsPass      ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=SasseRidge       ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=SkateCreek       ./bin/submit_cfad_mask.sh ; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},REGION=PotatoHill       ./bin/submit_cfad_mask.sh ; done

# qsub -v YEAR=${year},REGION=CayusePass       ./bin/submit_cfad_mask.sh