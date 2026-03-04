#! /glade/work/meghan/miniforge3/envs/dorn/bin/python3.10 -u
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
# coding: utf-8
import os
import re
import logging
import numpy as np
import xarray as xr
import wrf
import os
from scipy.constants import g
from netCDF4 import Dataset
import datetime
import metpy.calc
from metpy.units import units
import glob
import argparse
from rich.logging import RichHandler
from rich.console import Console
import enum
import rich_click as click
import calendar
import pandas as pd

logging.basicConfig(
    level=os.environ.get('DORN_LOGLEVEL', 'INFO'), 
    format=" [%(name)s] :: %(message)s", 
    datefmt="[%X] ", 
    handlers=[
        RichHandler(
            console=Console(width=200, force_terminal=True),
            locals_max_length=None, 
            locals_max_string=None)])

logger=logging.getLogger('SC_ROLL')


_months=['11','12','01','02', '03','04']

class StrataType(enum.IntEnum):
    GROUND=0
    AIR=1

def makedirs(*dirs):
    _umask = os.umask(0)
    _mode = 0o7775 # stat.S_ISUID|stat.S_ISGID|stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO
    def _mk(_dir):
        _=os.chmod(_dir, _mode) if os.path.exists(_dir) else os.makedirs(_dir, _mode)
    try:
        list(map(_mk, dirs))
    finally:
        os.umask(_umask)
        return dirs[0] if (len(dirs)==1) else dirs

PGW=bool(int(os.environ.get('PGW','0')))

os.environ.update({
    'TMPDIR':makedirs("/glade/derecho/scratch/meghan/tmp"),
    'SQUB_STASH':makedirs("/glade/derecho/scratch/meghan/Roza/qsub/logs"),
    'ROOT_DIR':makedirs("/glade/derecho/scratch/meghan/Roza/roza"),
    })
_model='CONUS404'
if PGW:
    _model='PGW'
_input_dir=f'/glade/campaign/ral/hap/meghan/Roza/data/{_model}/SeedingVariables'
_output_dir=f'/glade/campaign/ral/hap/meghan/Roza/data/{_model}/SC_ROLLUP'
_pbs_array_index = os.environ.get('PBS_ARRAY_INDEX')
if _pbs_array_index:
    os.environ.update({'MONTH':_months[int(_pbs_array_index)]})

class ChartModelType(enum.IntEnum):
    CONUS404=0
    PGW=1

class ChartRangeType(enum.IntEnum):
    SEASON=0
    JANUARY=1
    FEBRUARY=2
    MARCH=3
    APRIL=4
    NOVEMBER=11
    DECEMBER=12

class ChartStrataType(enum.IntEnum):
    GROUND=0
    AIR=1

class ChartVariableType(enum.IntEnum):
    TEMPERATURE=0
    LWC=1
    TLWC=2

class ChartMeasurementType(enum.IntEnum):
    FREQUENCY=0


def handle_sc_hourly_file(input_file, output_dir, strata=StrataType.GROUND):
    logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'handle_sc_hourly_file({input_file=}, {output_dir=}, {strata.name=})')
    # Seeding_criteria_1979-11-01_210000.nc
    _match=re.match(r'^(Seeding)_(criteria)_(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)_(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2}).*nc$',os.path.basename(input_file), flags=re.I)
    _group_dict=_match.groupdict()
    _timestamp = datetime.datetime(int(_group_dict.get('year')), int(_group_dict.get('month')), int(_group_dict.get('day')), int(_group_dict.get('hour')), int(_group_dict.get('minute')), int(_group_dict.get('second')))
    _output_dir=os.path.join(output_dir, 'hourly', f'{_timestamp:%Y}', f'{_timestamp.month:02d}', f'{_timestamp.day:02d}', f'{strata.name.lower()}')
    _output_file=f'SLW_{strata.name}_CRITMASK_{_timestamp:%Y}-{_timestamp:%m}-{_timestamp:%d}_{_timestamp:%H}{_timestamp:%M}{_timestamp:%S}.nc'
    _ignore_vars=[
        # "AS_LWC", 
        "AS_LWC_CRIT", 
        # "AS_Tc", 
        "AS_Tc_CRIT", "AS_IWC", "AS_SLW_CRIT", "AS_U",  "AS_V",  
        # "GS_LWC", 
        "GS_LWC_CRIT", 
        # "GS_Tc", 
        "GS_Tc_CRIT", "GS_IWC", "GS_SLW_CRIT", "GS_U",  "GS_V", 
        "GS_LWC2", "GS_LWC2_CRIT", "GS_Tc2", "GS_Tc2_CRIT", "GS_IWC2", "GS_SLW2_CRIT", "GS_U2",  "GS_V2",  
        "Tc_250MB", "U_250MB", "V_250MB", "Z_250MB", 
        "Tc_500MB", "U_500MB", "V_500MB", "Z_500MB", 
        "Tc_700MB", "U_700MB", "V_700MB", "Z_700MB", 
        "Tc_850MB", "U_850MB", "V_850MB", "Z_850MB"]
    _criteria={
        StrataType.GROUND:{
            'COUNT':(lambda ds: np.ones(ds['GS_LWC'].shape)*len(ds['Time'])),
            'GS_LWC_CRIT':(lambda ds: np.where(ds['GS_LWC']>(1e-2 - 1e-9), 1, 0)),
            'GS_Tc_AG_CRIT':(lambda ds: np.where((ds['GS_Tc']>(-18.0 - 1e-9)) & (ds['GS_Tc']<(-6 + 1e-9)), 1, 0)),
            'GS_LWC_Tc_AG_CRIT':(lambda ds: np.where((ds['GS_LWC']>(1e-2 - 1e-9)) & (ds['GS_Tc']>(-18.0 - 1e-9)) & (ds['GS_Tc']<(-6 + 1e-9)), 1, 0)),
        },
        StrataType.AIR:{
            'COUNT':(lambda ds: np.ones(ds['AS_LWC'].shape)*len(ds['Time'])),
            'AS_LWC_CRIT':(lambda ds: np.where(ds['AS_LWC']>(1e-2 - 1e-9), 1, 0)),
            'AS_Tc_AG_CRIT':(lambda ds: np.where((ds['AS_Tc']>(-18.0 - 1e-9)) & (ds['AS_Tc']<(-6 + 1e-9)), 1, 0)),
            'AS_LWC_Tc_AG_CRIT':(lambda ds: np.where((ds['AS_LWC']>(1e-2 - 1e-9)) & (ds['AS_Tc']>(-18.0 - 1e-9)) & (ds['AS_Tc']<(-6 + 1e-9)), 1, 0)),
        }
    }.get(strata)

    logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'Loading "{os.path.basename(input_file)}"')
    with xr.open_dataset(input_file, drop_variables=_ignore_vars) as ds:
        _time=ds['Time']
        slw_sc_file=xr.Dataset(data_vars={kk:(["south_north", "west_east"],vv(ds)[0,:,:]) for kk,vv in _criteria.items()})
        slw_sc_file=slw_sc_file.expand_dims(dim="Time",axis=0)
        slw_sc_file=slw_sc_file.assign_coords(Time=_time)
        _output_path = os.path.join(makedirs(_output_dir), _output_file)
        logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'Outputting to "{_output_path}"')
        slw_sc_file.to_netcdf(_output_path, unlimited_dims=['Time'])
        logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'Done outputting')
        return _output_path

def handle_sc_daily_rollup(output_dir, year, month, day, strata=StrataType.GROUND):
    logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'handle_sc_daily_rollup({year=}, {month=}, {day=}, {strata.name=})')
    # _pattern=rf'^(Seeding)_(criteria)_{year}-{month}-{day}.*nc$'
    _pattern=rf'^(SLW)_({strata.name})_(CRITMASK)_{year}-{month}-{day}.*nc$'
    _input_dir=os.path.join(output_dir, 'hourly', f'{year}', f'{month}', f'{day}', f'{strata.name.lower()}')
    _output_dir=os.path.join(output_dir, 'daily', f'{year}', f'{month}', f'{strata.name.lower()}')
    _output_file=f'SLW_{strata.name}_CRITMASK_{year}-{month}-{day}.nc'
    _files=sorted([os.path.join(_root, _ff) for _root, _, _files in os.walk(_input_dir) for _ff in _files if re.match(_pattern, _ff, flags=re.I)])
    logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'Loading {len(_files)}')
    if _files:
        ds_combined = xr.open_mfdataset(
            _files,
            # concat_dim='Time', # Or 'lon', 'lat', etc., depending on your data
            # data_vars='minimal',
            # coords='minimal',
            # compat='override',
            # parallel=True # Uncomment if you have Dask installed and many large files for speed
            )
        # daily_rollup_ds=ds_combined.sum(dim='Time')
        ds_combined = ds_combined.reduce(np.sum, dim="Time", keepdims=False)
        ds_combined = ds_combined.expand_dims(dim="Time",axis=0)
        ds_combined = ds_combined.assign_coords(Time=np.array([pd.to_datetime(datetime.datetime(int(year), int(month), int(day)))]))

        _output_path = os.path.join(makedirs(_output_dir), _output_file)
        logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'Outputting to "{_output_path}"')
        ds_combined.to_netcdf(_output_path, unlimited_dims=['Time'])
        logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'Done outputting')
        return _output_path
    
def handle_sc_year_month_rollup(output_dir, year, month, strata=StrataType.GROUND):
    logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'handle_sc_monthly_rollup({year=}, {month=}, {strata.name=})')
    # _pattern=rf'^(Seeding)_(criteria)_{year}-{month}-{day}.*nc$'
    _pattern=rf'^(SLW)_({strata.name})_(CRITMASK)_{year}-{month}-.*nc$'
    _input_dir=os.path.join(output_dir, 'daily', f'{year}', f'{month}', f'{strata.name.lower()}')
    _output_dir=os.path.join(output_dir, 'monthly', f'{year}', f'{strata.name.lower()}')
    _output_file=f'SLW_{strata.name}_CRITMASK_{year}-{month}.nc'
    _files=sorted([os.path.join(_root, _ff) for _root, _, _files in os.walk(_input_dir) for _ff in _files if re.match(_pattern, _ff, flags=re.I)])
    logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'Loading {len(_files)}')
    if _files:
        ds_combined = xr.open_mfdataset(_files)

        ds_combined = ds_combined.reduce(np.sum, dim="Time", keepdims=False)
        ds_combined = ds_combined.expand_dims(dim="Time",axis=0)
        ds_combined = ds_combined.assign_coords(Time=np.array([pd.to_datetime(datetime.datetime(int(year), int(month), 1)) ]))

        _output_path = os.path.join(makedirs(_output_dir), _output_file)
        logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'Outputting to "{_output_path}"')
        ds_combined.to_netcdf(_output_path, unlimited_dims=['Time'])
        logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'Done outputting')
        return _output_path

def handle_sc_season_month_rollup(output_dir, month, strata=StrataType.GROUND):
    logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'handle_sc_season_month_rollup({month=}, {strata.name=})')
    # _pattern=rf'^(Seeding)_(criteria)_{year}-{month}-{day}.*nc$'
    _pattern=rf'^(SLW)_({strata.name})_(CRITMASK)_([\d]+)-{month}\.nc$'
    _input_dir=os.path.join(output_dir, 'monthly')
    _output_dir=os.path.join(output_dir, 'season', f'{strata.name.lower()}')
    _output_file=f'SLW_{strata.name}_CRITMASK_{month}.nc'
    _files=sorted([os.path.join(_root, _ff) for _root, _, _files in os.walk(_input_dir) for _ff in _files if re.match(_pattern, _ff, flags=re.I)])
    logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'Loading {len(_files)}')
    if _files:
        ds_combined = xr.open_mfdataset(_files)
        ds_combined = ds_combined.reduce(np.sum, dim="Time", keepdims=True)

        _output_path = os.path.join(makedirs(_output_dir), _output_file)
        logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'Outputting to "{_output_path}"')
        ds_combined.to_netcdf(_output_path, unlimited_dims=['Time'])
        logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'Done outputting')
        return _output_path
# list(range(1, calendar.monthrange(year, month)[1] + 1))

def handle_sc_full_season_rollup(output_dir, strata=StrataType.GROUND):
    logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'handle_sc_full_season_rollup({strata.name=})')
    _pattern=rf'^(SLW)_({strata.name})_(CRITMASK)_([\d]+)-([\d]+)\.nc$'
    _input_dir=os.path.join(output_dir, 'monthly')
    _output_dir=os.path.join(output_dir, 'season', f'{strata.name.lower()}')
    _output_file=f'SLW_{strata.name}_CRITMASK_SEASON.nc'
    _files=[os.path.join(_root, _ff) for _root, _, _files in os.walk(_input_dir) for _ff in _files if re.match(_pattern, _ff, flags=re.I)]
    if _files:
        ds_combined = xr.open_mfdataset(_files)
        ds_combined = ds_combined.reduce(np.sum, dim="Time", keepdims=True)

        _output_path = os.path.join(makedirs(_output_dir), _output_file)
        logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'Outputting to "{_output_path}"')
        ds_combined.to_netcdf(_output_path, unlimited_dims=['Time'])
        logging.getLogger(f'SC_ROLLUP.{os.environ.get("year")}.{os.environ.get("month")}').info(f'Done outputting')
        return _output_path


def snap_chart(model:ChartModelType, range:ChartRangeType, strata:ChartStrataType, variable:ChartVariableType, measurement:ChartMeasurementType):
    # f"CA_{model_name}_{data_range.name}_{strata.name}_{variable.name}_{measurement.name}"
    logger.info(f'snap_chart({model=}, {range=}, {strata=}, {variable=}, {measurement=})')
    _data_root='/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/SC_ROLLUP'
    _data_range_name=range.name if range == ChartRangeType.SEASON else f'{range.value:02d}' 
    _data_path=os.path.join(_data_root, 'season',f'{strata.name.lower()}', f'SLW_{strata.name}_CRITMASK_{_data_range_name}.nc')
    strata_var_to_data_var={
        (ChartStrataType.GROUND, ChartVariableType.TEMPERATURE):'GS_Tc_AG_CRIT',
        (ChartStrataType.GROUND, ChartVariableType.LWC):'GS_LWC_CRIT',
        (ChartStrataType.GROUND, ChartVariableType.TLWC):'GS_LWC_Tc_AG_CRIT',
        (ChartStrataType.AIR, ChartVariableType.TEMPERATURE):'AS_Tc_AG_CRIT',
        (ChartStrataType.AIR, ChartVariableType.LWC):'AS_LWC_CRIT',
        (ChartStrataType.AIR, ChartVariableType.TLWC):'AS_LWC_Tc_AG_CRIT'}

    output_name=f"RZ_{model.name}_{range.name}_{strata.name}_{variable.name}_{measurement.name}"
    _cache_dir=makedirs(os.path.join(os.environ.get('ROOT_DIR'), 'cache', output_name))
    _cache_file=os.path.join(_cache_dir, f'{output_name}.nc')
    if os.path.exists(_cache_file):
        return logger.warning(f'Cache already exists ({output_name=}), skipping...')
    
    _dom_file_name='wrfconstants_pgw_roza.nc' if PGW else 'wrfconstants_usgs404_roza.nc'
    _dom_file=os.path.join(_input_dir, '..', _dom_file_name)
    # _dom_file=os.path.abspath(os.path.join(_data_root, '..', 'wrfconstants_usgs404_roza.nc'))
    logger.info(f'Using Domain File "{_dom_file}"')
    with xr.open_dataset(_dom_file) as ds:
        _lat=ds['XLAT'].squeeze()
        _lon=ds['XLONG'].squeeze()
    
    with xr.open_dataset(_data_path) as ds:
        _var_sum=ds[strata_var_to_data_var.get((strata, variable))].squeeze()
        _var_count=ds['COUNT'].squeeze()
        _var=(_var_sum/_var_count)*100
        _var=np.where(_var>5,_var,np.nan)


    logger.info(f'Saving data to cache "{_cache_file}"')
    _cvar = _var if isinstance(_var, np.ndarray) else _var.to_numpy()
    dataset = xr.Dataset(data_vars = dict(
            data=(["south_north","west_east"],_cvar),
        ),
        coords = dict(
            XLONG = (["south_north","west_east"],_lon.data),
            XLAT  = (["south_north","west_east"],_lat.data),
        ),
    )
    dataset.to_netcdf(_cache_file)
    logger.info(f'Saved data to cache "{_cache_file}"')




@click.command()
@click.option('--debug/--no-debug', default=False)
# @click.option('--project', default=os.environ.get('PROJECT','California'))
# @click.option('--model', default=os.environ.get('MODEL','CONUS404'))
@click.option('-m','--month', default=os.environ.get('MONTH','11'))
@click.option('-y','--year', default=os.environ.get('YEAR','1979'))
# @click.option('-s','--site', default=os.environ.get('SITE',sites[0]))
@click.option('-i','--input-file', default=None)#os.path.join('/glade/campaign/ral/hap/meghan/California/data/CONUS404/SeedingVariables','Seeding_criteria_1979-11-01_210000.nc'))
@click.option('-d','--input-dir', default=_input_dir)
@click.option('-o','--output-dir', default=_output_dir)
@click.option('--hourly/--no-hourly', default=None)
@click.option('--daily/--no-daily', default=None)
@click.option('--monthly/--no-monthly', default=None)
@click.option('--season/--no-season', default=None)
@click.option('--all-season/--no-all-season', default=None)
@click.option('--snap-cache/--no-snap-cache', default=None)
# "/glade/derecho/scratch/meghan/California/california"
@click.pass_context
def cli(ctx, *args, **kwargs):
    """A CLI tool."""
    # Ensure ctx.obj exists and store debug setting    
    ctx.ensure_object(dict)
    ctx.obj.update(kwargs)
    _input_file=kwargs.get('input_file')
    _outtie=kwargs.get('output_dir', _output_dir)
    _year = kwargs.get('year')
    _month=kwargs.get('month')
    _input_dir=kwargs.get('input_dir')
    os.environ.update(dict(year=_year, month=_month))
    if kwargs.get('hourly') or re.match(r'^.*?(t|1).*$', os.environ.get('HOURLY','')):
        if _input_file:
            handle_sc_hourly_file(_input_file, _outtie, strata=StrataType.GROUND)
        else:
            _pattern=rf'^(Seeding)_(criteria)_{_year}-{_month}-.*nc$'
            _files=sorted([os.path.join(_root, _ff) for _root, _, _files in os.walk(_input_dir) for _ff in _files if re.match(_pattern, _ff, flags=re.I)])
            [handle_sc_hourly_file(_input_file, _outtie, strata=_strata) for _input_file in _files for _strata in StrataType]

    if kwargs.get('daily') or re.match(r'^.*?(t|1).*$', os.environ.get('DAILY','')):
        [handle_sc_daily_rollup(_outtie, _year, _month, f'{_day:02d}', strata=_strata) for _day in list(range(1, calendar.monthrange(int(_year), int(_month))[1] + 1)) for _strata in StrataType]

    if kwargs.get('monthly') or re.match(r'^.*?(t|1).*$', os.environ.get('MONTHLY','')):
        [handle_sc_year_month_rollup(_outtie, _year, _month, strata=_strata) for _strata in StrataType]
        
    if kwargs.get('season') or re.match(r'^.*?(t|1).*$', os.environ.get('SEASON','')):
        [handle_sc_season_month_rollup(_outtie, _month, strata=_strata) for _strata in StrataType]

    if kwargs.get('all_season') or re.match(r'^.*?(t|1).*$', os.environ.get('ALL_SEASON','')):
        if int(_month) in [11]:
            [handle_sc_full_season_rollup(_outtie, strata=_strata) for _strata in StrataType]
    
    if kwargs.get('snap_cache') or re.match(r'^.*?(t|1).*$', os.environ.get('SNAP_CACHE','')):
        if int(_month) in [11]:
            if PGW:
                [snap_chart(model, range, strata, variable, measurement) for model in [ChartModelType.PGW] for range in ChartRangeType for strata in ChartStrataType for variable in ChartVariableType for measurement in ChartMeasurementType]
            else:
                [snap_chart(model, range, strata, variable, measurement) for model in [ChartModelType.CONUS404] for range in ChartRangeType for strata in ChartStrataType for variable in ChartVariableType for measurement in ChartMeasurementType]



            
            
            
            
            

if __name__ == '__main__':
    cli(obj={})

## CONUS404
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},HOURLY=true ./bin/seeding_criteria_rollup.py; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},DAILY=true ./bin/seeding_criteria_rollup.py; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},MONTHLY=true ./bin/seeding_criteria_rollup.py; done
# qsub -v SEASON=true ./bin/seeding_criteria_rollup.py
# qsub -v ALL_SEASON=true ./bin/seeding_criteria_rollup.py
# qsub -v SNAP_CACHE=true ./bin/seeding_criteria_rollup.py

## PGW
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},HOURLY=true,PGW=1  ./bin/seeding_criteria_rollup.py; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},DAILY=true,PGW=1   ./bin/seeding_criteria_rollup.py; done
# for year in `seq 1979 2022`; do qsub -v YEAR=${year},MONTHLY=true,PGW=1 ./bin/seeding_criteria_rollup.py; done
# qsub -v SEASON=true,PGW=1 ./bin/seeding_criteria_rollup.py
# qsub -v ALL_SEASON=true,PGW=1 ./bin/seeding_criteria_rollup.py
# qsub -v SNAP_CACHE=true,PGW=1 ./bin/seeding_criteria_rollup.py

