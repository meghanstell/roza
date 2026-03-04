import numpy as np
import xarray as xr
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
#import geocat as geo
import geocat.datafiles as gdf
import netCDF4 as nc
from netCDF4 import Dataset
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from mpl_toolkits.axes_grid1 import make_axes_locatable
from wrf import (getvar, interplevel, to_np, latlon_coords)
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.mpl.contour
import math
import os
import wrf
import geocat.viz as gv
import geopandas as gpd
import shapefile as shp
import statistics
from matplotlib.colors import LinearSegmentedColormap
import matplotlib as mpl
import cmaps
import cartopy
import matplotlib
import proplot as pplt
import seaborn as sns
import seaborn.objects as so
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import matplotlib.ticker as ticker
import datetime
import logging
import re
import json
import platform
import pandas as pd
from rich.logging import RichHandler
from rich.traceback import install
from rich.console import Console
import enum
import collections
import itertools
import random

from dataclasses import dataclass
install()

logging.basicConfig(
    level=os.environ.get('DORN_LOGLEVEL', 'INFO'), 
    format=" [%(name)s] :: %(message)s", 
    datefmt="[%X] ", 
    handlers=[
        RichHandler(
            console=Console(width=200, force_terminal=True),
            locals_max_length=None, 
            locals_max_string=None)])

from rich.console import Console
from rich.syntax import Syntax
from rich.table import (Column, Table)

wind_root = '/glade/derecho/scratch/meghan/Roza/masks'
fr_root = '/glade/derecho/scratch/meghan/Roza/froude/masked'

create_froudes=False

# if re.match(r'^.*(stewmanji).*$', platform.node(), flags=re.I):
#     area_avg_root = '/media/Work/SandBox/luker/ncar/data/netCDF_masks'
#     crit_root = area_avg_root
#     create_froudes=False
# elif re.match(r'^.*(casper|derecho).*$', platform.node(), flags=re.I):
area_avg_root = '/glade/campaign/ral/hap/meghan/Roza/data/CONUS404'
pgw_area_avg_root = '/glade/campaign/ral/hap/meghan/Roza/data/PGW'

applied_masks=    '/glade/derecho/scratch/meghan/Roza/roza/applied_masks'
applied_masks_pgw='/glade/derecho/scratch/meghan/Roza/masks/PGW'

crit_root = area_avg_root
pgw_crit_root=pgw_area_avg_root

matplotlib.rcParams['mathtext.fontset'] = 'stix'
matplotlib.rcParams['font.family'] = 'STIXGeneral'
matplotlib.rcParams['font.size'] = 20

class LwcType(enum.IntEnum):
    GROUND=0
    AIR=1

class Base(object):
    @property
    def _qualname(self):
        if self.__qualname is None:
            module = self.__class__.__module__
            self._qualname=self.__class__.__name__  if ((module is(None)) or (module == str.__class__.__module__)) else '.'.join([module, self.__class__.__name__])
        return self.__qualname
    @_qualname.setter
    def _qualname(self, value): self.__qualname = value

    @property
    def logger(self):
        if self._logger is None: self.logger = logging.getLogger(self._qualname)
        return self._logger
    @logger.setter
    def logger(self, value):
        if isinstance(value, str): return
        self._logger=value

    @property
    def ignore_keys(self):
        if self._ignore_keys is None: self.ignore_keys = ['ignore_keys', 'logger']
        return self._ignore_keys
    @ignore_keys.setter
    def ignore_keys(self, value): self._ignore_keys=value

    def __init__(self, *args, **kwargs): [self.__setattr__(kk,vv) for kk,vv in kwargs.items()]
    def __call__(self, *args, **kwargs):
        [self.__setattr__(kk,vv) for kk,vv in kwargs.items()]
        return self
    def __getattr__(self, name): return self.__dict__.get(name, None)

class Collection(Base):
    @property
    def name(self):
        if self._name is None:
            self.name = self.basename
        return self._name
    @name.setter
    def name(self, value):
        self._name = value
    
    @property
    def wind_label(self):
        if self._wind_label is None:
            self.wind_label = f'{self.WindDirMin}_{self.WindDirMax}'
        return self._wind_label
    @wind_label.setter
    def wind_label(self, value):
        self._wind_label = value

    @property
    def basename(self):
        if self._basename is None:
            self.basename = os.path.splitext(os.path.basename(self.filepath))[0]
        return self._basename
    @basename.setter
    def basename(self, value):
        self._basename = value
    
    @property
    def data(self):
        if self._data is None:
            if self.filepath and os.path.exists(self.filepath):
                self.data = nc.Dataset(self.filepath, 'r')
            else:
                self.logger.warning('Invalid filepath: "{}"'.format(self.filepath))
        return self._data
    @data.setter
    def data(self, value):
        self._data = value
    
    @property
    def Time(self):
        if self._Time is None:
            if 'Time' in self.data.variables:
                if (self.data.variables['Time'].dtype == np.dtype('S1')):
                    self.Time=np.array(list(map(lambda x: (datetime.datetime.strptime(x, '%Y-%m-%d_%H:%M:%S')-datetime.datetime(1979, 10, 1, 0, 0)).total_seconds()/60 , [row.tobytes().decode() for row in self.data.variables['Time'][:]] ) ))
                else:
                    self.Time = self.data.variables['Time'][:]
            else:
                if (self.data.variables['time'].dtype == np.dtype('S1')):
                    self.Time=np.array(list(map(lambda x: (datetime.datetime.strptime(x, '%Y-%m-%d_%H:%M:%S')-datetime.datetime(1979, 10, 1, 0, 0)).total_seconds()/60 , [row.tobytes().decode() for row in self.data.variables['time'][:]] ) ))
                else:
                    self.Time = self.data.variables['time'][:]
        return self._Time
    @Time.setter
    def Time(self, value):
        self._Time = value

    @property
    def Temp(self):
        if self._Temp is None:
            self.Temp = self.data.variables['Tc_700MB'][:]
        return self._Temp
    @Temp.setter
    def Temp(self, value):
        self._Temp = value

    @property
    def Precip(self):
        if self._Precip is None:
            self.Precip = self.data.variables['PREC_ACC_NC'][:]
        return self._Precip
    @Precip.setter
    def Precip(self, value):
        self._Precip = value

    @property
    def Air_LWC(self):
        if self._Air_LWC is None:
            self.Air_LWC = self.data.variables['AS_LWC'][:]
        return self._Air_LWC
    @Air_LWC.setter
    def Air_LWC(self, value):
        self._Air_LWC = value

    @property
    def Air_Temp(self):
        if self._Air_Temp is None:
            self.Air_Temp = self.data.variables['AS_Tc'][:]
        return self._Air_Temp
    @Air_Temp.setter
    def Air_Temp(self, value):
        self._Air_Temp = value

    @property
    def Ground_LWC(self):
        if self._Ground_LWC is None:
            self.Ground_LWC = self.data.variables['GS_LWC'][:]
        return self._Ground_LWC
    @Ground_LWC.setter
    def Ground_LWC(self, value):
        self._Ground_LWC = value

    @property
    def Ground_Temp(self):
        if self._Ground_Temp is None:
            self.Ground_Temp = self.data.variables['GS_Tc'][:]
        return self._Ground_Temp
    @Ground_Temp.setter
    def Ground_Temp(self, value):
        self._Ground_Temp = value
    
    @property
    def U(self):
        if self._U is None:
            self.U = self.data.variables['U_700MB'][:]
        return self._U
    @U.setter
    def U(self, value):
        self._U = value

    @property
    def V(self):
        if self._V is None:
            self.V = self.data.variables['V_700MB'][:]
        return self._V
    @V.setter
    def V(self, value):
        self._V = value

    @property
    def WindDir(self):
        if self._WindDir is None:
            self.WindDir = np.arctan2(self.U,self.V)*180/math.pi+180
        return self._WindDir
    @WindDir.setter
    def WindDir(self, value):
        self._WindDir = value
    
    @property
    def WindDirMin(self):
        if self._WindDirMin is None:
            self.WindDirMin = 220
        return self._WindDirMin
    @WindDirMin.setter
    def WindDirMin(self, value):
        self._WindDirMin = value

    @property
    def WindDirMax(self):
        if self._WindDirMax is None:
            self.WindDirMax = 280
        return self._WindDirMax
    @WindDirMax.setter
    def WindDirMax(self, value):
        self._WindDirMax = value

    # @property
    # def FR(self): return self.Fr

    @property
    def Fr(self):
        if self._Fr is None:
            self.Fr = self.data.variables[self.fr_var][:].data
        return self._Fr
    @Fr.setter
    def Fr(self, value):
        self._Fr = value

    @property
    def phi_range(self):
        if self._phi_range is None:
            self.phi_range=list(range(0,360,15))
        return self._phi_range
    @phi_range.setter
    def phi_range(self, value):
        self._phi_range=value

    @property
    def phi(self):
        if self._phi is None:
            self.phi=0
        return self._phi
    @phi.setter
    def phi(self, value):
        self._phi=value
        self.phi_index=self.phi_range.index(value)
    
    @property
    def phi_index(self):
        if self.phi_index is None:
            self._phi_index=0
        return self._phi_index
    @phi_index.setter
    def phi_index(self, value):
        self._phi_index=value
        self.FR=self.Fr[:,value]

    @property
    def fr_var(self):
        if self._fr_var is None:
            self.fr_var = 'FR'
            # if re.match(r'^.*?(gen_A).*$', os.path.basename(self.filepath), flags=re.I):
            #     self.fr_var = 'FrA'
            # if re.match(r'^.*?(gen_E).*$', os.path.basename(self.filepath), flags=re.I):
            #     self.fr_var = 'FrE'
        return self._fr_var
    @fr_var.setter
    def fr_var(self, value):
        self._fr_var = value

def merge_dfs(*dfs):
    _dd = {}
    for df in dfs:
        for items in df.to_dict(orient='records'):
            _dd.setdefault(items.get('time'), {}).update(items)
    df = pd.DataFrame.from_records(list(_dd.values()))
    df.set_index('time', drop=True, inplace=True)
    df['time'] = pd.to_datetime(df.index, origin=datetime.datetime(1979,10,1), unit='m')
    df.set_index('time', drop=True, inplace=True)
    return df

model='CONUS404 Current and Future Climate'

def create_freq_chart(
        precip=None, 
        criteria=None, 
        criteria_pgw=None, 
        wind=None, 
        wind_pgw=None, 
        froude=None):
    logging.getLogger(__name__).info('Creating Frequency Chart for criteria: "{}", froude: "{}"'.format(criteria.basename, froude.basename))
    criteria_df = pd.DataFrame({'time':criteria.Time, 'temp':criteria.Ground_Temp, 'lwc':criteria.Ground_LWC})
    criteria_pgw_df = pd.DataFrame({'time':criteria_pgw.Time, 'temp':criteria_pgw.Ground_Temp, 'lwc':criteria_pgw.Ground_LWC})
    wind_df = pd.DataFrame({'time':wind.Time, 'wind':wind.WindDir})
    wind_pgw_df = pd.DataFrame({'time':wind_pgw.Time, 'wind':wind_pgw.WindDir})
    froude_df = pd.DataFrame({'time':froude.Time, 'Fr':froude.FR})
    _odf = merge_dfs(criteria_df, wind_df, froude_df)
    _odf_pgw = merge_dfs(criteria_pgw_df, wind_pgw_df, froude_df)
    _months=['','Jan','Feb','Mar', 'Apr','May','Jun','Jul','Aug','Sept','Oct','Nov','Dec']

    def calc_lwc_criteria_match_for_month(month=11, location='lemhi'):
        _month_df = _odf[_odf.index.month == month]
        _crit_df = _month_df[_month_df['temp'] < -6]
        _crit_df = _crit_df[_crit_df['temp'] > -18]
        _crit_df = _crit_df[_crit_df['lwc'] > 0.01]
        _surface_df = _crit_df[_crit_df['wind']>wind.WindDirMin]
        _surface_df = _surface_df[_surface_df['wind'] <wind.WindDirMax]
        _froude_df = _surface_df[_surface_df['Fr'] > 0.4999]
        # _precip_df = _froude_df[_froude_df['precip'] > 0.001]
        return {
            'month':_months[month], 
            '(LWC>0.01 g/kg) & (-18\xb0C<Temp<-6\xb0C)':(len(_crit_df)/len(_month_df))*100, 
            'LWC+Temp+Wind Dir ({}\xb0-{}\xb0)'.format(wind.WindDirMin, wind.WindDirMax):(len(_surface_df)/len(_month_df))*100,
            'LWC+Temp+Wind Dir+Froude>0.5':(len(_froude_df)/len(_month_df))*100, 
            # 'LWC+Temp+Wind Dir+Froude+Precip > 0 (mm)':(len(_precip_df)/len(_month_df))*100, 
            }
    
    def pgw_calc_lwc_criteria_match_for_month(month=11, location='lemhi'):
        _month_df = _odf_pgw[_odf_pgw.index.month == month]
        _crit_df = _month_df[_month_df['temp'] < -6]
        _crit_df = _crit_df[_crit_df['temp'] > -18]
        _crit_df = _crit_df[_crit_df['lwc'] > 0.01]
        _surface_df = _crit_df[_crit_df['wind']>wind.WindDirMin]
        _surface_df = _surface_df[_surface_df['wind'] <wind.WindDirMax]
        _froude_df = _surface_df[_surface_df['Fr'] > 0.4999]
        # _precip_df = _froude_df[_froude_df['precip'] > 0.001]
        return {
            'month':_months[month], 
            'PGW (LWC>0.01 g/kg) & (-18\xb0C<Temp<-6\xb0C)':(len(_crit_df)/len(_month_df))*100, 
            'PGW LWC+Temp+Wind Dir ({}\xb0-{}\xb0)'.format(wind.WindDirMin, wind.WindDirMax):(len(_surface_df)/len(_month_df))*100,
            'PGW LWC+Temp+Wind Dir+Froude>0.5':(len(_froude_df)/len(_month_df))*100, 
            # 'LWC+Temp+Wind Dir+Froude+Precip > 0 (mm)':(len(_precip_df)/len(_month_df))*100, 
            }

    data_dict = [calc_lwc_criteria_match_for_month(month=_month) for _month in [11,12,1,2,3,4]]
    pgw_data_dict = [pgw_calc_lwc_criteria_match_for_month(month=_month) for _month in [11,12,1,2,3,4]]

    df = pd.DataFrame.from_records(data_dict)
    df.set_index('month', inplace=True, drop=True)

    pgw_df = pd.DataFrame.from_records(pgw_data_dict)
    pgw_df.set_index('month', inplace=True, drop=True)
    
    ax=df.plot(kind='bar',rot=0,color=['ocean blue','tiffany blue','burnt orange','apricot'])
    pgw_df.plot(ax=ax,kind='line', linestyle = '--', rot=0,color=['ocean blue','tiffany blue','burnt orange','apricot'])
    # plt.rcParams.update({"text.usetex": False})
    # plt.title(f'Ground Monthly Seeding Frequency \n CONUS 404 Current Climate \n Region: {criteria.name} | Precip: {precip.name}', fontsize = 18)
    
    plt.title(f'Monthly Ground Seeding Frequency \n {model} \n Region: {criteria.name} | Wind: {wind.name} | Froude: {froude.name}', fontsize = 26, fontweight='bold')
    fig = ax.get_figure()
    # fig.set_size_inches(8,8)
    plt.yticks(fontsize=22)
    plt.xticks(fontsize=22)
    fig.set_size_inches(18.5, 10.5)
    # plt.legend(loc="upper right")
    plt.legend(loc="upper right", fontsize=22, ncol=2)
    ax.yaxis.grid(True, which='major')
    # ax.set_ylim(0,math.ceil( max([df[_col].max() for _col in df.columns if _col not in ['month']]) /5.0) * 5)
    ax.set_ylim(0,30)
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.set_xlabel('Month',fontsize =24)
    ax.set_ylabel('Frequency (%)', fontsize =24)
    fig.patch.set_facecolor('white')
    output_name = f'comparison_monthly_ground_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_noPrecip.png'
    output_path = os.path.abspath(output_name)
    plt.savefig(output_path, dpi=300)
    logging.getLogger(__name__).info('Chart saved to "{}"'.format(output_path))
    plt.close()


def create_monthly_airborne_freq_chart(
        precip=None, 
        criteria=None, 
        criteria_pgw=None, 
        wind=None, 
        wind_pgw=None,
        froude=None
        ):
    logging.getLogger(__name__).info('Creating Monthly Airborne Frequency Chart for criteria: "{}"'.format(criteria.basename))
    criteria_df = pd.DataFrame({'time':criteria.Time, 'temp':criteria.Air_Temp, 'lwc':criteria.Air_LWC})
    criteria_pgw_df = pd.DataFrame({'time':criteria_pgw.Time, 'temp':criteria_pgw.Air_Temp, 'lwc':criteria_pgw.Air_LWC})
    _odf = merge_dfs(criteria_df)
    _pgw_odf = merge_dfs(criteria_pgw_df)
    _months=['','Jan','Feb','Mar', 'Apr','May','Jun','Jul','Aug','Sept','Oct','Nov','Dec']

    def calc_lwc_criteria_match_for_month(month=11):
        _month_df = _odf[_odf.index.month == month]
        _crit_df = _month_df[_month_df['temp'] < -6]
        _crit_df = _crit_df[_crit_df['temp'] > -18]
        _crit_df = _crit_df[_crit_df['lwc'] > 0.01]
        return {
            'month':_months[month], 
            'LWC > 0.01 g/kg & -18\xb0C < Temp < -6\xb0C':(len(_crit_df)/len(_month_df))*100
            }

    def pgw_calc_lwc_criteria_match_for_month(month=11):
        _month_df = _pgw_odf[_pgw_odf.index.month == month]
        _crit_df = _month_df[_month_df['temp'] < -6]
        _crit_df = _crit_df[_crit_df['temp'] > -18]
        _crit_df = _crit_df[_crit_df['lwc'] > 0.01]
        return {
            'month':_months[month], 
            'PGW LWC > 0.01 g/kg & -18\xb0C < Temp < -6\xb0C':(len(_crit_df)/len(_month_df))*100
            }

    data_dict = [calc_lwc_criteria_match_for_month(month=_month) for _month in [11,12,1,2,3,4]]
    pgw_data_dict = [pgw_calc_lwc_criteria_match_for_month(month=_month) for _month in [11,12,1,2,3,4]]

    df = pd.DataFrame.from_records(data_dict)
    df.set_index('month', inplace=True, drop=True)
    
    pgw_df = pd.DataFrame.from_records(pgw_data_dict)
    pgw_df.set_index('month', inplace=True, drop=True)
    
    ax=df.plot(kind='bar',rot=0,color=['ocean blue','tiffany blue','burnt orange','apricot'])
    pgw_df.plot(ax=ax,kind='line', linestyle = '--', rot=0,color=['ocean blue','tiffany blue','burnt orange','apricot'])

    # plt.rcParams.update({"text.usetex": False})
    plt.title(f'Monthly Airborne Seeding Frequency \n {model} \n Region: {criteria.name}', fontsize = 26, fontweight='bold')
    fig = ax.get_figure()
    # fig.set_size_inches(8,8)
    plt.yticks(fontsize=22)
    plt.xticks(fontsize=22)
    fig.set_size_inches(18.5, 10.5)
    # plt.legend(loc="upper right")
    plt.legend(loc="upper right", fontsize=22, ncol=2)
    ax.yaxis.grid(True, which='major')
    # ax.set_ylim(0,math.ceil( max([df[_col].max() for _col in df.columns if _col not in ['month']]) /5.0) * 5)
    ax.set_ylim(0,35)
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.set_xlabel('Month',fontsize =24)
    ax.set_ylabel('Frequency (%)', fontsize =24)
    fig.patch.set_facecolor('white')
    # output_name = f'{precip.basename}_{criteria.basename}_{froude.basename}.png'
    # output_name = f'monthly_airborne_{criteria.basename}_{precip.basename}_{froude.basename}_noPrecip.png'
    output_name = f'comparison_monthly_airborne_{criteria.basename}_noPrecip.png'
    output_path = os.path.abspath(output_name)
    plt.savefig(output_path, dpi=300)
    logging.getLogger(__name__).info('Chart saved to "{}"'.format(output_path))
    plt.close()

def create_yearly_chart(
        precip=None, 
        criteria=None, 
        criteria_pgw=None,
        wind=None, 
        wind_pgw=None,
        froude=None,
        lwc_type=LwcType.GROUND):
    logging.getLogger(__name__).info(f'Creating {lwc_type.name} Yearly Seeding Frequency \n {model} \n Region: {criteria.name} | Wind: {wind.name} ({wind.wind_label})')
    if lwc_type == LwcType.GROUND:
        logging.getLogger(__name__).debug('Creating GROUND criteria_df')
        criteria_df = pd.DataFrame({'time':criteria.Time, 'temp':criteria.Ground_Temp, 'lwc':criteria.Ground_LWC})
        wind_df = pd.DataFrame({'time':wind.Time, 'wind':wind.WindDir})
        criteria_pgw_df = pd.DataFrame({'time':criteria_pgw.Time, 'temp':criteria_pgw.Ground_Temp, 'lwc':criteria_pgw.Ground_LWC})
        wind_pgw_df = pd.DataFrame({'time':wind_pgw.Time, 'wind':wind_pgw.WindDir})
        froude_df = pd.DataFrame({'time':froude.Time, 'Fr':froude.FR})
        _odf = merge_dfs(criteria_df, wind_df, froude_df)
        _odf_pgw=merge_dfs(criteria_pgw_df, wind_pgw_df, froude_df)
    else:
        logging.getLogger(__name__).debug('Creating AIR criteria_df')
        criteria_df = pd.DataFrame({'time':criteria.Time, 'temp':criteria.Air_Temp, 'lwc':criteria.Air_LWC})
        criteria_pgw_df = pd.DataFrame({'time':criteria_pgw.Time, 'temp':criteria_pgw.Air_Temp, 'lwc':criteria_pgw.Air_LWC})
        _odf = merge_dfs(criteria_df)
        _odf_pgw = merge_dfs(criteria_pgw_df)

    def calc_lwc_criteria_match_for_year(year=2000):
        logging.getLogger(__name__).debug('calc_lwc_criteria_match_for_year: {}'.format(year))
        _pyear_df = _odf[(_odf.index.year == year-1) & (_odf.index.month>9)]
        _tyear_df = _odf[(_odf.index.year == year) & (_odf.index.month<5)]
        _year_df = pd.concat([_pyear_df, _tyear_df])
        _crit_df = _year_df[_year_df['temp'] < -6]
        _crit_df = _crit_df[_crit_df['temp'] > -18]
        _crit_df = _crit_df[_crit_df['lwc'] > 0.01]
        # _precip_df = _crit_df[_crit_df['precip'] > 0.001]

        if lwc_type == LwcType.GROUND:
            _surface_df = _crit_df[_crit_df['wind']>wind.WindDirMin]
            _surface_df = _surface_df[_surface_df['wind'] <wind.WindDirMax]
            _froude_df = _surface_df[_surface_df['Fr'] > 0.4999]
            return {
                'year':year, 
                'LWC > 0.01 g/kg & -18\xb0C < Temp < -6\xb0C':(len(_crit_df)/len(_year_df))*100, 
                'LWC+Temp+Wind Dir {}\xb0 - {}\xb0'.format(wind.WindDirMin, wind.WindDirMax):(len(_surface_df)/len(_year_df))*100,
                'LWC+Temp+Wind Dir+Froude > 0.5':(len(_froude_df)/len(_year_df))*100, 
                }

        return {
            'year':year, 
            'LWC > 0.01 g/kg & -18\xb0C < Temp < -6\xb0C':(len(_crit_df)/len(_year_df))*100, 
            # 'LWC+Temp+Precip > 0 mm':(len(_precip_df)/len(_year_df))*100,  
            }
    
    def pgw_calc_lwc_criteria_match_for_year(year=2000):
        logging.getLogger(__name__).debug('calc_lwc_criteria_match_for_year: {}'.format(year))
        _pyear_df = _odf_pgw[(_odf_pgw.index.year == year-1) & (_odf_pgw.index.month>9)]
        _tyear_df = _odf_pgw[(_odf_pgw.index.year == year) & (_odf_pgw.index.month<5)]
        _year_df = pd.concat([_pyear_df, _tyear_df])
        _crit_df = _year_df[_year_df['temp'] < -6]
        _crit_df = _crit_df[_crit_df['temp'] > -18]
        _crit_df = _crit_df[_crit_df['lwc'] > 0.01]
        # _precip_df = _crit_df[_crit_df['precip'] > 0.001]

        if lwc_type == LwcType.GROUND:
            _surface_df = _crit_df[_crit_df['wind']>wind.WindDirMin]
            _surface_df = _surface_df[_surface_df['wind'] <wind.WindDirMax]
            _froude_df = _surface_df[_surface_df['Fr'] > 0.4999]
            return {
                'year':year, 
                'PGW LWC > 0.01 g/kg & -18\xb0C < Temp < -6\xb0C':(len(_crit_df)/len(_year_df))*100, 
                'PGW LWC+Temp+Wind Dir {}\xb0 - {}\xb0'.format(wind.WindDirMin, wind.WindDirMax):(len(_surface_df)/len(_year_df))*100,
                'PGW LWC+Temp+Wind Dir+Froude > 0.5':(len(_froude_df)/len(_year_df))*100, 
                }

        return {
            'year':year, 
            'PGW LWC > 0.01 g/kg & -18\xb0C < Temp < -6\xb0C':(len(_crit_df)/len(_year_df))*100, 
            # 'LWC+Temp+Precip > 0 mm':(len(_precip_df)/len(_year_df))*100,  
            }
            

    def get_avg(data):
        keys=list(data[0].keys())
        def _avg(_key):
            return sum(list(map(lambda x: x.get(_key), data)))/len(data)
        def _max(_key):
            return max(list(map(lambda x: x.get(_key), data)))
        # logging.getLogger(__name__).info(f'{data=}')
        _dd={_key:_avg(_key) for _key in keys}
        # max_year = _max('year')
        # _dd.update({'year':max_year+1})
        _dd.update({'year':'40 Yr Avg'})
        # print(_dd)
        return _dd
        # return data + [_dd]



    data_dict = [calc_lwc_criteria_match_for_year(year=_year) for _year in range(1980, 2022)]
    _cavg=get_avg(data_dict)
    pgw_data_dict = [pgw_calc_lwc_criteria_match_for_year(year=_year) for _year in range(1980, 2022)]
    _pavg=get_avg(pgw_data_dict)

    # data_dict = [calc_lwc_criteria_match_for_year(year=_year) for _year in range(1980, 2022)]

    logging.getLogger(__name__).debug('Creating Plot DF')
    df = pd.DataFrame.from_records(data_dict)
    df.set_index('year', inplace=True, drop=True)

    pgw_df=pd.DataFrame.from_records(pgw_data_dict)
    pgw_df.set_index('year', inplace=True, drop=True)

    logging.getLogger(__name__).debug(f'df:\n{df}')
    logging.getLogger(__name__).debug('Plotting')
    _colors=['ocean blue','firebrick','apricot']
    ax=df.plot(kind='line',rot=45,color=_colors)
    pgw_df.plot(ax=ax,kind='line', linestyle = '--', rot=45,color=_colors)

    jj=0
    for kk, vv in _cavg.items():
        if kk in ['year']: continue
        # ax.axhline(vv, ls='-.', label=f'40 Yr Avg({kk})', color=_colors[jj], xmin=1980, xmax=2021, transform=ax.transData)
        ax.axhline(vv, ls='-.', label=f'40 Yr Avg({kk})', color=_colors[jj])
        jj+=1
    
    jj=0
    for kk, vv in _pavg.items():
        if kk in ['year']: continue
        # ax.axhline(vv, ls='-.', label=f'40 Yr Avg({kk})', color=_colors[jj], xmin=1980, xmax=2021, transform=ax.transData)
        ax.axhline(vv, ls=':', label=f'40 Yr Avg({kk})', color=_colors[jj])
        jj+=1


    # plt.rcParams.update({
    #     "text.usetex": False,
    # })

    if lwc_type == LwcType.GROUND:
        plt.title(f'Yearly Ground Seeding Frequency \n {model} \n Region: {criteria.name} | Wind: {wind.name} | Froude: {froude.name}', fontsize = 26, fontweight='bold')
    else:
        plt.title(f'Yearly Airborne Seeding Frequency \n {model} \n Region: {criteria.name}', fontsize = 26, fontweight='bold')
    fig = ax.get_figure()
    # fig.set_size_inches(8,8)
    plt.yticks(fontsize=22)
    plt.xticks(fontsize=22)
    fig.set_size_inches(18.5, 10.5)
    # plt.legend(loc="upper right")
    plt.legend(loc="upper right", fontsize=18, ncol=2)
    ax.yaxis.grid(True, which='major')
    # if lwc_type == LwcType.GROUND:
    ax.set_ylim(0,50) 
        # ax.set_xlim(0,42) 
    # else:
    #     ax.set_ylim(0,35) 
    ax.set_xlim(1980, 2021)
    
    # labels=[
    #     '','','',
    #     '1980', '', '1982', '', '1984', '', '1986', '', '1988', '', 
    #     '1990', '', '1992', '', '1994', '', '1996', '', '1998', '', 
    #     '2000', '', '2002', '', '2004', '', '2006', '', '2008', '', 
    #     '2010', '', '2012', '', '2014', '', '2016', '', '2018', '', 
    #     # '2020', '', '40 Yr']
    #     '2020', '', '40 Yr Avg','','','']

    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.xaxis.set_minor_locator(AutoMinorLocator())

    # ax.xaxis.set_minor_locator(AutoMinorLocator())
    fig.canvas.draw()
    labels = [item.get_text() for item in ax.get_xticklabels()]
    pos = ax.get_xticks()
    logging.getLogger(__name__).debug(f'{pos=}')
    logging.getLogger(__name__).debug(f'{labels=}')

    ax.set_xlabel('Year',fontsize =24)
    # ax.set_xlabel("ha=right")
    ax.set_ylabel('Frequency (%)', fontsize =24)
    fig.patch.set_facecolor('white')
    if lwc_type == LwcType.GROUND:
        output_name = f'comparison_yearly_ground_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}.png'
    else:
        output_name = f'comparison_yearly_airborne_{criteria.basename}_{wind.basename}.png'
    output_path = os.path.abspath(output_name)
    plt.savefig(output_path, dpi=300)
    logging.getLogger(__name__).info('Chart saved to "{}"'.format(output_path))
    plt.close()

def create_monthly_combined_chart(precip=None, criteria=None, criteria_pgw=None, wind=None, wind_pgw=None, froude=None, verbose=None):
    #Yearly: Beaverhead South with Lemhi Ridge Precip
    logging.getLogger(__name__).info(f'Creating Combined Monthly Seeding Frequency \n {model} \n Region: {criteria.name} | Surface: {wind.name} ({wind.wind_label}) | Froude: {froude.name}, Phi: {froude.phi}')

    # logging.getLogger(__name__).info('Creating precip_df')
    # precip_df = pd.DataFrame({'time':precip.Time, 'precip':precip.Precip})
    logging.getLogger(__name__).debug('Creating criteria_df')
    combined_criteria_df = pd.DataFrame({'time':criteria.Time, 'gtemp':criteria.Ground_Temp, 'atemp':criteria.Air_Temp,'glwc':criteria.Ground_LWC, 'alwc':criteria.Air_LWC})
    gnd_criteria_df = pd.DataFrame({'time':criteria.Time, 'gtemp':criteria.Ground_Temp, 'glwc':criteria.Ground_LWC})
    air_criteria_df = pd.DataFrame({'time':criteria.Time, 'atemp':criteria.Air_Temp,'alwc':criteria.Air_LWC})
    wind_df = pd.DataFrame({'time':wind.Time, 'wind':wind.WindDir})
    froude_df = pd.DataFrame({'time':froude.Time, 'Fr':froude.FR})

    combined_criteria_pgw_df = pd.DataFrame({'time':criteria_pgw.Time, 'gtemp':criteria_pgw.Ground_Temp, 'atemp':criteria_pgw.Air_Temp,'glwc':criteria_pgw.Ground_LWC, 'alwc':criteria_pgw.Air_LWC})
    gnd_criteria_pgw_df = pd.DataFrame({'time':criteria_pgw.Time, 'gtemp':criteria_pgw.Ground_Temp, 'glwc':criteria_pgw.Ground_LWC})
    air_criteria_pgw_df = pd.DataFrame({'time':criteria_pgw.Time, 'atemp':criteria_pgw.Air_Temp,'alwc':criteria_pgw.Air_LWC})
    wind_df_pgw = pd.DataFrame({'time':wind_pgw.Time, 'wind':wind_pgw.WindDir})

    # precip_df.set_index('time', drop=True, inplace=True)
    # criteria_df.set_index('time', drop=True, inplace=True)

    # _odf = criteria_df.join(precip_df, how='inner')
    logging.getLogger(__name__).debug('Merging DFs')
    # _odf = merge_dfs(criteria_df, precip_df)
    # _odf = merge_dfs(criteria_df, precip_df, wind_df, froude_df)
    _cmb_odf = merge_dfs(combined_criteria_df, wind_df, froude_df).copy()
    _or_odf = merge_dfs(combined_criteria_df, wind_df, froude_df).copy()
    _gnd_odf = merge_dfs(gnd_criteria_df, wind_df, froude_df).copy()
    _air_odf = merge_dfs(air_criteria_df, wind_df, froude_df).copy()

    _cmb_odf_pgw = merge_dfs(combined_criteria_pgw_df, wind_df_pgw, froude_df).copy()
    _or_odf_pgw = merge_dfs(combined_criteria_pgw_df, wind_df_pgw, froude_df).copy()
    _gnd_odf_pgw = merge_dfs(gnd_criteria_pgw_df, wind_df_pgw, froude_df).copy()
    _air_odf_pgw = merge_dfs(air_criteria_pgw_df, wind_df_pgw, froude_df).copy()
    # _cmb_odf = merge_dfs(combined_criteria_df, wind_df).copy()
    # _gnd_odf = merge_dfs(gnd_criteria_df, wind_df).copy()
    # _air_odf = merge_dfs(air_criteria_df, wind_df).copy()
    # _odf = pd.concat([criteria_df, precip_df])
    # logging.getLogger(__name__).info('Converting Time')
    # _odf['time'] = pd.to_datetime(_odf.index, origin=datetime.datetime(1979,10,1), unit='m') #converts minutes to datetimeh')
    # logging.getLogger(__name__).info('Setting Time Index')
    # _odf.set_index('time', drop=True, inplace=True)
    _months=['','Jan','Feb','Mar', 'Apr','May','Jun','Jul','Aug','Sept','Oct','Nov','Dec']
    def calc_lwc_criteria_match_for_month(month=11, location='lemhi'):
        logging.getLogger(__name__).debug('calc_lwc_criteria_match_for_month: {}'.format(month))
        _cmonth_df = _cmb_odf[_cmb_odf.index.month == month]
        _gmonth_df = _gnd_odf[_gnd_odf.index.month == month]
        _amonth_df = _air_odf[_air_odf.index.month == month]
        _omonth_df = _or_odf[_or_odf.index.month == month]


        if verbose:
            output_name = f'PGW_monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_month_df.json' if PGW else f'monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_month_df.json'
            json.dump(json.loads(_gmonth_df.to_json(orient='records')), open(output_name, 'w'),  indent=4)
        _acrit_df = _amonth_df[_amonth_df['atemp'] < -6]
        _acrit_df = _acrit_df[_acrit_df['atemp'] > -18]
        _acrit_df = _acrit_df[_acrit_df['alwc'] > 0.01]

        _gcrit_df = _gmonth_df[_gmonth_df['gtemp'] < -6]
        _gcrit_df = _gcrit_df[_gcrit_df['gtemp'] > -18]
        _gcrit_df = _gcrit_df[_gcrit_df['glwc'] > 0.01]
        if verbose:
            output_name = f'PGW_monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_crit_df.json' if PGW else f'monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_crit_df.json'
            json.dump(json.loads(_gcrit_df.to_json(orient='records')), open(output_name, 'w'),  indent=4)
        _gcrit_df = _gcrit_df[_gcrit_df['wind']>wind.WindDirMin]
        _gcrit_df = _gcrit_df[_gcrit_df['wind'] <wind.WindDirMax]
        if verbose:
            output_name = f'PGW_monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_surface_df.json' if PGW else f'monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_surface_df.json'
            json.dump(json.loads(_gcrit_df.to_json(orient='records')), open(output_name, 'w'),  indent=4)
        _gcrit_df = _gcrit_df[_gcrit_df['Fr'] > 0.4999]
        if verbose:
            output_name = f'PGW_monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_froude_df.json' if PGW else f'monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_froude_df.json'
            json.dump(json.loads(_gcrit_df.to_json(orient='records')), open(output_name, 'w'),  indent=4)

        _ccrit_df = _cmonth_df[_cmonth_df['atemp'] < -6]
        _ccrit_df = _ccrit_df[_ccrit_df['atemp'] > -18]
        _ccrit_df = _ccrit_df[_ccrit_df['alwc'] > 0.01]
        _ccrit_df = _ccrit_df[_ccrit_df['gtemp'] < -6]
        _ccrit_df = _ccrit_df[_ccrit_df['gtemp'] > -18]
        _ccrit_df = _ccrit_df[_ccrit_df['glwc'] > 0.01]
        _ccrit_df = _ccrit_df[_ccrit_df['wind']>wind.WindDirMin]
        _ccrit_df = _ccrit_df[_ccrit_df['wind'] <wind.WindDirMax]
        _ccrit_df = _ccrit_df[_ccrit_df['Fr'] > 0.4999]

        _omonth_df['gnd_mask'] = True
        _omonth_df['gnd_mask'] = _omonth_df['gnd_mask'].where((_omonth_df['gnd_mask']==True) & (_omonth_df['gtemp'] < -6), False )
        _omonth_df['gnd_mask'] = _omonth_df['gnd_mask'].where((_omonth_df['gnd_mask']==True) & (_omonth_df['gtemp'] > -18), False )
        _omonth_df['gnd_mask'] = _omonth_df['gnd_mask'].where((_omonth_df['gnd_mask']==True) & (_omonth_df['glwc'] > 0.01), False )
        _omonth_df['gnd_mask'] = _omonth_df['gnd_mask'].where((_omonth_df['gnd_mask']==True) & (_omonth_df['wind']>wind.WindDirMin), False )
        _omonth_df['gnd_mask'] = _omonth_df['gnd_mask'].where((_omonth_df['gnd_mask']==True) & (_omonth_df['wind'] <wind.WindDirMax), False )
        _omonth_df['gnd_mask'] = _omonth_df['gnd_mask'].where((_omonth_df['gnd_mask']==True) & (_omonth_df['Fr'] > 0.4999), False )

        _omonth_df['air_mask'] = True
        _omonth_df['air_mask'] = _omonth_df['air_mask'].where((_omonth_df['air_mask']==True) & (_omonth_df['atemp']<-6), False)
        _omonth_df['air_mask'] = _omonth_df['air_mask'].where((_omonth_df['air_mask']==True) & (_omonth_df['atemp']>-18), False) 
        _omonth_df['air_mask'] = _omonth_df['air_mask'].where((_omonth_df['air_mask']==True) & (_omonth_df['alwc'] > 0.01), False)
        # _o_year_df['air_mask'] = _o_year_df[(_o_year_df['atemp'] < -6) & (_o_year_df['atemp'] > -18) & (_o_year_df['alwc'] > 0.01)]
        _omonth_df['or_mask']  = True
        _omonth_df['or_mask']  = _omonth_df['or_mask'].where((_omonth_df['air_mask']==True) | (_omonth_df['gnd_mask']==True), False)
        # _o_year_df['or_mask']  = _o_year_df[(_o_year_df['gnd_mask'])   | (_o_year_df['air_mask'])]        
        # _ocrit_df = _omonth_df.copy()
        _ocrit_df = _omonth_df[_omonth_df['or_mask']==True]

        # _precip_df = _ccrit_df[_ccrit_df['precip'] > 0.001]
        return {
            'month':_months[month], 
            'Air':(len(_acrit_df)/len(_amonth_df))*100, 
            'Ground':(len(_gcrit_df)/len(_gmonth_df))*100, 
            'Air & Ground':(len(_ccrit_df)/len(_cmonth_df))*100, 
            'Air | Ground':(len(_ocrit_df)/len(_omonth_df))*100, 
            # 'Air + Ground + Precip':(len(_precip_df)/len(_month_df))*100,  
            }
    
    def calc_lwc_criteria_match_for_month_pgw(month=11, location='lemhi'):
        logging.getLogger(__name__).debug('calc_lwc_criteria_match_for_month: {}'.format(month))
        _cmonth_df = _cmb_odf_pgw[_cmb_odf_pgw.index.month == month]
        _gmonth_df = _gnd_odf_pgw[_gnd_odf_pgw.index.month == month]
        _amonth_df = _air_odf_pgw[_air_odf_pgw.index.month == month]
        _omonth_df = _or_odf_pgw[_or_odf_pgw.index.month == month]


        if verbose:
            output_name = f'PGW_monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_month_df.json' if PGW else f'monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_month_df.json'
            json.dump(json.loads(_gmonth_df.to_json(orient='records')), open(output_name, 'w'),  indent=4)
        _acrit_df = _amonth_df[_amonth_df['atemp'] < -6]
        _acrit_df = _acrit_df[_acrit_df['atemp'] > -18]
        _acrit_df = _acrit_df[_acrit_df['alwc'] > 0.01]

        _gcrit_df = _gmonth_df[_gmonth_df['gtemp'] < -6]
        _gcrit_df = _gcrit_df[_gcrit_df['gtemp'] > -18]
        _gcrit_df = _gcrit_df[_gcrit_df['glwc'] > 0.01]
        if verbose:
            output_name = f'PGW_monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_crit_df.json' if PGW else f'monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_crit_df.json'
            json.dump(json.loads(_gcrit_df.to_json(orient='records')), open(output_name, 'w'),  indent=4)
        _gcrit_df = _gcrit_df[_gcrit_df['wind']>wind.WindDirMin]
        _gcrit_df = _gcrit_df[_gcrit_df['wind'] <wind.WindDirMax]
        if verbose:
            output_name = f'PGW_monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_surface_df.json' if PGW else f'monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_surface_df.json'
            json.dump(json.loads(_gcrit_df.to_json(orient='records')), open(output_name, 'w'),  indent=4)
        _gcrit_df = _gcrit_df[_gcrit_df['Fr'] > 0.4999]
        if verbose:
            output_name = f'PGW_monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_froude_df.json' if PGW else f'monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_froude_df.json'
            json.dump(json.loads(_gcrit_df.to_json(orient='records')), open(output_name, 'w'),  indent=4)

        _ccrit_df = _cmonth_df[_cmonth_df['atemp'] < -6]
        _ccrit_df = _ccrit_df[_ccrit_df['atemp'] > -18]
        _ccrit_df = _ccrit_df[_ccrit_df['alwc'] > 0.01]
        _ccrit_df = _ccrit_df[_ccrit_df['gtemp'] < -6]
        _ccrit_df = _ccrit_df[_ccrit_df['gtemp'] > -18]
        _ccrit_df = _ccrit_df[_ccrit_df['glwc'] > 0.01]
        _ccrit_df = _ccrit_df[_ccrit_df['wind']>wind.WindDirMin]
        _ccrit_df = _ccrit_df[_ccrit_df['wind'] <wind.WindDirMax]
        _ccrit_df = _ccrit_df[_ccrit_df['Fr'] > 0.4999]

        _omonth_df['gnd_mask'] = True
        _omonth_df['gnd_mask'] = _omonth_df['gnd_mask'].where((_omonth_df['gnd_mask']==True) & (_omonth_df['gtemp'] < -6), False )
        _omonth_df['gnd_mask'] = _omonth_df['gnd_mask'].where((_omonth_df['gnd_mask']==True) & (_omonth_df['gtemp'] > -18), False )
        _omonth_df['gnd_mask'] = _omonth_df['gnd_mask'].where((_omonth_df['gnd_mask']==True) & (_omonth_df['glwc'] > 0.01), False )
        _omonth_df['gnd_mask'] = _omonth_df['gnd_mask'].where((_omonth_df['gnd_mask']==True) & (_omonth_df['wind']>wind.WindDirMin), False )
        _omonth_df['gnd_mask'] = _omonth_df['gnd_mask'].where((_omonth_df['gnd_mask']==True) & (_omonth_df['wind'] <wind.WindDirMax), False )
        _omonth_df['gnd_mask'] = _omonth_df['gnd_mask'].where((_omonth_df['gnd_mask']==True) & (_omonth_df['Fr'] > 0.4999), False )

        _omonth_df['air_mask'] = True
        _omonth_df['air_mask'] = _omonth_df['air_mask'].where((_omonth_df['air_mask']==True) & (_omonth_df['atemp']<-6), False)
        _omonth_df['air_mask'] = _omonth_df['air_mask'].where((_omonth_df['air_mask']==True) & (_omonth_df['atemp']>-18), False) 
        _omonth_df['air_mask'] = _omonth_df['air_mask'].where((_omonth_df['air_mask']==True) & (_omonth_df['alwc'] > 0.01), False)
        # _o_year_df['air_mask'] = _o_year_df[(_o_year_df['atemp'] < -6) & (_o_year_df['atemp'] > -18) & (_o_year_df['alwc'] > 0.01)]
        _omonth_df['or_mask']  = True
        _omonth_df['or_mask']  = _omonth_df['or_mask'].where((_omonth_df['air_mask']==True) | (_omonth_df['gnd_mask']==True), False)
        # _o_year_df['or_mask']  = _o_year_df[(_o_year_df['gnd_mask'])   | (_o_year_df['air_mask'])]        
        # _ocrit_df = _omonth_df.copy()
        _ocrit_df = _omonth_df[_omonth_df['or_mask']==True]

        # _precip_df = _ccrit_df[_ccrit_df['precip'] > 0.001]
        return {
            'month':_months[month], 
            'PGW Air':(len(_acrit_df)/len(_amonth_df))*100, 
            'PGW Ground':(len(_gcrit_df)/len(_gmonth_df))*100, 
            'PGW Air & Ground':(len(_ccrit_df)/len(_cmonth_df))*100, 
            'PGW Air | Ground':(len(_ocrit_df)/len(_omonth_df))*100, 
            # 'Air + Ground + Precip':(len(_precip_df)/len(_month_df))*100,  
            }

    data_dict = [calc_lwc_criteria_match_for_month(month=_month) for _month in [11,12,1,2,3,4]]
    data_dict_pgw = [calc_lwc_criteria_match_for_month_pgw(month=_month) for _month in [11,12,1,2,3,4]]

    logging.getLogger(__name__).debug('Creating Plot DF')
    df = pd.DataFrame.from_records(data_dict)
    df.set_index('month', inplace=True, drop=True)

    df_pgw = pd.DataFrame.from_records(data_dict_pgw)
    df_pgw.set_index('month', inplace=True, drop=True)

    logging.getLogger(__name__).debug('Plotting')
    ax=df.plot(kind='bar',rot=45,color=['ocean blue','tiffany blue','burnt orange','apricot'])
    df_pgw.plot(ax=ax,kind='line', linestyle = '--', rot=45,color=['ocean blue','tiffany blue','burnt orange','apricot'])

    # plt.rcParams.update({
    #     "text.usetex": False,
    # })

    plt.title(f'Monthly Simultaneous Seeding Frequency \n {model} \n Region: {criteria.name} | Wind: {wind.name} | Froude: {froude.name}', fontsize = 26, fontweight='bold')
    fig = ax.get_figure()
    # fig.set_size_inches(8,8)
    plt.yticks(fontsize=22)
    plt.xticks(fontsize=22)
    fig.set_size_inches(18.5, 10.5)
    # plt.legend(loc="upper right")
    plt.legend(loc="upper right", fontsize=22)
    ax.yaxis.grid(True, which='major')
    ax.set_ylim(0,40)
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.set_xlabel('Year',fontsize =24)
    # ax.set_ylabel('Frequency (%)', fontsize =22)
    ax.set_ylabel(r'$Frequency\ \left(\%\right)$', fontsize =24)
    fig.patch.set_facecolor('white')
    # plt.savefig('bhs_lrp_ground_year.png', dpi=300)
    output_name = f'comparison_monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}.png'
    output_path = os.path.abspath(output_name)
    plt.savefig(output_path, dpi=300)
    logging.getLogger(__name__).info('Chart saved to "{}"'.format(output_path))
    plt.close()

# /glade/derecho/scratch/meghan/Roza/masks
RainierEast = Collection(filepath=os.path.join(applied_masks, 'RainierEast.nc'), name='Rainier East') 
RainierWest = Collection(filepath=os.path.join(applied_masks, 'RainierWest.nc'), name='Rainier West') 
NachesRiver = Collection(filepath=os.path.join(applied_masks, 'NachesRiver.nc'), name='Naches River')
UpperYakimaSouth = Collection(filepath=os.path.join(applied_masks, 'UpperYakimaSouth.nc'), name='Upper Yakima South')
NachesEast = Collection(filepath=os.path.join(applied_masks, 'NachesEast.nc'), name='Naches East')
UpperYakimaNorth = Collection(filepath=os.path.join(applied_masks, 'UpperYakimaNorth.nc'), name='Upper Yakima North')
NachesWest = Collection(filepath=os.path.join(applied_masks, 'NachesWest.nc'), name='Naches West')
RainierEastPgw = Collection(filepath=os.path.join(applied_masks_pgw, 'RainierEast.nc'), name='Rainier East') 
RainierWestPgw = Collection(filepath=os.path.join(applied_masks_pgw, 'RainierWest.nc'), name='Rainier West') 
NachesRiverPgw = Collection(filepath=os.path.join(applied_masks_pgw, 'NachesRiver.nc'), name='Naches River')
UpperYakimaSouthPgw = Collection(filepath=os.path.join(applied_masks_pgw, 'UpperYakimaSouth.nc'), name='Upper Yakima South')
NachesEastPgw = Collection(filepath=os.path.join(applied_masks_pgw, 'NachesEast.nc'), name='Naches East')
UpperYakimaNorthPgw = Collection(filepath=os.path.join(applied_masks_pgw, 'UpperYakimaNorth.nc'), name='Upper Yakima North')
NachesWestPgw = Collection(filepath=os.path.join(applied_masks_pgw, 'NachesWest.nc'), name='Naches West')

# /glade/derecho/scratch/meghan/Roza/masks
BurntMountain = Collection(filepath=os.path.join(applied_masks, 'BurntMountain.nc'), name='Burnt Mountain')
MeadowsPass = Collection(filepath=os.path.join(applied_masks, 'MeadowsPass.nc'), name='Meadows Pass')
CayusePass = Collection(filepath=os.path.join(applied_masks, 'CayusePass.nc'), name='Cayuse Pass')
FishLake = Collection(filepath=os.path.join(applied_masks, 'FishLake.nc'), name='Fish Lake')
BumpingRidge = Collection(filepath=os.path.join(applied_masks, 'BumpingRidge.nc'), name='Bumping Ridge')
CorralPass = Collection(filepath=os.path.join(applied_masks, 'CorralPass.nc'), name='Corral Pass')
SasseRidge = Collection(filepath=os.path.join(applied_masks, 'SasseRidge.nc'), name='Sasse Ridge')
SkateCreek = Collection(filepath=os.path.join(applied_masks, 'SkateCreek.nc'), name='Skate Creek')
PotatoHill = Collection(filepath=os.path.join(applied_masks, 'PotatoHill.nc'), name='Potato Hill')
CougarMountain = Collection(filepath=os.path.join(applied_masks, 'CougarMountain.nc'), name='Cougar Mountain')
BurntMountainPgw = Collection(filepath=os.path.join(applied_masks_pgw, 'BurntMountain.nc'), name='Burnt Mountain')
MeadowsPassPgw = Collection(filepath=os.path.join(applied_masks_pgw, 'MeadowsPass.nc'), name='Meadows Pass')
CayusePassPgw = Collection(filepath=os.path.join(applied_masks_pgw, 'CayusePass.nc'), name='Cayuse Pass')
FishLakePgw = Collection(filepath=os.path.join(applied_masks_pgw, 'FishLake.nc'), name='Fish Lake')
BumpingRidgePgw = Collection(filepath=os.path.join(applied_masks_pgw, 'BumpingRidge.nc'), name='Bumping Ridge')
CorralPassPgw = Collection(filepath=os.path.join(applied_masks_pgw, 'CorralPass.nc'), name='Corral Pass')
SasseRidgePgw = Collection(filepath=os.path.join(applied_masks_pgw, 'SasseRidge.nc'), name='Sasse Ridge')
SkateCreekPgw = Collection(filepath=os.path.join(applied_masks_pgw, 'SkateCreek.nc'), name='Skate Creek')
PotatoHillPgw = Collection(filepath=os.path.join(applied_masks_pgw, 'PotatoHill.nc'), name='Potato Hill')
CougarMountainPgw = Collection(filepath=os.path.join(applied_masks_pgw, 'CougarMountain.nc'), name='Cougar Mountain')

# /glade/derecho/scratch/meghan/Roza/froude/masked
# Rainier West	105
# Rainier East	105
# Naches West	120
# Naches East	120
# Naches River	105
# Upper Yakima South 120
# Upper Yakima North 105
# FrRainierEast = Collection(filepath=os.path.join(fr_root, 'froude_RainierEast.nc'), name='Rainier East')(phi=105)
# FrRainierWest = Collection(filepath=os.path.join(fr_root, 'froude_RainierWest.nc'), name='Rainier West')(phi=105)
# FrNachesRiver = Collection(filepath=os.path.join(fr_root, 'froude_NachesRiver.nc'), name='Naches River')(phi=105)
# FrUpperYakimaSouth = Collection(filepath=os.path.join(fr_root, 'froude_UpperYakimaSouth.nc'), name='Upper Yakima South')(phi=120)
# FrNachesEast = Collection(filepath=os.path.join(fr_root, 'froude_NachesEast.nc'), name='Naches East')(phi=120)
# FrUpperYakimaNorth = Collection(filepath=os.path.join(fr_root, 'froude_UpperYakimaNorth.nc'), name='Upper Yakima North')(phi=105)
# FrUpperYakimaSouth = Collection(filepath=os.path.join(fr_root, 'froude_UpperYakimaSouth.nc'), name='Froude Upper Yakima South')
# FrNachesWest = Collection(filepath=os.path.join(fr_root, 'froude_NachesWest.nc'), name='Naches West')(phi=120)
# FrGenA = Collection(filepath=os.path.join(fr_root, 'froude_gen_A.nc'), name='Gen A', phi=105, fr_var = 'FR_phi105_hoffset1500')
# FrGenE = Collection(filepath=os.path.join(fr_root, 'froude_gen_E.nc'), name='Gen E', phi=120, fr_var = 'FR_phi120_hoffset1500')
# FrGenE = Collection(filepath=os.path.join(fr_root, 'froude_gen_A.nc'), name='Gen E', phi=120, fr_var = 'FR_phi120_hoffset1500')
# FrA1 = Collection(filepath=os.path.join(fr_root, 'froude_A1.nc'), name='A1', phi=105, fr_var = 'FR')
# FrA2 = Collection(filepath=os.path.join(fr_root, 'froude_A2.nc'), name='A2', phi=105, fr_var = 'FR')
# FrA3 = Collection(filepath=os.path.join(fr_root, 'froude_A3.nc'), name='A3', phi=105, fr_var = 'FR')
# FrA4 = Collection(filepath=os.path.join(fr_root, 'froude_A4.nc'), name='A4', phi=105, fr_var = 'FR')
FrA5 = Collection(filepath=os.path.join(fr_root, 'froude_A5.nc'), name='A', phi=105, fr_var = 'FR')
# FrA6 = Collection(filepath=os.path.join(fr_root, 'froude_A6.nc'), name='A6', phi=105, fr_var = 'FR')
# FrE1 = Collection(filepath=os.path.join(fr_root, 'froude_E1.nc'), name='E1', phi=105, fr_var = 'FR')
# FrE2 = Collection(filepath=os.path.join(fr_root, 'froude_E2.nc'), name='E2', phi=105, fr_var = 'FR')
# FrE3 = Collection(filepath=os.path.join(fr_root, 'froude_E3.nc'), name='E3', phi=105, fr_var = 'FR')
# FrE4 = Collection(filepath=os.path.join(fr_root, 'froude_E4.nc'), name='E4', phi=105, fr_var = 'FR')
FrE5 = Collection(filepath=os.path.join(fr_root, 'froude_E5.nc'), name='E', phi=105, fr_var = 'FR')
# FrE6 = Collection(filepath=os.path.join(fr_root, 'froude_E6.nc'), name='E6', phi=105, fr_var = 'FR')
# FrE7 = Collection(filepath=os.path.join(fr_root, 'froude_E7.nc'), name='E7', phi=105, fr_var = 'FR')


class DataSourceEnum(enum.IntEnum):
    CONUS=0
    PGW=1

WindSwathT = collections.namedtuple('WindSwathT', ['min', 'max', 'label'])

class WindSwathEnum(enum.Enum):
    SSW=WindSwathT(180, 210, 'SSW')
    SWW=WindSwathT(210, 270, 'SWW')
    WNW=WindSwathT(270, 310, 'WNW')
    NWN=WindSwathT(310, 360, 'NWN')


# wind_swaths =[
#     dict(WindDirMin=180, WindDirMax=210, wind_label='SSW'),
#     dict(WindDirMin=210, WindDirMax=270, wind_label='SWW'),
#     dict(WindDirMin=270, WindDirMax=310, wind_label='WNW'),
#     dict(WindDirMin=310, WindDirMax=360, wind_label='NWN'),
# ]

_months=['','Jan','Feb','Mar', 'Apr','May','Jun','Jul','Aug','Sept','Oct','Nov','Dec']

@dataclass
class RgbColor:
    red_value: int=0
    green_value: int=0
    blue_value: int=0
    
    @property
    def hex(self):
        return f'#{self.red_value:02X}{self.green_value:02X}{self.blue_value:02X}'


ocean_blue = RgbColor(13,94,139)
tiffany_blue=RgbColor(109,242,210)
burnt_orange=RgbColor(176,58,5)
apricot=RgbColor(254,161,90)
firebrick=RgbColor(160,17,27)

# def calc_wind_swath_freq_for_month(month=11, data_source=DataSourceEnum.CONUS, wind_swath=WindSwathEnum.SSW):
#     import random
#     _months=['','Jan','Feb','Mar', 'Apr','May','Jun','Jul','Aug','Sept','Oct','Nov','Dec']
#     return {'Month':_months[month], 'SourceName':data_source.name,'SourceValue':data_source.value,'Swath':wind_swath.name,'Frequency':random.choice(range(5,50,10))}

def stacked_wind_frequency_monthly(precip=None, criteria=None, criteria_pgw=None, wind=None, wind_pgw=None, froude=None, verbose=None):
    logging.getLogger(__name__).info(f'Creating stacked_wind_frequency_monthly Chart for criteria: "{criteria.basename}", froude: "{froude.basename}", wind: "{wind.basename}" ({wind.wind_label})')

    _odf = merge_dfs(pd.DataFrame({'time':wind.Time, 'wind':wind.WindDir}))
    _odf_pgw = merge_dfs(pd.DataFrame({'time':wind_pgw.Time, 'wind':wind_pgw.WindDir}))
    
    def calc_wind_swath_freq_for_month(month=11, data_source=DataSourceEnum.CONUS, wind_swath=WindSwathEnum.SSW):
        __odf = _odf if data_source in [DataSourceEnum.CONUS] else _odf_pgw
        _month_df = __odf[__odf.index.month == month]
        _surface_df = _month_df[(_month_df['wind'] > wind_swath.value.min) & (_month_df['wind'] < wind_swath.value.max)]
        return {
            'Month':_months[month], 
            'Source':data_source.value,
            'Swath':wind_swath.name,
            'Frequency':(len(_surface_df)/len(_month_df))*100,
            # f'{data_source.name} {wind_swath.name} Wind Dir ({wind_swath.value.min}\xb0-{wind_swath.value.max}\xb0)':(len(_surface_df)/len(_month_df))*100,
            }

    df = pd.DataFrame.from_records([calc_wind_swath_freq_for_month(month=_month, data_source=_data_source, wind_swath=_swath) for _data_source in DataSourceEnum for _swath in WindSwathEnum for _month in [11,12,1,2,3,4]])
    df_conus = df[df['Source']==DataSourceEnum.CONUS]
    df_pgw = df[df['Source']==DataSourceEnum.PGW]
    pivot_conus = pd.pivot_table(data=df_conus, index=['Month'], columns=['Swath'], values='Frequency')
    pivot_pgw   = pd.pivot_table(data=df_pgw,   index=['Month'], columns=['Swath'], values='Frequency')

    # Plotting parameters
    bar_width = 0.3
    x_positions = range(len(pivot_conus.index))
    _colors=[ocean_blue.hex, tiffany_blue.hex, burnt_orange.hex, apricot.hex]

    fig, ax = plt.subplots(figsize=(18.5, 10.5))

    _=pivot_conus.plot.bar(ax=ax, width=bar_width, position=0, stacked=True, color=_colors, legend=False)
    _=[bar.set_hatch('x') for i, bar in enumerate(ax.patches)]
    _=pivot_pgw.plot.bar(  ax=ax, width=bar_width, position=1, stacked=True, color=_colors, legend=False)

    ax.set_xticks(x_positions)
    ax.set_xticklabels(pivot_conus.index)
    ax.set_xlabel('Month',fontsize =24)
    ax.set_ylabel('Frequency (%)', fontsize =24)
    fig.patch.set_facecolor('white')
    # ax.set_title('Two Stacked Bar Charts Side-by-Side')
    # model='CONUS404 Current and Future Climate'
    # criteria_name='Rainier West'
    # wind_name='Burnt Mountain'
    # froude_name='Rainier West'
    
    plt.yticks(fontsize=22)
    plt.xticks(fontsize=22)
    custom_legend_handles = [
        Patch(facecolor=ocean_blue.hex, label=f'{DataSourceEnum.CONUS.name} {WindSwathEnum.NWN.name}', hatch='x'),
        Patch(facecolor=tiffany_blue.hex, label=f'{DataSourceEnum.CONUS.name} {WindSwathEnum.SSW.name}', hatch='x'),
        Patch(facecolor=burnt_orange.hex, label=f'{DataSourceEnum.CONUS.name} {WindSwathEnum.SWW.name}', hatch='x'),
        Patch(facecolor=apricot.hex, label=f'{DataSourceEnum.CONUS.name} {WindSwathEnum.WNW.name}', hatch='x'),
        Patch(facecolor=ocean_blue.hex, label=f'{DataSourceEnum.PGW.name} {WindSwathEnum.NWN.name}'),
        Patch(facecolor=tiffany_blue.hex, label=f'{DataSourceEnum.PGW.name} {WindSwathEnum.SSW.name}'),
        Patch(facecolor=burnt_orange.hex, label=f'{DataSourceEnum.PGW.name} {WindSwathEnum.SWW.name}'),
        Patch(facecolor=apricot.hex, label=f'{DataSourceEnum.PGW.name} {WindSwathEnum.WNW.name}')]
    ax.legend(
        handles=custom_legend_handles, 
        loc='upper right', 
        # bbox_to_anchor=(1, 1), 
        fontsize=22, 
        ncol=2)
    _x_min, _x_max = plt.xlim()
    ax.set_xlim(_x_min, _x_max+0.5)
    ax.set_ylim(0, 120)
    ax.grid(True)
    fig.suptitle(f'Monthly Ground Wind Direction Frequency Stacked by Wind Swath\n {model} \n Region: {criteria.name} | Wind: {wind.name} | Froude: {froude.name}', fontsize = 26, fontweight='bold')
    output_name = f'comparison_monthly_ground_stacked_wind_swath{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_noPrecip.png'
    output_path = os.path.abspath(output_name)
    plt.savefig(output_path, dpi=300)
    logging.getLogger(__name__).info('Chart saved to "{}"'.format(output_path))
    plt.close()

def stacked_wind_frequency_yearly(precip=None, criteria=None, criteria_pgw=None, wind=None, wind_pgw=None, froude=None, verbose=None):
    logging.getLogger(__name__).info(f'Creating stacked_wind_frequency_yearly Seeding Frequency \n {model} \n Region: {criteria.name} | Wind: {wind.name}')

    wind_df = pd.DataFrame({'time':wind.Time, 'wind':wind.WindDir})
    wind_pgw_df = pd.DataFrame({'time':wind_pgw.Time, 'wind':wind_pgw.WindDir})
    _odf = merge_dfs(wind_df)
    _odf_pgw=merge_dfs(wind_pgw_df)

    def calc_wind_swath_match_for_year(year=2000, data_source=DataSourceEnum.CONUS, wind_swath=WindSwathEnum.SSW):
        logging.getLogger(__name__).debug('calc_lwc_criteria_match_for_year: {}'.format(year))
        __odf = _odf if data_source in [DataSourceEnum.CONUS] else _odf_pgw
        _pyear_df = __odf[(__odf.index.year == year-1) & (__odf.index.month>9)]
        _tyear_df = __odf[(__odf.index.year == year) & (__odf.index.month<5)]
        _year_df = pd.concat([_pyear_df, _tyear_df])
        _surface_df = _year_df[(_year_df['wind'] > wind_swath.value.min) & (_year_df['wind'] < wind_swath.value.max)]
        return {
            'Year':year, 
            'Source':data_source.value,
            'Swath':wind_swath.name,
            'Frequency':(len(_surface_df)/len(_year_df))*100}
    
    def get_avg(data):
        keys=list(data[0].keys())
        def _avg(_key): return sum(list(map(lambda x: x.get(_key), data)))/len(data)
        def _max(_key): return max(list(map(lambda x: x.get(_key), data)))
        _dd={_key:_avg(_key) for _key in keys}
        _dd.update({'year':'40 Yr Avg'})
        return _dd

    df = pd.DataFrame.from_records([calc_wind_swath_match_for_year(month=_month, data_source=_data_source, wind_swath=_swath) for _data_source in DataSourceEnum for _swath in WindSwathEnum for _month in [11,12,1,2,3,4]])
    df_conus = df[df['Source']==DataSourceEnum.CONUS]
    df_pgw   = df[df['Source']==DataSourceEnum.PGW]
    pivot_conus = pd.pivot_table(data=df_conus, index=['Year'], columns=['Swath'], values='Frequency')
    pivot_pgw   = pd.pivot_table(data=df_pgw,   index=['Year'], columns=['Swath'], values='Frequency')

    # Plotting parameters
    bar_width = 0.3
    x_positions = range(len(pivot_conus.index))
    _colors=[ocean_blue.hex, firebrick.hex, apricot.hex]

    fig, ax = plt.subplots(figsize=(18.5, 10.5))

    _=pivot_conus.plot.bar(ax=ax, width=bar_width, position=0, stacked=True, color=_colors, legend=False)
    _=[bar.set_hatch('x') for i, bar in enumerate(ax.patches)]
    _=pivot_pgw.plot.bar(  ax=ax, width=bar_width, position=1, stacked=True, color=_colors, legend=False)

    # ax.set_xticks(x_positions)
    # ax.set_xticklabels(pivot_conus.index)
    # ax.set_xlabel('Year',fontsize =24)
    # ax.set_ylabel('Frequency (%)', fontsize =24)
    # fig.patch.set_facecolor('white')
    # ax.set_title('Two Stacked Bar Charts Side-by-Side')
    # model='CONUS404 Current and Future Climate'
    # criteria_name='Rainier West'
    # wind_name='Burnt Mountain'
    # froude_name='Rainier West'
    
    plt.yticks(fontsize=22)
    plt.xticks(fontsize=22)
    custom_legend_handles = [
        Patch(facecolor=ocean_blue.hex, label=f'{DataSourceEnum.CONUS.name} {WindSwathEnum.NWN.name}', hatch='x'),
        Patch(facecolor=tiffany_blue.hex, label=f'{DataSourceEnum.CONUS.name} {WindSwathEnum.SSW.name}', hatch='x'),
        Patch(facecolor=burnt_orange.hex, label=f'{DataSourceEnum.CONUS.name} {WindSwathEnum.SWW.name}', hatch='x'),
        Patch(facecolor=apricot.hex, label=f'{DataSourceEnum.CONUS.name} {WindSwathEnum.WNW.name}', hatch='x'),
        Patch(facecolor=ocean_blue.hex, label=f'{DataSourceEnum.PGW.name} {WindSwathEnum.NWN.name}'),
        Patch(facecolor=tiffany_blue.hex, label=f'{DataSourceEnum.PGW.name} {WindSwathEnum.SSW.name}'),
        Patch(facecolor=burnt_orange.hex, label=f'{DataSourceEnum.PGW.name} {WindSwathEnum.SWW.name}'),
        Patch(facecolor=apricot.hex, label=f'{DataSourceEnum.PGW.name} {WindSwathEnum.WNW.name}')]
    ax.legend(
        handles=custom_legend_handles, 
        loc='upper right', 
        # bbox_to_anchor=(1, 1), 
        fontsize=22, 
        ncol=2)
    # _x_min, _x_max = plt.xlim()
    # ax.set_xlim(_x_min, _x_max+0.5)
    ax.set_xlim(1980, 2021)
    ax.grid(True)

    # _colors=['ocean blue','firebrick','apricot']
    # ax=df.plot(kind='line',rot=45,color=_colors)
    # pgw_df.plot(ax=ax,kind='line', linestyle = '--', rot=45,color=_colors)

    jj=0
    for kk, vv in _cavg.items():
        if kk in ['year']: continue
        # ax.axhline(vv, ls='-.', label=f'40 Yr Avg({kk})', color=_colors[jj], xmin=1980, xmax=2021, transform=ax.transData)
        ax.axhline(vv, ls='-.', label=f'40 Yr Avg({kk})', color=_colors[jj])
        jj+=1
    
    jj=0
    for kk, vv in _pavg.items():
        if kk in ['year']: continue
        # ax.axhline(vv, ls='-.', label=f'40 Yr Avg({kk})', color=_colors[jj], xmin=1980, xmax=2021, transform=ax.transData)
        ax.axhline(vv, ls=':', label=f'40 Yr Avg({kk})', color=_colors[jj])
        jj+=1

    plt.title(f'Yearly Ground Seeding Frequency \n {model} \n Region: {criteria.name} | Wind: {wind.name} | Froude: {froude.name}', fontsize = 26, fontweight='bold')
    
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.xaxis.set_minor_locator(AutoMinorLocator())

    fig.canvas.draw()

    ax.set_xlabel('Year',fontsize =24)
    ax.set_ylabel('Frequency (%)', fontsize =24)
    fig.patch.set_facecolor('white')
    output_name = f'comparison_yearly_ground_stacked_wind_swath_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}.png'
    output_path = os.path.abspath(output_name)
    plt.savefig(output_path, dpi=300)
    logging.getLogger(__name__).info('Chart saved to "{}"'.format(output_path))
    plt.close()

def stacked_wind_frequency_combined(precip=None, criteria=None, criteria_pgw=None, wind=None, wind_pgw=None, froude=None, verbose=None):
    pass

def frequency_heatmap(precip=None, criteria=None, criteria_pgw=None, wind=None, wind_pgw=None, froude=None, verbose=None):
    plt.rcParams.update({'font.size': 20})
    logging.getLogger(__name__).info(f'Creating Frequency Heatmaps for criteria: "{criteria.basename}", wind: "{wind.basename}", froude: "{froude.basename}"')

    criteria_df = pd.DataFrame({'time':criteria.Time, 'temp':criteria.Ground_Temp, 'lwc':criteria.Ground_LWC})
    criteria_pgw_df = pd.DataFrame({'time':criteria_pgw.Time, 'temp':criteria_pgw.Ground_Temp, 'lwc':criteria_pgw.Ground_LWC})
    
    wind_df = pd.DataFrame({'time':wind.Time, 'wind':wind.WindDir})
    wind_pgw_df = pd.DataFrame({'time':wind_pgw.Time, 'wind':wind_pgw.WindDir})
    
    froude_df = pd.DataFrame({'time':froude.Time, 'Fr':froude.FR})
    
    _odf_gnd = merge_dfs(criteria_df, wind_df, froude_df)
    _odf_gnd_pgw = merge_dfs(criteria_pgw_df, wind_pgw_df, froude_df)
    
    criteria_air_df = pd.DataFrame({'time':criteria.Time, 'temp':criteria.Air_Temp, 'lwc':criteria.Air_LWC})
    criteria_air_pgw_df = pd.DataFrame({'time':criteria_pgw.Time, 'temp':criteria_pgw.Air_Temp, 'lwc':criteria_pgw.Air_LWC})
    
    _odf_air = merge_dfs(criteria_air_df)
    _odf_air_pgw = merge_dfs(criteria_air_pgw_df)

    _months=['','Jan','Feb','Mar', 'Apr','May','Jun','Jul','Aug','Sept','Oct','Nov','Dec']

    def calc_lwc_criteria_match_for_month(month=11, data_source=DataSourceEnum.CONUS, strata=LwcType.GROUND):
        if strata == LwcType.GROUND:
            __odf=_odf_gnd_pgw if data_source==DataSourceEnum.PGW else _odf_gnd
        else:
            __odf=_odf_air_pgw if data_source==DataSourceEnum.PGW else _odf_air

        _month_df = __odf[__odf.index.month == month]

        def calc_lwc_criteria_match_for_month_hour(hour=1):
            _hour_df = _month_df[_month_df.index.hour == hour]
            _crit_df = _hour_df[(_hour_df['temp'] < -6) & (_hour_df['temp'] > -18) & (_hour_df['lwc'] > 0.01)]
            if strata == LwcType.GROUND:
                # _crit_df = _month_df[(_month_df['temp'] < -6) & (_month_df['temp'] > -18) & (_month_df['lwc'] > 0.01) & (_month_df['wind'] > wind_swath.value.min) & (_month_df['wind'] < wind_swath.value.max)]
                _crit_df = _crit_df[(_crit_df['wind'] > wind.WindDirMin) & (_crit_df['wind'] < wind.WindDirMax) & (_crit_df['Fr'] > 0.4999)]

            return {
                'Month':_months[month], 
                'Hour':hour,
                'Source':data_source.value,
                'Strata':strata.value,
                'Frequency':(len(_crit_df)/len(_hour_df))*100}
        
        return [calc_lwc_criteria_match_for_month_hour(hour=_hour) for _hour in sorted(_month_df.index.hour.unique())]
    
    def calc_lwc_criteria_match_for_month_stub(month=11, data_source=DataSourceEnum.CONUS, strata=LwcType.GROUND):
        def calc_lwc_criteria_match_for_month_hour(hour=1):return {'Month':_months[month], 'Hour':hour,'Source':data_source.value,'Strata':strata.value,'Frequency':random.choice(range(5,50,10))}
        return [calc_lwc_criteria_match_for_month_hour(hour=_hour) for _hour in range(0, 25)]

    monthly_data = list(itertools.chain.from_iterable([calc_lwc_criteria_match_for_month(month=_month, data_source=_data_source, strata=_strata) for _data_source in DataSourceEnum for _strata in LwcType for _month in [11,12,1,2,3,4]]))
    # test_monthly_data = list(itertools.chain.from_iterable([calc_lwc_criteria_match_for_month_stub(month=_month, data_source=_data_source, strata=_strata) for _data_source in DataSourceEnum for _strata in LwcType for _month in [11,12,1,2,3,4]]))
    # monthly_data=test_monthly_data
    df = pd.DataFrame.from_records(monthly_data)

    df_gnd_conus = df[(df['Source']==DataSourceEnum.CONUS) & (df['Strata']==LwcType.GROUND)].copy()
    df_gnd_pgw =   df[(df['Source']==DataSourceEnum.PGW)   & (df['Strata']==LwcType.GROUND)].copy()
    df_air_conus = df[(df['Source']==DataSourceEnum.CONUS) & (df['Strata']==LwcType.AIR)].copy()
    df_air_pgw =   df[(df['Source']==DataSourceEnum.PGW)   & (df['Strata']==LwcType.AIR)].copy()

    _pivot_gnd_conus = pd.pivot_table(data=df_gnd_conus, index=['Hour'], columns=['Month'], values='Frequency')
    _pivot_gnd_pgw   = pd.pivot_table(data=df_gnd_pgw,   index=['Hour'], columns=['Month'], values='Frequency')
    _pivot_air_conus = pd.pivot_table(data=df_air_conus, index=['Hour'], columns=['Month'], values='Frequency')
    _pivot_air_pgw   = pd.pivot_table(data=df_air_pgw,   index=['Hour'], columns=['Month'], values='Frequency')

    _pivot_gnd_conus.sort_index(level=0, ascending=False, inplace=True)
    _pivot_gnd_pgw.sort_index(level=0, ascending=False, inplace=True)
    _pivot_air_conus.sort_index(level=0, ascending=False, inplace=True)
    _pivot_air_pgw.sort_index(level=0, ascending=False, inplace=True)

    column_order=['Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr']
    pivot_gnd_conus=_pivot_gnd_conus.reindex(column_order, axis=1)
    pivot_gnd_pgw=_pivot_gnd_pgw.reindex(column_order, axis=1)
    pivot_air_conus=_pivot_air_conus.reindex(column_order, axis=1)
    pivot_air_pgw=_pivot_air_pgw.reindex(column_order, axis=1)

    logging.getLogger(__name__).debug(f'{df=}')
    logging.getLogger(__name__).debug(f'{df_gnd_conus=}')
    logging.getLogger(__name__).debug(f'{df_gnd_pgw=}')
    logging.getLogger(__name__).debug(f'{df_air_conus=}')
    logging.getLogger(__name__).debug(f'{df_air_pgw=}')
    logging.getLogger(__name__).debug(f'{pivot_gnd_conus=}')
    logging.getLogger(__name__).debug(f'{pivot_gnd_pgw=}')
    logging.getLogger(__name__).debug(f'{pivot_air_conus=}')
    logging.getLogger(__name__).debug(f'{pivot_air_pgw=}')

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(19.5, 13.5))
    _cax = plt.axes((0.17, 0.05, 0.68, 0.015), anchor='C')
    ax2_2 = ax2.twinx()
    ax4_2 = ax4.twinx()

    _hm_kwargs=dict(vmin=0, vmax=35) # math.ceil(df['Frequency'].max())) #, linewidth=.5)
    # _annotate=True
    _annotate=False

    _hms=[]
    _hms.append(sns.heatmap(pivot_air_conus, ax=ax1, annot=_annotate, cmap='viridis', cbar_ax=_cax,
                            cbar_kws=dict(shrink=0.75,label='Frequency (%)',orientation='horizontal'),
                            # xticklabels=False, yticklabels=True,
                            **_hm_kwargs))
    ax1.set_title('CONUS404', fontweight='bold', fontsize=22)
    ax1.set_xticklabels([])
    ax1.set_xticks([])
    ax1.set_xlabel('')
    # ax1.set_ylabel('Hour', fontsize=20, fontweight='bold')
    # ax1.tick_params(axis='y', labelrotation=0)#, labelsize=20)
    ax1.tick_params(axis='both', which='major', labelsize=20)

    _hms.append(sns.heatmap(pivot_air_pgw,   ax=ax2, annot=_annotate, cmap='viridis', cbar=False, 
                            # xticklabels=False, yticklabels=False, 
                            **_hm_kwargs))
    ax2.set_title('PGW', fontweight='bold', fontsize=22)
    ax2.yaxis.tick_right()
    ax2.yaxis.set_label_position("right")
    # ax1.set_ylabel('Hour', fontsize=20, fontweight='bold')
    # ax2.tick_params(axis='y', labelrotation=0)#, labelsize=20)
    ax2.tick_params(axis='both', which='major', labelsize=20)
    ax2_2.yaxis.set_label_position("right")
    ax2.set_xticklabels([])
    ax2.set_xticks([])
    ax2_2.set_ylabel('Air', labelpad=70, fontsize=22)#, fontweight='bold')
    ax2_2.set_yticklabels([])
    ax2_2.set_yticks([])
    ax2_2.yaxis.label.set_rotation(0)
    ax2_2.tick_params(axis='both', which='major', labelsize=20)

    _hms.append(sns.heatmap(pivot_gnd_conus, ax=ax3, annot=_annotate, cmap='viridis', cbar=False, 
                            # xticklabels=False, yticklabels=True, 
                            **_hm_kwargs))
    # ax3.tick_params(axis='y', labelrotation=0)#, labelsize=20)
    ax3.tick_params(axis='both', which='major', labelsize=20)
    # ax3.set_ylabel('Hour', fontsize=20, fontweight='bold')
    # ax3.set_xlabel('Month', fontsize=20, fontweight='bold')
    # ax3.tick_params(axis='x', labelsize=20)

    _hms.append(sns.heatmap(pivot_gnd_pgw,   ax=ax4, annot=_annotate, cmap='viridis', cbar=False,
                            # xticklabels=False, yticklabels=False, 
                            **_hm_kwargs))
    ax4.yaxis.tick_right()
    ax4.yaxis.set_label_position("right")
    # ax4.tick_params(axis='y', labelrotation=0)#, labelsize=20)
    ax4.tick_params(axis='both', which='major', labelsize=20)
    # ax4.set_ylabel('Hour', fontsize=20, fontweight='bold')
    # ax4.set_xlabel('Month', fontsize=20, fontweight='bold')
    ax4_2.yaxis.set_label_position("right")
    ax4_2.set_ylabel('Ground', labelpad=75, fontsize=22)#, fontweight='bold')
    ax4_2.set_yticklabels([])
    ax4_2.set_yticks([])
    ax4_2.yaxis.label.set_rotation(0)
    ax4_2.tick_params(axis='both', which='major', labelsize=20)

    fig.subplots_adjust(wspace=0.005, hspace=0.01)
    # _cax.tick_params(labelsize=12)
    # _cax.set_label('Frequency (%)', size=22)

    fig.suptitle(f'Seedable Conditions Frequency Heatmap -- Month-Hour Aggregate\nRegion: {criteria.name} | Surface: {wind.name}', fontsize=26)

    output_name = f'seedable_conditions_frequency_heatmap_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_noPrecip.png'
    output_path = os.path.abspath(output_name)
    plt.savefig(output_path, dpi=300)
    logging.getLogger(__name__).info('Chart saved to "{}"'.format(output_path))
    plt.close()

# _wind_swath=dict(WindDirMin=210, WindDirMax=320)


# create_monthly_airborne=True
create_monthly_airborne=False
if create_monthly_airborne:
    create_monthly_airborne_freq_chart(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        # froude=FrGenA
        )
    create_monthly_airborne_freq_chart(
        criteria=UpperYakimaSouth, 
        criteria_pgw=UpperYakimaSouthPgw, 
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        # froude=FrGenA
        )
    create_monthly_airborne_freq_chart(
        criteria=UpperYakimaNorth, 
        criteria_pgw=UpperYakimaNorthPgw, 
        wind=FishLake(WindDirMin=225, WindDirMax=315),
        wind_pgw=FishLakePgw(WindDirMin=225, WindDirMax=315),
        # froude=FrGenA
        )
    create_monthly_airborne_freq_chart(
        criteria=UpperYakimaSouth, 
        criteria_pgw=UpperYakimaSouthPgw, 
        wind=SasseRidge(WindDirMin=210, WindDirMax=315),
        wind_pgw=SasseRidgePgw(WindDirMin=210, WindDirMax=315),
        # froude=FrGenA
        )
    create_monthly_airborne_freq_chart(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=CougarMountain(WindDirMin=225, WindDirMax=320),
        wind_pgw=CougarMountainPgw(WindDirMin=225, WindDirMax=320),
        # froude=FrGenA
        )

    create_monthly_airborne_freq_chart(
        criteria=RainierWest,      
        criteria_pgw=RainierWestPgw,      
        wind=BurntMountain(WindDirMin=225, WindDirMax=315),
        wind_pgw=BurntMountainPgw(WindDirMin=225, WindDirMax=315),
        # froude=FrGenE
        )
    create_monthly_airborne_freq_chart(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        # froude=FrGenE
        )
    create_monthly_airborne_freq_chart(
        criteria=NachesEast,       
        criteria_pgw=NachesEastPgw,       
        wind=CayusePass(WindDirMin=225, WindDirMax=315),
        wind_pgw=CayusePassPgw(WindDirMin=225, WindDirMax=315),
        # froude=FrGenE
        )
    create_monthly_airborne_freq_chart(
        criteria=NachesEast,       
        criteria_pgw=NachesEastPgw,       
        wind=BumpingRidge(WindDirMin=240, WindDirMax=320),
        wind_pgw=BumpingRidgePgw(WindDirMin=240, WindDirMax=320),
        # froude=FrGenE
        )
    create_monthly_airborne_freq_chart(
        criteria=RainierEast,      
        criteria_pgw=RainierEastPgw,      
        wind=CorralPass(WindDirMin=225, WindDirMax=320),
        wind_pgw=CorralPassPgw(WindDirMin=225, WindDirMax=320),
        # froude=FrGenE
        )
    create_monthly_airborne_freq_chart(
        criteria=NachesWest,       
        criteria_pgw=NachesWestPgw,       
        wind=PotatoHill(WindDirMin=225, WindDirMax=320),
        wind_pgw=PotatoHillPgw(WindDirMin=225, WindDirMax=320),
        # froude=FrGenE
        )
    create_monthly_airborne_freq_chart(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=CougarMountain(WindDirMin=225, WindDirMax=320),
        wind_pgw=CougarMountainPgw(WindDirMin=225, WindDirMax=320),
        # froude=FrGenE
        )
    create_monthly_airborne_freq_chart(
        criteria=NachesWest,       
        criteria_pgw=NachesWestPgw,       
        wind=SkateCreek(WindDirMin=215, WindDirMax=320),
        wind_pgw=SkateCreekPgw(WindDirMin=215, WindDirMax=320),
        # froude=FrGenE
        )
    logging.getLogger(__name__).info('All done with "create_monthly_airborne"!!')

# for ii, _phi in enumerate(FrA1.phi_range):
FrA_phi=240
FrE_phi=90
create_heatmap=True
# create_heatmap=False
if create_heatmap:
    # for FrGenA in [FrA1, FrA2, FrA3, FrA4, FrA5, FrA6]:
    FrGenA=FrA5(phi=FrA_phi)
    frequency_heatmap(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    frequency_heatmap(
        criteria=UpperYakimaSouth, 
        criteria_pgw=UpperYakimaSouthPgw, 
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    frequency_heatmap(
        criteria=UpperYakimaNorth, 
        criteria_pgw=UpperYakimaNorthPgw, 
        wind=FishLake(WindDirMin=225, WindDirMax=315),
        wind_pgw=FishLakePgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenA)
    frequency_heatmap(
        criteria=UpperYakimaSouth, 
        criteria_pgw=UpperYakimaSouthPgw, 
        wind=SasseRidge(WindDirMin=210, WindDirMax=315),
        wind_pgw=SasseRidgePgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    frequency_heatmap(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=CougarMountain(WindDirMin=225, WindDirMax=320),
        wind_pgw=CougarMountainPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenA)
    # for FrGenE in [FrE1, FrE2, FrE3, FrE4, FrE5, FrE6, FrE7]:
    #     FrGenE=FrGenE(phi=_phi)
    FrGenE=FrE5(phi=FrE_phi)
    frequency_heatmap(
        criteria=RainierWest,      
        criteria_pgw=RainierWestPgw,      
        wind=BurntMountain(WindDirMin=225, WindDirMax=315),
        wind_pgw=BurntMountainPgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenE)
    frequency_heatmap(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenE)
    frequency_heatmap(
        criteria=NachesEast,       
        criteria_pgw=NachesEastPgw,       
        wind=CayusePass(WindDirMin=225, WindDirMax=315),
        wind_pgw=CayusePassPgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenE)
    frequency_heatmap(
        criteria=NachesEast,       
        criteria_pgw=NachesEastPgw,       
        wind=BumpingRidge(WindDirMin=240, WindDirMax=320),
        wind_pgw=BumpingRidgePgw(WindDirMin=240, WindDirMax=320),
        froude=FrGenE)
    frequency_heatmap(
        criteria=RainierEast,      
        criteria_pgw=RainierEastPgw,      
        wind=CorralPass(WindDirMin=225, WindDirMax=320),
        wind_pgw=CorralPassPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    frequency_heatmap(
        criteria=NachesWest,       
        criteria_pgw=NachesWestPgw,       
        wind=PotatoHill(WindDirMin=225, WindDirMax=320),
        wind_pgw=PotatoHillPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    frequency_heatmap(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=CougarMountain(WindDirMin=225, WindDirMax=320),
        wind_pgw=CougarMountainPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    frequency_heatmap(
        criteria=NachesWest,       
        criteria_pgw=NachesWestPgw,       
        wind=SkateCreek(WindDirMin=215, WindDirMax=320),
        wind_pgw=SkateCreekPgw(WindDirMin=215, WindDirMax=320),
        froude=FrGenE)
    logging.getLogger(__name__).info('All done with "heatmaps"!!')


# create_monthly_stacked_wind=True
create_monthly_stacked_wind=False
if create_monthly_stacked_wind:
    FrGenA=FrA5(phi=FrA_phi)
    stacked_wind_frequency_monthly(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    stacked_wind_frequency_monthly(
        criteria=UpperYakimaSouth, 
        criteria_pgw=UpperYakimaSouthPgw, 
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    stacked_wind_frequency_monthly(
        criteria=UpperYakimaNorth, 
        criteria_pgw=UpperYakimaNorthPgw, 
        wind=FishLake(WindDirMin=225, WindDirMax=315),
        wind_pgw=FishLakePgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenA)
    stacked_wind_frequency_monthly(
        criteria=UpperYakimaSouth, 
        criteria_pgw=UpperYakimaSouthPgw, 
        wind=SasseRidge(WindDirMin=210, WindDirMax=315),
        wind_pgw=SasseRidgePgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    stacked_wind_frequency_monthly(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=CougarMountain(WindDirMin=225, WindDirMax=320),
        wind_pgw=CougarMountainPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenA)
    

    FrGenE=FrE5(phi=FrE_phi)
    stacked_wind_frequency_monthly(
        criteria=RainierWest,      
        criteria_pgw=RainierWestPgw,      
        wind=BurntMountain(WindDirMin=225, WindDirMax=315),
        wind_pgw=BurntMountainPgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenE)
    stacked_wind_frequency_monthly(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenE)
    stacked_wind_frequency_monthly(
        criteria=NachesEast,       
        criteria_pgw=NachesEastPgw,       
        wind=CayusePass(WindDirMin=225, WindDirMax=315),
        wind_pgw=CayusePassPgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenE)
    stacked_wind_frequency_monthly(
        criteria=NachesEast,       
        criteria_pgw=NachesEastPgw,       
        wind=BumpingRidge(WindDirMin=240, WindDirMax=320),
        wind_pgw=BumpingRidgePgw(WindDirMin=240, WindDirMax=320),
        froude=FrGenE)
    stacked_wind_frequency_monthly(
        criteria=RainierEast,      
        criteria_pgw=RainierEastPgw,      
        wind=CorralPass(WindDirMin=225, WindDirMax=320),
        wind_pgw=CorralPassPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    stacked_wind_frequency_monthly(
        criteria=NachesWest,       
        criteria_pgw=NachesWestPgw,       
        wind=PotatoHill(WindDirMin=225, WindDirMax=320),
        wind_pgw=PotatoHillPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    stacked_wind_frequency_monthly(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=CougarMountain(WindDirMin=225, WindDirMax=320),
        wind_pgw=CougarMountainPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    stacked_wind_frequency_monthly(
        criteria=NachesWest,       
        criteria_pgw=NachesWestPgw,       
        wind=SkateCreek(WindDirMin=215, WindDirMax=320),
        wind_pgw=SkateCreekPgw(WindDirMin=215, WindDirMax=320),
        froude=FrGenE)
    logging.getLogger(__name__).info('All done with "create_monthly_stacked_wind"!!')


    # for ii, _wind_swath in enumerate(wind_swaths):
    # for ii, _wind_swath in enumerate([dict(WindDirMin=210, WindDirMax=320)]):
# create_monthly_ground=True
create_monthly_ground=False
if create_monthly_ground:
    FrGenA=FrA5(phi=FrA_phi)
    create_freq_chart(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    create_freq_chart(
        criteria=UpperYakimaSouth, 
        criteria_pgw=UpperYakimaSouthPgw, 
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    create_freq_chart(
        criteria=UpperYakimaNorth, 
        criteria_pgw=UpperYakimaNorthPgw, 
        wind=FishLake(WindDirMin=225, WindDirMax=315),
        wind_pgw=FishLakePgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenA)
    create_freq_chart(
        criteria=UpperYakimaSouth, 
        criteria_pgw=UpperYakimaSouthPgw, 
        wind=SasseRidge(WindDirMin=210, WindDirMax=315),
        wind_pgw=SasseRidgePgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    create_freq_chart(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=CougarMountain(WindDirMin=225, WindDirMax=320),
        wind_pgw=CougarMountainPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenA)
    
    FrGenE=FrE5(phi=FrE_phi)
    create_freq_chart(
        criteria=RainierWest,      
        criteria_pgw=RainierWestPgw,      
        wind=BurntMountain(WindDirMin=225, WindDirMax=315),
        wind_pgw=BurntMountainPgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenE)
    create_freq_chart(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenE)
    create_freq_chart(
        criteria=NachesEast,       
        criteria_pgw=NachesEastPgw,       
        wind=CayusePass(WindDirMin=225, WindDirMax=315),
        wind_pgw=CayusePassPgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenE)
    create_freq_chart(
        criteria=NachesEast,       
        criteria_pgw=NachesEastPgw,       
        wind=BumpingRidge(WindDirMin=240, WindDirMax=320),
        wind_pgw=BumpingRidgePgw(WindDirMin=240, WindDirMax=320),
        froude=FrGenE)
    create_freq_chart(
        criteria=RainierEast,      
        criteria_pgw=RainierEastPgw,      
        wind=CorralPass(WindDirMin=225, WindDirMax=320),
        wind_pgw=CorralPassPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    create_freq_chart(
        criteria=NachesWest,       
        criteria_pgw=NachesWestPgw,       
        wind=PotatoHill(WindDirMin=225, WindDirMax=320),
        wind_pgw=PotatoHillPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    create_freq_chart(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=CougarMountain(WindDirMin=225, WindDirMax=320),
        wind_pgw=CougarMountainPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    create_freq_chart(
        criteria=NachesWest,       
        criteria_pgw=NachesWestPgw,       
        wind=SkateCreek(WindDirMin=215, WindDirMax=320),
        wind_pgw=SkateCreekPgw(WindDirMin=215, WindDirMax=320),
        froude=FrGenE)
    logging.getLogger(__name__).info('All done with "create_monthly_ground"!!')

        


# create_yearly_ground = True
create_yearly_ground = False
if create_yearly_ground:
    FrGenA=FrA5(phi=FrA_phi)
    create_yearly_chart(
        lwc_type=LwcType.GROUND,
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    create_yearly_chart(
        lwc_type=LwcType.GROUND,
        criteria=UpperYakimaSouth, 
        criteria_pgw=UpperYakimaSouthPgw, 
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    create_yearly_chart(
        lwc_type=LwcType.GROUND,
        criteria=UpperYakimaNorth, 
        criteria_pgw=UpperYakimaNorthPgw, 
        wind=FishLake(WindDirMin=225, WindDirMax=315),
        wind_pgw=FishLakePgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenA)
    create_yearly_chart(
        lwc_type=LwcType.GROUND,
        criteria=UpperYakimaSouth, 
        criteria_pgw=UpperYakimaSouthPgw, 
        wind=SasseRidge(WindDirMin=210, WindDirMax=315),
        wind_pgw=SasseRidgePgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    create_yearly_chart(
        lwc_type=LwcType.GROUND,
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=CougarMountain(WindDirMin=225, WindDirMax=320),
        wind_pgw=CougarMountainPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenA)
    
    FrGenE=FrE5(phi=FrE_phi)
    create_yearly_chart(
        lwc_type=LwcType.GROUND,
        criteria=RainierWest,      
        criteria_pgw=RainierWestPgw,      
        wind=BurntMountain(WindDirMin=225, WindDirMax=315),
        wind_pgw=BurntMountainPgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenE)
    create_yearly_chart(
        lwc_type=LwcType.GROUND,
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenE)
    create_yearly_chart(
        lwc_type=LwcType.GROUND,
        criteria=NachesEast,       
        criteria_pgw=NachesEastPgw,       
        wind=CayusePass(WindDirMin=225, WindDirMax=315),
        wind_pgw=CayusePassPgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenE)
    create_yearly_chart(
        lwc_type=LwcType.GROUND,
        criteria=NachesEast,       
        criteria_pgw=NachesEastPgw,       
        wind=BumpingRidge(WindDirMin=240, WindDirMax=320),
        wind_pgw=BumpingRidgePgw(WindDirMin=240, WindDirMax=320),
        froude=FrGenE)
    create_yearly_chart(
        lwc_type=LwcType.GROUND,
        criteria=RainierEast,      
        criteria_pgw=RainierEastPgw,      
        wind=CorralPass(WindDirMin=225, WindDirMax=320),
        wind_pgw=CorralPassPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    create_yearly_chart(
        lwc_type=LwcType.GROUND,
        criteria=NachesWest,       
        criteria_pgw=NachesWestPgw,       
        wind=PotatoHill(WindDirMin=225, WindDirMax=320),
        wind_pgw=PotatoHillPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    create_yearly_chart(
        lwc_type=LwcType.GROUND,
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=CougarMountain(WindDirMin=225, WindDirMax=320),
        wind_pgw=CougarMountainPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    create_yearly_chart(
        lwc_type=LwcType.GROUND,
        criteria=NachesWest,       
        criteria_pgw=NachesWestPgw,       
        wind=SkateCreek(WindDirMin=215, WindDirMax=320),
        wind_pgw=SkateCreekPgw(WindDirMin=215, WindDirMax=320),
        froude=FrGenE)
    logging.getLogger(__name__).info('All done with "create_yearly_ground"!!')

# create_yearly_air = True
create_yearly_air = False
if create_yearly_air:
    FrGenA=FrA5(phi=FrA_phi)
    create_yearly_chart(
        lwc_type=LwcType.AIR,
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    create_yearly_chart(
        lwc_type=LwcType.AIR,
        criteria=UpperYakimaSouth, 
        criteria_pgw=UpperYakimaSouthPgw, 
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    create_yearly_chart(
        lwc_type=LwcType.AIR,
        criteria=UpperYakimaNorth, 
        criteria_pgw=UpperYakimaNorthPgw, 
        wind=FishLake(WindDirMin=225, WindDirMax=315),
        wind_pgw=FishLakePgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenA)
    create_yearly_chart(
        lwc_type=LwcType.AIR,
        criteria=UpperYakimaSouth, 
        criteria_pgw=UpperYakimaSouthPgw, 
        wind=SasseRidge(WindDirMin=210, WindDirMax=315),
        wind_pgw=SasseRidgePgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    create_yearly_chart(
        lwc_type=LwcType.AIR,
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=CougarMountain(WindDirMin=225, WindDirMax=320),
        wind_pgw=CougarMountainPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenA)
    FrGenE=FrE5(phi=FrE_phi)
    create_yearly_chart(
        lwc_type=LwcType.AIR,
        criteria=RainierWest,      
        criteria_pgw=RainierWestPgw,      
        wind=BurntMountain(WindDirMin=225, WindDirMax=315),
        wind_pgw=BurntMountainPgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenE)
    create_yearly_chart(
        lwc_type=LwcType.AIR,
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenE)
    create_yearly_chart(
        lwc_type=LwcType.AIR,
        criteria=NachesEast,       
        criteria_pgw=NachesEastPgw,       
        wind=CayusePass(WindDirMin=225, WindDirMax=315),
        wind_pgw=CayusePassPgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenE)
    create_yearly_chart(
        lwc_type=LwcType.AIR,
        criteria=NachesEast,       
        criteria_pgw=NachesEastPgw,       
        wind=BumpingRidge(WindDirMin=240, WindDirMax=320),
        wind_pgw=BumpingRidgePgw(WindDirMin=240, WindDirMax=320),
        froude=FrGenE)
    create_yearly_chart(
        lwc_type=LwcType.AIR,
        criteria=RainierEast,      
        criteria_pgw=RainierEastPgw,      
        wind=CorralPass(WindDirMin=225, WindDirMax=320),
        wind_pgw=CorralPassPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    create_yearly_chart(
        lwc_type=LwcType.AIR,
        criteria=NachesWest,       
        criteria_pgw=NachesWestPgw,       
        wind=PotatoHill(WindDirMin=225, WindDirMax=320),
        wind_pgw=PotatoHillPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    create_yearly_chart(
        lwc_type=LwcType.AIR,
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=CougarMountain(WindDirMin=225, WindDirMax=320),
        wind_pgw=CougarMountainPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    create_yearly_chart(
        lwc_type=LwcType.AIR,
        criteria=NachesWest,       
        criteria_pgw=NachesWestPgw,       
        wind=SkateCreek(WindDirMin=215, WindDirMax=320),
        wind_pgw=SkateCreekPgw(WindDirMin=215, WindDirMax=320),
        froude=FrGenE)
    logging.getLogger(__name__).info('All done with "create_yearly_air"!!')
            
# create_monthly_combined = True
create_monthly_combined = False
if create_monthly_combined:
    FrGenA=FrA5(phi=FrA_phi)
    create_monthly_combined_chart(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    create_monthly_combined_chart(
        criteria=UpperYakimaSouth, 
        criteria_pgw=UpperYakimaSouthPgw, 
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    create_monthly_combined_chart(
        criteria=UpperYakimaNorth, 
        criteria_pgw=UpperYakimaNorthPgw, 
        wind=FishLake(WindDirMin=225, WindDirMax=315),
        wind_pgw=FishLakePgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenA)
    create_monthly_combined_chart(
        criteria=UpperYakimaSouth, 
        criteria_pgw=UpperYakimaSouthPgw, 
        wind=SasseRidge(WindDirMin=210, WindDirMax=315),
        wind_pgw=SasseRidgePgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenA)
    create_monthly_combined_chart(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=CougarMountain(WindDirMin=225, WindDirMax=320),
        wind_pgw=CougarMountainPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenA)
    
    FrGenE=FrE5(phi=FrE_phi)
    create_monthly_combined_chart(
        criteria=RainierWest,      
        criteria_pgw=RainierWestPgw,      
        wind=BurntMountain(WindDirMin=225, WindDirMax=315),
        wind_pgw=BurntMountainPgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenE)
    create_monthly_combined_chart(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=MeadowsPass(WindDirMin=210, WindDirMax=315),
        wind_pgw=MeadowsPassPgw(WindDirMin=210, WindDirMax=315),
        froude=FrGenE)
    create_monthly_combined_chart(
        criteria=NachesEast,       
        criteria_pgw=NachesEastPgw,       
        wind=CayusePass(WindDirMin=225, WindDirMax=315),
        wind_pgw=CayusePassPgw(WindDirMin=225, WindDirMax=315),
        froude=FrGenE)
    create_monthly_combined_chart(
        criteria=NachesEast,       
        criteria_pgw=NachesEastPgw,       
        wind=BumpingRidge(WindDirMin=240, WindDirMax=320),
        wind_pgw=BumpingRidgePgw(WindDirMin=240, WindDirMax=320),
        froude=FrGenE)
    create_monthly_combined_chart(
        criteria=RainierEast,      
        criteria_pgw=RainierEastPgw,      
        wind=CorralPass(WindDirMin=225, WindDirMax=320),
        wind_pgw=CorralPassPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    create_monthly_combined_chart(
        criteria=NachesWest,       
        criteria_pgw=NachesWestPgw,       
        wind=PotatoHill(WindDirMin=225, WindDirMax=320),
        wind_pgw=PotatoHillPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    create_monthly_combined_chart(
        criteria=NachesRiver,      
        criteria_pgw=NachesRiverPgw,      
        wind=CougarMountain(WindDirMin=225, WindDirMax=320),
        wind_pgw=CougarMountainPgw(WindDirMin=225, WindDirMax=320),
        froude=FrGenE)
    create_monthly_combined_chart(
        criteria=NachesWest,       
        criteria_pgw=NachesWestPgw,       
        wind=SkateCreek(WindDirMin=215, WindDirMax=320),
        wind_pgw=SkateCreekPgw(WindDirMin=215, WindDirMax=320),
        froude=FrGenE)
    logging.getLogger(__name__).info('All done with "create_monthly_combined"!!')
    
logging.getLogger(__name__).info('ALL DONE!!')

