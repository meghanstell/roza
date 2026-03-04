import numpy as np
import xarray as xr
import cartopy.crs as ccrs
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
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
import json
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
import platform
import pandas as pd
from rich.logging import RichHandler
from rich.traceback import install
from rich.console import Console
import enum
import collections


install(show_locals=True, suppress=['click', 'rich',  'rich_click'])

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
# applied_masks = '/glade/derecho/scratch/meghan/Roza/masks'
applied_masks= '/glade/derecho/scratch/meghan/Roza/roza/applied_masks'
fr_root = '/glade/derecho/scratch/meghan/Roza/froude/masked'

create_froudes=False
# PGW=True
# PGW=False
PGW=bool(int(os.environ.get('PGW','0')))

# if re.match(r'^.*(stewmanji).*$', platform.node(), flags=re.I):
#     area_avg_root = '/media/Work/SandBox/luker/ncar/data/netCDF_masks'
#     crit_root = area_avg_root
#     create_froudes=False
# elif re.match(r'^.*(casper|derecho).*$', platform.node(), flags=re.I):
area_avg_root = '/glade/campaign/ral/hap/meghan/Roza/data/PGW' if PGW else '/glade/campaign/ral/hap/meghan/Roza/data/CONUS404'
crit_root = area_avg_root

if PGW:
    applied_masks='/glade/derecho/scratch/meghan/Roza/masks/PGW'

matplotlib.rcParams['mathtext.fontset'] = 'stix'
matplotlib.rcParams['font.family'] = 'STIXGeneral'

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
        # self._phi=value
        # _str=os.path.splitext(os.path.basename(self.filepath))[0]
        # if re.match(r'^.*?(gen_A).*$', _str, flags=re.I):
        #     self._phi=value
        # if re.match(r'^.*?(gen_E).*$', _str, flags=re.I):
        #     self._phi=value
        # else:
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
        # else:
        #     self._phi_index=value
        #     self.FR=self.Fr[:,value]

    @property
    def fr_var(self):
        if self._fr_var is None:
            # if re.match(r'^.*?(gen_A).*$', os.path.basename(self.filepath), flags=re.I):
            #     self.fr_var = 'FrA'
            # if re.match(r'^.*?(gen_E).*$', os.path.basename(self.filepath), flags=re.I):
            #     self.fr_var = 'FrE'
            # else:
                self.fr_var = 'FR'
            # _str=os.path.splitext(os.path.basename(self.filepath))[0]
            # if re.match(r'^.*?(beaverheadsouth|bhs|g3|a4|g2|a5).*$', _str, flags=re.I):
            #     self.fr_var = 'FrBH'
            # elif re.match(r'^.*?(beaverheadnorth|bhn|c1|c3).*$', _str, flags=re.I):
            #     self.fr_var = 'FrBH'
            # elif re.match(r'^.*?(beaverhead|bhn|c1|c3).*$', _str, flags=re.I):
            #     self.fr_var = 'FrBH'
            # elif re.match(r'^.*?(anacondawest|e1).*$', _str, flags=re.I):
            #     self.fr_var = 'FrAWW'
            # elif re.match(r'^.*?(anacondaeast|f2|f4).*$', _str, flags=re.I):
            #     self.fr_var = 'FrAEW'
            #     # self.fr_var = 'FrAE'
            # elif re.match(r'^.*?(pioneerwest|i7).*$', _str, flags=re.I):
            #     self.fr_var = 'FrPWW'
            # elif re.match(r'^.*?(pioneereast|j3|i2).*$', _str, flags=re.I):
            #     self.fr_var = 'FrPE'
            # elif re.match(r'^.*?(tobaccoroot|j6).*$', _str, flags=re.I):
            #     self.fr_var = 'FrTR'
            # else:
            #     self.fr_var = None
        return self._fr_var
    @fr_var.setter
    def fr_var(self, value):
        self._fr_var = value

def merge_dfs(*dfs):
    _dd = {}
    for df in dfs:
        _df=df.copy()
        for items in _df.to_dict(orient='records'):
            _dd.setdefault(items.get('time'), {}).update(items)
    __df = pd.DataFrame.from_records(list(_dd.values()))
    __df.set_index('time', drop=True, inplace=True)
    __df['time'] = pd.to_datetime(__df.index, origin=datetime.datetime(1979,10,1), unit='m')
    __df.set_index('time', drop=True, inplace=True)
    return __df

model='CONUS404 - PGW' if PGW else 'CONUS404 Current Climate'

def create_freq_chart(precip=None, criteria=None, wind=None, froude=None, verbose=None):
    logging.getLogger(__name__).info(f'Creating Frequency Chart for criteria: "{criteria.basename}", wind: "{wind.basename}" ({wind.wind_label}), froude: "{froude.name}"')
    # precip_df = pd.DataFrame({'time':precip.Time, 'precip':precip.Precip})
    # logging.getLogger(__name__).info(f'{criteria.Time=}')
    # logging.getLogger(__name__).info(f'{criteria.Ground_Temp=}')
    # logging.getLogger(__name__).info(f'{criteria.Ground_LWC=}')
    criteria_df = pd.DataFrame({'time':criteria.Time, 'gtemp':criteria.Ground_Temp, 'glwc':criteria.Ground_LWC})
    wind_df = pd.DataFrame({'time':wind.Time, 'wind':wind.WindDir})
    logging.getLogger(__name__).info(f'{froude.Time=}')
    logging.getLogger(__name__).info(f'{froude.FR=}')
    froude_df = pd.DataFrame({'time':froude.Time, 'Fr':froude.FR})
    # _odf = merge_dfs(criteria_df, precip_df, wind_df, froude_df)
    _odf = merge_dfs(criteria_df, wind_df, froude_df)
    # _odf = merge_dfs(criteria_df, wind_df)
    _months=['','Jan','Feb','Mar', 'Apr','May','Jun','Jul','Aug','Sept','Oct','Nov','Dec']

    def calc_lwc_criteria_match_for_month(month=11, location='lemhi'):
        _month_df = _odf[_odf.index.month == month]
        if verbose:
            output_name = f'PGW_monthly_ground_{criteria.basename}_{wind.basename}_{wind.wind_label}_{froude.basename}_{froude.phi}_noPrecip_month_df.json' if PGW else f'monthly_ground_{criteria.basename}_{wind.basename}_{wind.wind_label}_{froude.basename}_{froude.phi}_noPrecip_month_df.json'
            json.dump(json.loads(_month_df.to_json(orient='records')), open(output_name, 'w'),  indent=4)
        _crit_df = _month_df[_month_df['gtemp'] < -6]
        _crit_df = _crit_df[_crit_df['gtemp'] > -18]
        _crit_df = _crit_df[_crit_df['glwc'] > 0.01]
        if verbose:
            output_name = f'PGW_monthly_ground_{criteria.basename}_{wind.basename}_{wind.wind_label}_{froude.basename}_{froude.phi}_noPrecip_crit_df.json' if PGW else f'monthly_ground_{criteria.basename}_{wind.basename}_{wind.wind_label}_{froude.basename}_{froude.phi}_noPrecip_crit_df.json'
            json.dump(json.loads(_crit_df.to_json(orient='records')), open(output_name, 'w'),  indent=4)
        _surface_df = _crit_df[_crit_df['wind']>wind.WindDirMin]
        _surface_df = _surface_df[_surface_df['wind'] <wind.WindDirMax]
        if verbose:
            output_name = f'PGW_monthly_ground_{criteria.basename}_{wind.basename}_{wind.wind_label}_{froude.basename}_{froude.phi}_noPrecip_surface_df.json' if PGW else f'monthly_ground_{criteria.basename}_{wind.basename}_{wind.wind_label}_{froude.basename}_{froude.phi}_noPrecip_surface_df.json'
            json.dump(json.loads(_surface_df.to_json(orient='records')), open(output_name, 'w'),  indent=4)
        _froude_df = _surface_df[_surface_df['Fr'] > 0.4999]
        if verbose:
            output_name = f'PGW_monthly_ground_{criteria.basename}_{wind.basename}_{wind.wind_label}_{froude.basename}_{froude.phi}_noPrecip_froude_df.json' if PGW else f'monthly_ground_{criteria.basename}_{wind.basename}_{wind.wind_label}_{froude.basename}_{froude.phi}_noPrecip_froude_df.json'
            json.dump(json.loads(_froude_df.to_json(orient='records')), open(output_name, 'w'),  indent=4)
        # _precip_df = _froude_df[_froude_df['precip'] > 0.001]
        return {
            'month':_months[month], 
            '(LWC > 0.01 g/kg) & (-18\xb0C < Temp < -6\xb0C)':(len(_crit_df)/len(_month_df))*100, 
            'LWC+Temp+Wind Dir ({}\xb0 - {}\xb0)'.format(wind.WindDirMin, wind.WindDirMax):(len(_surface_df)/len(_month_df))*100,
            'LWC+Temp+Wind Dir+Froude > 0.5':(len(_froude_df)/len(_month_df))*100, 
            # 'LWC+Temp+Wind Dir+Froude+Precip > 0 (mm)':(len(_precip_df)/len(_month_df))*100, 
            }

    data_dict = [calc_lwc_criteria_match_for_month(month=_month) for _month in [11,12,1,2,3,4]]
    df = pd.DataFrame.from_records(data_dict)
    df.set_index('month', inplace=True, drop=True)
    ax=df.plot(kind='bar',rot=0,color=['ocean blue','tiffany blue','burnt orange','apricot'])
    # plt.rcParams.update({"text.usetex": False})
    # plt.title(f'Ground Monthly Seeding Frequency \n CONUS 404 Current Climate \n Region: {criteria.name} | Precip: {precip.name}', fontsize = 18)
    
    plt.title(f'Ground Monthly Seeding Frequency \n {model} \n Region: {criteria.name} | Wind: {wind.name} | Froude: {froude.name}', fontsize = 26, fontweight='bold')
    # plt.title(f'Ground Monthly Seeding Frequency \n {model} \n Region: {criteria.name} | Wind: {wind.name} | Froude: {froude.name}', fontsize = 26, fontweight='bold')
    fig = ax.get_figure()
    # fig.set_size_inches(8,8)
    plt.yticks(fontsize=22)
    plt.xticks(fontsize=22)
    fig.set_size_inches(18.5, 10.5)
    # plt.legend(loc="upper right")
    plt.legend(loc="upper right", fontsize=22)
    ax.yaxis.grid(True, which='major')
    # ax.set_ylim(0,math.ceil( max([df[_col].max() for _col in df.columns if _col not in ['month']]) /5.0) * 5)
    ax.set_ylim(0,30)
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.set_xlabel('Month',fontsize =24)
    # ax.set_ylabel('Frequency (%)', fontsize =22)
    ax.set_ylabel(r'$Frequency\ \left(\%\right)$', fontsize =24)
    fig.patch.set_facecolor('white')
    # output_name = f'{precip.basename}_{criteria.basename}_{froude.basename}.png'
    # output_name = f'monthly_ground_{criteria.basename}_{precip.basename}_{froude.basename}_noPrecip.png'
    output_name = f'PGW_monthly_ground_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}_noPrecip.png' if PGW else f'monthly_ground_{criteria.basename}_{wind.basename}_{wind.wind_label}_{froude.basename}_{froude.phi}_noPrecip.png'
    output_path = os.path.abspath(output_name)
    plt.savefig(output_path, dpi=300)
    logging.getLogger(__name__).info('Chart saved to "{}"'.format(output_path))
    plt.close()


def create_monthly_airborne_freq_chart(precip=None, criteria=None, wind=None, froude=None):
    logging.getLogger(__name__).info(f'Creating Monthly Airborne Frequency Chart for criteria: "{criteria.basename}"')
    criteria_df = pd.DataFrame({'time':criteria.Time, 'temp':criteria.Air_Temp, 'lwc':criteria.Air_LWC})
    _odf = merge_dfs(criteria_df)
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

    data_dict = [calc_lwc_criteria_match_for_month(month=_month) for _month in [11,12,1,2,3,4]]
    df = pd.DataFrame.from_records(data_dict)
    df.set_index('month', inplace=True, drop=True)
    ax=df.plot(kind='bar',rot=0,color=['ocean blue','tiffany blue','burnt orange','apricot'])
    # plt.rcParams.update({"text.usetex": False})
    # plt.title(f'Ground Monthly Seeding Frequency \n CONUS 404 Current Climate \n Region: {criteria.name} | Precip: {precip.name}', fontsize = 18)
    plt.title(f'Airborne Monthly Seeding Frequency \n {model} \n Region: {criteria.name}', fontsize = 26, fontweight='bold')
    fig = ax.get_figure()
    # fig.set_size_inches(8,8)
    plt.yticks(fontsize=22)
    plt.xticks(fontsize=22)
    fig.set_size_inches(18.5, 10.5)
    # plt.legend(loc="upper right")
    plt.legend(loc="upper right", fontsize=22)
    ax.yaxis.grid(True, which='major')
    # ax.set_ylim(0,math.ceil( max([df[_col].max() for _col in df.columns if _col not in ['month']]) /5.0) * 5)
    ax.set_ylim(0,40)
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.set_xlabel('Month',fontsize =24)
    # ax.set_ylabel('Frequency (%)', fontsize =22)
    ax.set_ylabel(r'$Frequency\ \left(\%\right)$', fontsize =24)
    fig.patch.set_facecolor('white')
    # output_name = f'{precip.basename}_{criteria.basename}_{froude.basename}.png'
    # output_name = f'monthly_airborne_{criteria.basename}_{precip.basename}_{froude.basename}_noPrecip.png'
    output_name = f'PGW_monthly_airborne_{criteria.basename}_noPrecip.png' if PGW else f'monthly_airborne_{criteria.basename}_noPrecip.png'
    output_path = os.path.abspath(output_name)
    plt.savefig(output_path, dpi=300)
    logging.getLogger(__name__).info('Chart saved to "{}"'.format(output_path))
    plt.close()

def create_yearly_chart(precip=None, criteria=None, wind=None, froude=None, lwc_type=LwcType.GROUND):
    if lwc_type == LwcType.GROUND:
        logging.getLogger(__name__).info(f'Creating {lwc_type.name} Yearly Seeding Frequency \n {model} \n Region: {criteria.name} | Wind: {wind.name} ({wind.wind_label}) | Froude: {froude.name}, Phi: {froude.phi}')
    else:
        logging.getLogger(__name__).info(f'Creating {lwc_type.name} Yearly Seeding Frequency \n {model} \n Region: {criteria.name} | Wind: {wind.name} ({wind.wind_label})')

    # logging.getLogger(__name__).info('Creating precip_df')
    # precip_df = pd.DataFrame({'time':precip.Time, 'precip':precip.Precip})
    if lwc_type == LwcType.GROUND:
        logging.getLogger(__name__).debug('Creating GROUND criteria_df')
        criteria_df = pd.DataFrame({'time':criteria.Time, 'temp':criteria.Ground_Temp, 'lwc':criteria.Ground_LWC})
        wind_df = pd.DataFrame({'time':wind.Time, 'wind':wind.WindDir})
        froude_df = pd.DataFrame({'time':froude.Time, 'Fr':froude.FR})
        _odf = merge_dfs(criteria_df, wind_df, froude_df)
        # _odf = merge_dfs(criteria_df, wind_df)
    else:
        logging.getLogger(__name__).debug('Creating AIR criteria_df')
        criteria_df = pd.DataFrame({'time':criteria.Time, 'temp':criteria.Air_Temp, 'lwc':criteria.Air_LWC})
        _odf = merge_dfs(criteria_df)

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
            _surface_df=_crit_df.copy()
            _surface_df = _surface_df[_surface_df['wind']>wind.WindDirMin]
            _surface_df = _surface_df[_surface_df['wind'] <wind.WindDirMax]
            _froude_df = _surface_df.copy()
            _froude_df = _froude_df[_froude_df['Fr'] > 0.4999]
            return {
                'year':year, 
                'LWC > 0.01 g/kg & -18\xb0C < Temp < -6\xb0C':(len(_crit_df)/len(_year_df))*100, 
                'LWC+Temp+Wind Dir {}\xb0 - {}\xb0'.format(wind.WindDirMin, wind.WindDirMax):(len(_surface_df)/len(_year_df))*100,
                'LWC+Temp+Wind Dir+Froude > 0.5':(len(_froude_df)/len(_year_df))*100, 
                }

        return {
            'year':str(year), 
            'LWC > 0.01 g/kg & -18\xb0C < Temp < -6\xb0C':(len(_crit_df)/len(_year_df))*100, 
            # 'LWC+Temp+Precip > 0 mm':(len(_precip_df)/len(_year_df))*100,  
            }
            

    def get_avg(data):
        keys=list(data[0].keys())
        def _avg(_key):
            return sum(list(map(lambda x: x.get(_key), data)))/len(data)
        def _max(_key):
            return max(list(map(lambda x: x.get(_key), data)))
        _dd={_key:_avg(_key) for _key in keys}
        # max_year = _max('year')
        # _dd.update({'year':max_year+1})
        _dd.update({'year':'40 Yr Avg'})
        return _dd
        # return data + [_dd]



    data_dict = [calc_lwc_criteria_match_for_year(year=_year) for _year in range(1980, 2022)]
    _avg=get_avg(data_dict)

    # data_dict = [calc_lwc_criteria_match_for_year(year=_year) for _year in range(1980, 2022)]

    logging.getLogger(__name__).debug('Creating Plot DF')
    df = pd.DataFrame.from_records(data_dict)
    df.set_index('year', inplace=True, drop=True)
    logging.getLogger(__name__).debug(f'df:\n{df}')
    logging.getLogger(__name__).debug('Plotting')

    _colors=['ocean blue','firebrick','apricot']
    ax=df.plot(kind='line',rot=45,color=_colors)

    jj=0
    for kk, vv in _avg.items():
        if kk in ['year']: continue
        # ax.axhline(vv, ls='-.', label=f'40 Yr Avg({kk})', color=_colors[jj], xmin=1980, xmax=2021, transform=ax.transData)
        ax.axhline(vv, ls='-.', label=f'40 Yr Avg({kk})', color=_colors[jj])
        jj+=1

    # plt.rcParams.update({
    #     "text.usetex": False,
    # })

    if lwc_type == LwcType.GROUND:
        plt.title(f'Ground Yearly Seeding Frequency \n {model} \n Region: {criteria.name} | Wind: {wind.name} | Froude: {froude.name}', fontsize = 26, fontweight='bold')
    else:
        plt.title(f'Airborne Yearly Seeding Frequency \n {model} \n Region: {criteria.name}', fontsize = 26, fontweight='bold')
    fig = ax.get_figure()
    # fig.set_size_inches(8,8)
    plt.yticks(fontsize=22)
    plt.xticks(fontsize=22)
    fig.set_size_inches(18.5, 10.5)
    # plt.legend(loc="upper right")

    plt.legend(loc="upper right", fontsize=18, ncol=2)
    ax.yaxis.grid(True, which='major')
    # if lwc_type == LwcType.GROUND:
    ax.set_ylim(0,30) 
    ax.set_xlim(1980,2021) 
    # else:
        # ax.set_ylim(0,20) 
    
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    
    # labels=[
    #     '','','',
    #     '1980', '', '1982', '', '1984', '', '1986', '', '1988', '', 
    #     '1990', '', '1992', '', '1994', '', '1996', '', '1998', '', 
    #     '2000', '', '2002', '', '2004', '', '2006', '', '2008', '', 
    #     '2010', '', '2012', '', '2014', '', '2016', '', '2018', '', 
    #     '2020', '', '40 Yr Avg','','','']

    # ax.yaxis.set_major_locator(MultipleLocator(5))
    # ax.yaxis.set_minor_locator(AutoMinorLocator())
    # ax.xaxis.set_major_locator(MultipleLocator(1))
    # ax.xaxis.set_major_locator(ticker.FixedLocator(np.array(range(-3,46))))
    # ax.xaxis.set_major_formatter(ticker.FixedFormatter(np.array(labels)))
    
    # ax.xaxis.set_minor_locator(AutoMinorLocator())
    fig.canvas.draw()
    labels = [item.get_text() for item in ax.get_xticklabels()]
    pos = ax.get_xticks()
    logging.getLogger(__name__).debug(f'{pos=}')
    logging.getLogger(__name__).debug(f'{labels=}')

    ax.set_xlabel('Year',fontsize =24)
    # ax.set_xlabel("ha=right")
    # ax.set_ylabel('Frequency (%)', fontsize =22)
    ax.set_ylabel(r'$Frequency\ \left(\%\right)$', fontsize =24)
    fig.patch.set_facecolor('white')
    if lwc_type == LwcType.GROUND:
        output_name = f'PGW_yearly_ground_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}.png' if PGW else f'yearly_ground_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}.png'
    else:
        output_name = f'PGW_yearly_airborne_{criteria.basename}_{wind.basename}.png' if PGW else f'yearly_airborne_{criteria.basename}_{wind.basename}.png'
    output_path = os.path.abspath(output_name)
    plt.savefig(output_path, dpi=300)
    logging.getLogger(__name__).info('Chart saved to "{}"'.format(output_path))
    plt.close()

def create_yearly_airborne_chart_combined(*criteria):
    lwc_type=LwcType.AIR

    def _handle_region(criteria):
        logging.getLogger(__name__).info(f'Creating {lwc_type.name} Yearly Seeding Frequency \n {model} \n Region: {criteria.name}')
        criteria_df = pd.DataFrame({'time':criteria.Time, 'temp':criteria.Air_Temp, 'lwc':criteria.Air_LWC})
        _odf = merge_dfs(criteria_df)

        def calc_lwc_criteria_match_for_year(year=2000):
            logging.getLogger(__name__).debug('calc_lwc_criteria_match_for_year: {}'.format(year))
            _pyear_df = _odf[(_odf.index.year == year-1) & (_odf.index.month>9)]
            _tyear_df = _odf[(_odf.index.year == year) & (_odf.index.month<5)]
            _year_df = pd.concat([_pyear_df, _tyear_df])
            _crit_df = _year_df[_year_df['temp'] < -6]
            _crit_df = _crit_df[_crit_df['temp'] > -18]
            _crit_df = _crit_df[_crit_df['lwc'] > 0.01]
            return {
                'year':year, 
                # 'LWC > 0.01 g/kg & -18\xb0C < Temp < -6\xb0C':(len(_crit_df)/len(_year_df))*100, 
                criteria.name:(len(_crit_df)/len(_year_df))*100, 
                # 'LWC+Temp+Precip > 0 mm':(len(_precip_df)/len(_year_df))*100,  
                }
        
        data_dict = [calc_lwc_criteria_match_for_year(year=_year) for _year in range(1980, 2022)]
        def get_avg(data):
            keys=list(data[0].keys())
            def _avg(_key):
                return sum(list(map(lambda x: x.get(_key), data)))/len(data)
            def _max(_key):
                return max(list(map(lambda x: x.get(_key), data)))
            _dd={_key:_avg(_key) for _key in keys}
            max_year = _max('year')
            # _dd.update({'year':max_year+1})
            _dd.update({'year':'40 Yr Avg'})
            return _dd
            # return data + [_dd]



        # data_dict = get_avg([calc_lwc_criteria_match_for_year(year=_year) for _year in range(1980, 2022)])
        data_dict = [calc_lwc_criteria_match_for_year(year=_year) for _year in range(1980, 2022)]
        _avg=get_avg(data_dict)

        logging.getLogger(__name__).debug('Creating Plot DF')
        df = pd.DataFrame.from_records(data_dict)
        df.set_index('year', inplace=True, drop=True)
        return df, _avg

    _colors = ['firebrick','orange','gold','turquoise','dodgerblue','dark violet','hotpink']
    _dfs=collections.OrderedDict((_region.name,_handle_region(_region)) for _region in criteria)
    logging.getLogger(__name__).debug('Plotting')
    fig, ax = plt.subplots(1, 1)
    # [df.plot(kind='line',ax=ax, rot=45, colormap=_colors[ii]) for ii,(_,df) in enumerate(_dfs.items())]
    # [ax.plot(df.index.to_list(), df[region].to_list(), color=_colors[ii], label=region) for ii,(region,(df, _avg)) in enumerate(_dfs.items())]
    
    for ii,(region,(df, _avg)) in enumerate(_dfs.items()):
        ax.plot(df.index.to_list(), df[region].to_list(), color=_colors[ii], label=region)

    jj=0
    for region,(df, _avg) in _dfs.items():
        for kk,vv in _avg.items():
            if kk in ['year']: continue
            # ax.axhline(vv, label=f'40 Yr Avg({kk})', ls='-.', color=_colors[jj], xmin=1980, xmax=2021, transform=ax.transData)
            ax.axhline(vv, label=f'40 Yr Avg({kk})', ls='-.', color=_colors[jj])
            jj+=1
     
    plt.xticks(rotation=45)
    # plt.rcParams.update({
    #     "text.usetex": False,
    # })

    plt.title(f'Airborne Yearly Seeding Frequency \n {model} \n Criteria: LWC > 0.01, -18 < TEMP < -6', fontsize = 26, fontweight='bold')
    fig = ax.get_figure()
    # fig.set_size_inches(8,8)
    plt.yticks(fontsize=22)
    plt.xticks(fontsize=22)
    fig.set_size_inches(18.5, 10.5)
    # plt.legend(loc="upper right")
    plt.legend(loc="upper right", fontsize=22, ncol=2)
    ax.yaxis.grid(True, which='major')
    ax.set_ylim(0,50) 
    ax.set_xlim(1980, 2021)
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.set_xlabel('Year',fontsize =24)
    # ax.set_xlabel("ha=right")
    # ax.set_ylabel('Frequency (%)', fontsize =22)
    ax.set_ylabel(r'$Frequency\ \left(\%\right)$', fontsize =24)
    fig.patch.set_facecolor('white')
    output_name = f'PGW_yearly_airborne_combined.png' if PGW else f'yearly_airborne_combined.png'
    output_path = os.path.abspath(output_name)
    plt.savefig(output_path, dpi=300)
    logging.getLogger(__name__).info('Chart saved to "{}"'.format(output_path))
    plt.close()

def create_yearly_combined_chart(precip=None, criteria=None, wind=None, froude=None):
    #Yearly: Beaverhead South with Lemhi Ridge Precip
    logging.getLogger(__name__).info(f'Creating Combined Yearly Seeding Frequency \n {model} \n Region: {criteria.name} | Surface: {wind.name} ({wind.wind_label}) | Froude: {froude.name}, Phi: {froude.phi}')

    # logging.getLogger(__name__).info('Creating precip_df')
    # precip_df = pd.DataFrame({'time':precip.Time, 'precip':precip.Precip})
    logging.getLogger(__name__).debug('Creating criteria_df')
    combined_criteria_df = pd.DataFrame({'time':criteria.Time, 'gtemp':criteria.Ground_Temp, 'atemp':criteria.Air_Temp,'glwc':criteria.Ground_LWC, 'alwc':criteria.Air_LWC})
    gnd_criteria_df = pd.DataFrame({'time':criteria.Time, 'gtemp':criteria.Ground_Temp, 'glwc':criteria.Ground_LWC})
    air_criteria_df = pd.DataFrame({'time':criteria.Time, 'atemp':criteria.Air_Temp,'alwc':criteria.Air_LWC})
    wind_df = pd.DataFrame({'time':wind.Time, 'wind':wind.WindDir})
    froude_df = pd.DataFrame({'time':froude.Time, 'Fr':froude.FR})

    # precip_df.set_index('time', drop=True, inplace=True)
    # criteria_df.set_index('time', drop=True, inplace=True)

    # _odf = criteria_df.join(precip_df, how='inner')
    logging.getLogger(__name__).debug('Merging DFs')
    # _odf = merge_dfs(criteria_df, precip_df)
    # _odf = merge_dfs(criteria_df, precip_df, wind_df, froude_df)
    # _cmb_odf = merge_dfs(combined_criteria_df, wind_df, froude_df).copy()
    # _gnd_odf = merge_dfs(gnd_criteria_df, wind_df, froude_df).copy()
    # _air_odf = merge_dfs(air_criteria_df, wind_df, froude_df).copy()
    _cmb_odf = merge_dfs(combined_criteria_df, wind_df, froude_df).copy()
    _or_odf = merge_dfs(combined_criteria_df, wind_df, froude_df).copy()
    _gnd_odf = merge_dfs(gnd_criteria_df, wind_df, froude_df).copy()
    _air_odf = merge_dfs(air_criteria_df, wind_df, froude_df).copy()
    # _odf = pd.concat([criteria_df, precip_df])
    # logging.getLogger(__name__).info('Converting Time')
    # _odf['time'] = pd.to_datetime(_odf.index, origin=datetime.datetime(1979,10,1), unit='m') #converts minutes to datetimeh')
    # logging.getLogger(__name__).info('Setting Time Index')
    # _odf.set_index('time', drop=True, inplace=True)

    def calc_lwc_criteria_match_for_year(year=2000):
        logging.getLogger(__name__).debug('calc_lwc_criteria_match_for_year: {}'.format(year))
        _c_pyear_df = _cmb_odf[(_cmb_odf.index.year == year-1) & (_cmb_odf.index.month>9)]
        _c_tyear_df = _cmb_odf[(_cmb_odf.index.year == year) & (_cmb_odf.index.month<5)]
        _c_year_df = pd.concat([_c_pyear_df, _c_tyear_df])

        _o_pyear_df = _cmb_odf[(_or_odf.index.year == year-1) & (_or_odf.index.month>9)]
        _o_tyear_df = _cmb_odf[(_or_odf.index.year == year) & (_or_odf.index.month<5)]
        _o_year_df = pd.concat([_o_pyear_df, _o_tyear_df])

        _g_pyear_df = _gnd_odf[(_gnd_odf.index.year == year-1) & (_gnd_odf.index.month>9)]
        _g_tyear_df = _gnd_odf[(_gnd_odf.index.year == year) & (_gnd_odf.index.month<5)]
        _g_year_df = pd.concat([_g_pyear_df, _g_tyear_df])

        _a_pyear_df = _air_odf[(_air_odf.index.year == year-1) & (_air_odf.index.month>9)]
        _a_tyear_df = _air_odf[(_air_odf.index.year == year) & (_air_odf.index.month<5)]
        _a_year_df = pd.concat([_a_pyear_df, _a_tyear_df])

        _ccrit_df = _c_year_df[_c_year_df['atemp'] < -6]
        _ccrit_df = _ccrit_df[_ccrit_df['atemp'] > -18]
        _ccrit_df = _ccrit_df[_ccrit_df['alwc'] > 0.01]
        _ccrit_df = _ccrit_df[_ccrit_df['gtemp'] < -6]
        _ccrit_df = _ccrit_df[_ccrit_df['gtemp'] > -18]
        _ccrit_df = _ccrit_df[_ccrit_df['glwc'] > 0.01]
        _ccrit_df = _ccrit_df[_ccrit_df['wind']>wind.WindDirMin]
        _ccrit_df = _ccrit_df[_ccrit_df['wind'] <wind.WindDirMax]
        _ccrit_df = _ccrit_df[_ccrit_df['Fr'] > 0.4999]


        # _o_year_df['gnd_mask'] = int(bool((_o_year_df['gtemp'] < -6) & (_o_year_df['gtemp'] > -18) & (_o_year_df['glwc'] > 0.01) & (_o_year_df['wind']>wind.WindDirMin) & (_o_year_df['wind'] <wind.WindDirMax) & (_o_year_df['Fr'] > 0.4999)))
        _o_year_df['gnd_mask'] = True
        _o_year_df['gnd_mask'] = _o_year_df['gnd_mask'].where((_o_year_df['gnd_mask']==True) & (_o_year_df['gtemp'] < -6), False )
        _o_year_df['gnd_mask'] = _o_year_df['gnd_mask'].where((_o_year_df['gnd_mask']==True) & (_o_year_df['gtemp'] > -18), False )
        _o_year_df['gnd_mask'] = _o_year_df['gnd_mask'].where((_o_year_df['gnd_mask']==True) & (_o_year_df['glwc'] > 0.01), False )
        _o_year_df['gnd_mask'] = _o_year_df['gnd_mask'].where((_o_year_df['gnd_mask']==True) & (_o_year_df['wind']>wind.WindDirMin), False )
        _o_year_df['gnd_mask'] = _o_year_df['gnd_mask'].where((_o_year_df['gnd_mask']==True) & (_o_year_df['wind'] <wind.WindDirMax), False )
        _o_year_df['gnd_mask'] = _o_year_df['gnd_mask'].where((_o_year_df['gnd_mask']==True) & (_o_year_df['Fr'] > 0.4999), False )

        _o_year_df['air_mask'] = True
        _o_year_df['air_mask'] = _o_year_df['air_mask'].where((_o_year_df['air_mask']==True) & (_o_year_df['atemp']<-6), False)
        _o_year_df['air_mask'] = _o_year_df['air_mask'].where((_o_year_df['air_mask']==True) & (_o_year_df['atemp']>-18), False) 
        _o_year_df['air_mask'] = _o_year_df['air_mask'].where((_o_year_df['air_mask']==True) & (_o_year_df['alwc'] > 0.01), False)
        # _o_year_df['air_mask'] = _o_year_df[(_o_year_df['atemp'] < -6) & (_o_year_df['atemp'] > -18) & (_o_year_df['alwc'] > 0.01)]
        _o_year_df['or_mask']  = True
        _o_year_df['or_mask']  = _o_year_df['or_mask'].where((_o_year_df['air_mask']==True) | (_o_year_df['gnd_mask']==True), False)
        # _o_year_df['or_mask']  = _o_year_df[(_o_year_df['gnd_mask'])   | (_o_year_df['air_mask'])]        
        # _ocrit_df = _o_year_df.copy()
        _ocrit_df = _o_year_df[_o_year_df['or_mask']==True]


        _gcrit_df = _g_year_df[_g_year_df['gtemp'] < -6]
        _gcrit_df = _gcrit_df[_gcrit_df['gtemp'] > -18]
        _gcrit_df = _gcrit_df[_gcrit_df['glwc'] > 0.01]
        _gcrit_df = _gcrit_df[_gcrit_df['wind']>wind.WindDirMin]
        _gcrit_df = _gcrit_df[_gcrit_df['wind'] <wind.WindDirMax]
        _gcrit_df = _gcrit_df[_gcrit_df['Fr'] > 0.4999]

        _acrit_df = _a_year_df[_a_year_df['atemp'] < -6]
        _acrit_df = _acrit_df[_acrit_df['atemp'] > -18]
        _acrit_df = _acrit_df[_acrit_df['alwc'] > 0.01]


        # _precip_df = _ccrit_df[_ccrit_df['precip'] > 0.001]
        return {
            'year':year, 
            'Air':(len(_acrit_df)/len(_a_year_df))*100, 
            'Ground':(len(_gcrit_df)/len(_g_year_df))*100, 
            'Air & Ground':(len(_ccrit_df)/len(_c_year_df))*100, 
            'Air | Ground':(len(_ocrit_df)/len(_o_year_df))*100, 
            # 'Air + Ground + Precip':(len(_precip_df)/len(_year_df))*100,  
            }

    def get_avg(data):
        keys=list(data[0].keys())
        def _avg(_key):
            return sum(list(map(lambda x: x.get(_key), data)))/len(data)
        def _max(_key):
            return max(list(map(lambda x: x.get(_key), data)))
        _dd={_key:_avg(_key) for _key in keys}
        max_year = _max('year')
        # _dd.update({'year':max_year+1})
        _dd.update({'year':'40 Yr Avg'})
        # _dd.update({'year':'Avg'})
        # logging.getLogger(__name__).info(_dd)
        return _dd
    # data_dict = [calc_lwc_criteria_match_for_year(year=_year) for _year in range(1980, 2022)]
    data_dict = [calc_lwc_criteria_match_for_year(year=_year) for _year in range(1980, 2022)]
    _avg=get_avg(data_dict)

    logging.getLogger(__name__).debug('Creating Plot DF')
    df = pd.DataFrame.from_records(data_dict)
    df.set_index('year', inplace=True, drop=True)

    logging.getLogger(__name__).debug(f'df:\n{df}')

    logging.getLogger(__name__).debug('Plotting')
    # ax=df.plot(kind='bar',rot=45,color=['ocean blue','tiffany blue','burnt orange','apricot'])
    _colors=['ocean blue','tiffany blue','burnt orange','apricot']
    ax=df.plot(rot=45,color=_colors)

    jj=0
    for kk, vv in _avg.items():
        if kk in ['year']: continue
        # ax.axhline(vv, ls='-.', color=_colors[jj], label=f'40 Yr Avg({kk})', xmin=1980, xmax=2021, transform=ax.transData)
        ax.axhline(vv, ls='-.', color=_colors[jj], label=f'40 Yr Avg({kk})')
        jj+=1


    # plt.rcParams.update({
    #     "text.usetex": False,
    # })

    plt.title(f'Yearly Simultaneous Seeding Frequency \n {model} \n Region: {criteria.name} | Wind: {wind.name} | Froude: {froude.name}', fontsize = 26, fontweight='bold')
    fig = ax.get_figure()
    # fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(18.5, 10.5)
    # fig.set_size_inches(8,8)
    plt.yticks(fontsize=22)
    plt.xticks(fontsize=22)
    plt.legend(loc="upper right", fontsize=22, ncol=2)
    # ax.yaxis.grid(True, which='major')
    ax.set_ylim(0,50)
    ax.set_xlim(1980,2021)
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.xaxis.set_minor_locator(AutoMinorLocator())

    # pos_list=list(range(1978, 2026, 2))
    # labels=['', '1980', '1982', '1984', '1986', '1988', '1990', '1992', '1994', '1996', '1998', '2000', '2002', '2004', '2006', '2008', '2010', '2012', '2014', '2016', '2018', '2020', '40 Year Avg', '']
    
    # ax.xaxis.set_major_locator(ticker.FixedLocator(pos_list))
    # ax.xaxis.set_major_formatter(ticker.FixedFormatter(labels))
    
    ax.set_xlabel('Year',fontsize =24)
    # ax.set_xlabel("ha=right")
    # ax.set_ylabel('Frequency (%)', fontsize =22)
    ax.set_ylabel(r'$Frequency\ \left(\%\right)$', fontsize =24)

    # logging.getLogger(__name__).info(f'{labels=}')
    # ax.set_xticklabels(labels)
    fig.patch.set_facecolor('white')
    # plt.savefig('bhs_lrp_ground_year.png', dpi=300)
    output_name = f'PGW_yearly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}.png' if PGW else f'yearly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}.png'
    output_path = os.path.abspath(output_name)
    plt.savefig(output_path, dpi=300)
    logging.getLogger(__name__).info('Chart saved to "{}"'.format(output_path))
    plt.close()


def create_monthly_combined_chart(precip=None, criteria=None, wind=None, froude=None, verbose=None):
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

    data_dict = [calc_lwc_criteria_match_for_month(month=_month) for _month in [11,12,1,2,3,4]]

    logging.getLogger(__name__).debug('Creating Plot DF')
    df = pd.DataFrame.from_records(data_dict)
    df.set_index('month', inplace=True, drop=True)

    logging.getLogger(__name__).debug('Plotting')
    ax=df.plot(kind='bar',rot=45,color=['ocean blue','tiffany blue','burnt orange','apricot'])


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
    ax.set_ylim(0,35)
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.set_xlabel('Year',fontsize =24)
    # ax.set_ylabel('Frequency (%)', fontsize =22)
    ax.set_ylabel(r'$Frequency\ \left(\%\right)$', fontsize =24)
    fig.patch.set_facecolor('white')
    # plt.savefig('bhs_lrp_ground_year.png', dpi=300)
    output_name = f'PGW_monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}.png' if PGW else f'monthly_combined_{criteria.basename}_{wind.basename}_{froude.basename}_{froude.phi}.png'
    output_path = os.path.abspath(output_name)
    plt.savefig(output_path, dpi=300)
    logging.getLogger(__name__).info('Chart saved to "{}"'.format(output_path))
    plt.close()

# | Surface          | SNOTEL         | Winds   | Froude |
# | ---------------- | -------------- | ------- | ------ |
# | Rainier          | BurntMountain  | 225-315 | 
# | NachesRiver      | MeadowsPass    | 210-315 |
# | UpperYakimaSouth | MeadowsPass    | 225-285 |
# | NachesEast       | CayusePass     | 225-315 |
# | NachesEast       | BumpingRidge   | 240-320 |
# | RainierEast      | CorralPass     | 225-320 |
# | UpperYakimaNorth | FishLake       | 225-315 |
# | UpperYakimaSouth | SasseRidge     | 210-315 |
# | NachesWest       | SkateCreek     | 225-320 |
# | NachesWest       | PotatoHill     | 225-320 |
# | NachesRiver      | CougarMountain | 225-320 |
# | NachesWest       | SkateCreek     | 215-320 |

# | Surface          | SNOTEL         | Winds   | Froude |
# | ---------------- | -------------- | ------- | ------ |
# | RainierWest      | BurntMountain  | 225-315 | GenE   |
# | NachesRiver      | MeadowsPass    | 210-315 | GenA   |
# | NachesRiver      | MeadowsPass    | 210-315 | GenE   |
# | UpperYakimaSouth | MeadowsPass    | 225-285 | GenA   |
# | NachesEast       | CayusePass     | 225-315 | GenE   |
# | NachesEast       | BumpingRidge   | 240-320 | GenE   |
# | RainierEast      | CorralPass     | 225-320 | GenE   |
# | UpperYakimaNorth | FishLake       | 225-315 | GenA   |
# | UpperYakimaSouth | SasseRidge     | 210-315 | GenA   |
# | NachesWest       | SkateCreek     | 225-320 | GenE   |
# | NachesWest       | PotatoHill     | 225-320 | GenE   |
# | NachesRiver      | CougarMountain | 225-320 | GenA   |
# | NachesRiver      | CougarMountain | 225-320 | GenE   |
# | NachesWest       | SkateCreek     | 215-320 | GenA   |

# /glade/derecho/scratch/meghan/Roza/masks
RainierEast = Collection(filepath=os.path.join(applied_masks, 'RainierEast.nc'), name='Rainier East') 
RainierWest = Collection(filepath=os.path.join(applied_masks, 'RainierWest.nc'), name='Rainier West') 
NachesRiver = Collection(filepath=os.path.join(applied_masks, 'NachesRiver.nc'), name='Naches River')
UpperYakimaSouth = Collection(filepath=os.path.join(applied_masks, 'UpperYakimaSouth.nc'), name='Upper Yakima South')
NachesEast = Collection(filepath=os.path.join(applied_masks, 'NachesEast.nc'), name='Naches East')
UpperYakimaNorth = Collection(filepath=os.path.join(applied_masks, 'UpperYakimaNorth.nc'), name='Upper Yakima North')
# UpperYakimaSouth = Collection(filepath=os.path.join(applied_masks, 'UpperYakimaSouth.nc'), name='Upper Yakima South')
NachesWest = Collection(filepath=os.path.join(applied_masks, 'NachesWest.nc'), name='Naches West')

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




# create_monthly_airborne=True
create_monthly_airborne=False
if create_monthly_airborne:
    create_monthly_airborne_freq_chart(criteria=RainierWest)
    create_monthly_airborne_freq_chart(criteria=RainierEast)
    create_monthly_airborne_freq_chart(criteria=NachesRiver)
    create_monthly_airborne_freq_chart(criteria=UpperYakimaSouth)
    create_monthly_airborne_freq_chart(criteria=NachesEast)
    create_monthly_airborne_freq_chart(criteria=UpperYakimaNorth)
    create_monthly_airborne_freq_chart(criteria=NachesWest)
    # 7

# create_yearly_air=True
create_yearly_air=False
if create_yearly_air:
    create_yearly_airborne_chart_combined(RainierWest, RainierEast, NachesRiver, UpperYakimaSouth, NachesEast, UpperYakimaNorth, NachesWest)
    # 1

wind_swaths =[
    dict(WindDirMin=180, WindDirMax=210, wind_label='SSW'),
    dict(WindDirMin=210, WindDirMax=270, wind_label='SWW'),
    dict(WindDirMin=270, WindDirMax=310, wind_label='WNW'),
    dict(WindDirMin=310, WindDirMax=360, wind_label='NWN'),
]
# FrGenA - UpperYakimaSouth
# FrGenA - UpperYakimaNorth
# FrGenA - NachesRiver
# FrGenE - NachesRiver
# FrGenE - RainierEast
# FrGenE - RainierWest
# FrGenE - NachesEast
# FrGenE - NachesWest

# | Surface          | Wind           | Winds   | Froude |
# | ---------------- | -------------- | ------- | ------ |
# | RainierWest      | BurntMountain  | 225-315 | GenE   |
# | NachesRiver      | MeadowsPass    | 210-315 | GenA   |
# | NachesRiver      | MeadowsPass    | 210-315 | GenE   |
# | UpperYakimaSouth | MeadowsPass    | 225-285 | GenA   |
# | NachesEast       | CayusePass     | 225-315 | GenE   |
# | NachesEast       | BumpingRidge   | 240-320 | GenE   |
# | RainierEast      | CorralPass     | 225-320 | GenE   |
# | UpperYakimaNorth | FishLake       | 225-315 | GenA   |
# | UpperYakimaSouth | SasseRidge     | 210-315 | GenA   |
# | NachesWest       | PotatoHill     | 225-320 | GenE   |
# | NachesRiver      | CougarMountain | 225-320 | GenA   |
# | NachesRiver      | CougarMountain | 225-320 | GenE   |
# | NachesWest       | SkateCreek     | 215-320 | GenA   |

# for ii, _wind_swath in enumerate(wind_swaths):
# for ii, _phi in enumerate(FrA1.phi_range):
FrA_phi=240
FrE_phi=90
create_monthly_ground=True
# create_monthly_ground=False
if create_monthly_ground:
    #for _froude in [FrA1, FrA2, FrA3, FrA4, FrA5, FrA6]:
    FrGenA=FrA5(phi=FrA_phi)
    create_freq_chart(criteria=NachesRiver,      wind=CougarMountain(WindDirMin=225, WindDirMax=320), froude=FrGenA)
    create_freq_chart(criteria=NachesRiver,      wind=MeadowsPass(   WindDirMin=210, WindDirMax=315), froude=FrGenA)
    create_freq_chart(criteria=UpperYakimaSouth, wind=MeadowsPass(   WindDirMin=225, WindDirMax=285), froude=FrGenA)
    create_freq_chart(criteria=UpperYakimaNorth, wind=FishLake(      WindDirMin=225, WindDirMax=315), froude=FrGenA)
    create_freq_chart(criteria=UpperYakimaSouth, wind=SasseRidge(    WindDirMin=210, WindDirMax=315), froude=FrGenA)

    #for _froude in [FrE1, FrE2, FrE3, FrE4, FrE5, FrE6, FrE7]:
    FrGenE=FrE5(phi=FrE_phi)
    create_freq_chart(criteria=RainierWest,      wind=BurntMountain( WindDirMin=225, WindDirMax=315), froude=FrGenE)
    create_freq_chart(criteria=NachesRiver,      wind=MeadowsPass(   WindDirMin=210, WindDirMax=315), froude=FrGenE)
    create_freq_chart(criteria=NachesEast,       wind=CayusePass(    WindDirMin=225, WindDirMax=315), froude=FrGenE)
    create_freq_chart(criteria=NachesEast,       wind=BumpingRidge(  WindDirMin=240, WindDirMax=320), froude=FrGenE)
    create_freq_chart(criteria=RainierEast,      wind=CorralPass(    WindDirMin=225, WindDirMax=320), froude=FrGenE)
    create_freq_chart(criteria=NachesWest,       wind=PotatoHill(    WindDirMin=225, WindDirMax=320), froude=FrGenE)
    create_freq_chart(criteria=NachesRiver,      wind=CougarMountain(WindDirMin=225, WindDirMax=320), froude=FrGenE)
    create_freq_chart(criteria=NachesWest,       wind=SkateCreek(    WindDirMin=215, WindDirMax=320), froude=FrGenE)
# 13

create_yearly_ground = True
# create_yearly_ground = False
if create_yearly_ground:
    #for _froude in [FrA1, FrA2, FrA3, FrA4, FrA5, FrA6]:
    FrGenA=FrA5(phi=FrA_phi)
    create_yearly_chart(criteria=NachesRiver,     wind=MeadowsPass(    WindDirMin=210, WindDirMax=315), froude=FrGenA,lwc_type=LwcType.GROUND)
    create_yearly_chart(criteria=UpperYakimaSouth,wind=MeadowsPass(    WindDirMin=225, WindDirMax=285), froude=FrGenA,lwc_type=LwcType.GROUND)
    create_yearly_chart(criteria=UpperYakimaNorth, wind=FishLake(      WindDirMin=225, WindDirMax=315), froude=FrGenA,lwc_type=LwcType.GROUND)
    create_yearly_chart(criteria=UpperYakimaSouth, wind=SasseRidge(    WindDirMin=210, WindDirMax=315), froude=FrGenA,lwc_type=LwcType.GROUND)
    create_yearly_chart(criteria=NachesRiver,      wind=CougarMountain(WindDirMin=225, WindDirMax=320), froude=FrGenA,lwc_type=LwcType.GROUND)

    #for _froude in [FrE1, FrE2, FrE3, FrE4, FrE5, FrE6, FrE7]:
    FrGenE=FrE5(phi=FrE_phi)
    create_yearly_chart(criteria=RainierWest,      wind=BurntMountain( WindDirMin=225, WindDirMax=315), froude=FrGenE,lwc_type=LwcType.GROUND)
    create_yearly_chart(criteria=NachesRiver,      wind=MeadowsPass(   WindDirMin=210, WindDirMax=315), froude=FrGenE,lwc_type=LwcType.GROUND)
    create_yearly_chart(criteria=NachesEast,       wind=CayusePass(    WindDirMin=225, WindDirMax=315), froude=FrGenE,lwc_type=LwcType.GROUND)
    create_yearly_chart(criteria=NachesEast,       wind=BumpingRidge(  WindDirMin=240, WindDirMax=320), froude=FrGenE,lwc_type=LwcType.GROUND)
    create_yearly_chart(criteria=RainierEast,      wind=CorralPass(    WindDirMin=225, WindDirMax=320), froude=FrGenE,lwc_type=LwcType.GROUND)
    create_yearly_chart(criteria=NachesWest,       wind=PotatoHill(    WindDirMin=225, WindDirMax=320), froude=FrGenE,lwc_type=LwcType.GROUND)
    create_yearly_chart(criteria=NachesRiver,      wind=CougarMountain(WindDirMin=225, WindDirMax=320), froude=FrGenE,lwc_type=LwcType.GROUND)
    create_yearly_chart(criteria=NachesWest,       wind=SkateCreek(    WindDirMin=215, WindDirMax=320), froude=FrGenE,lwc_type=LwcType.GROUND)
# 13

create_yearly_combined=True
# create_yearly_combined=False
if create_yearly_combined:
    FrGenA=FrA5(phi=FrA_phi)
    create_yearly_combined_chart(criteria=NachesRiver,      wind=MeadowsPass(   WindDirMin=210, WindDirMax=315), froude=FrGenA)
    create_yearly_combined_chart(criteria=UpperYakimaSouth, wind=MeadowsPass(   WindDirMin=225, WindDirMax=285), froude=FrGenA)
    create_yearly_combined_chart(criteria=UpperYakimaNorth, wind=FishLake(      WindDirMin=225, WindDirMax=315), froude=FrGenA)
    create_yearly_combined_chart(criteria=UpperYakimaSouth, wind=SasseRidge(    WindDirMin=210, WindDirMax=315), froude=FrGenA)
    create_yearly_combined_chart(criteria=NachesRiver,      wind=CougarMountain(WindDirMin=225, WindDirMax=320), froude=FrGenA)
    FrGenE=FrE5(phi=FrE_phi)
    create_yearly_combined_chart(criteria=RainierWest,      wind=BurntMountain( WindDirMin=225, WindDirMax=315), froude=FrGenE)
    create_yearly_combined_chart(criteria=NachesRiver,      wind=MeadowsPass(   WindDirMin=210, WindDirMax=315), froude=FrGenE)
    create_yearly_combined_chart(criteria=NachesEast,       wind=CayusePass(    WindDirMin=225, WindDirMax=315), froude=FrGenE)
    create_yearly_combined_chart(criteria=NachesEast,       wind=BumpingRidge(  WindDirMin=240, WindDirMax=320), froude=FrGenE)
    create_yearly_combined_chart(criteria=RainierEast,      wind=CorralPass(    WindDirMin=225, WindDirMax=320), froude=FrGenE)
    create_yearly_combined_chart(criteria=NachesWest,       wind=PotatoHill(    WindDirMin=225, WindDirMax=320), froude=FrGenE)
    create_yearly_combined_chart(criteria=NachesRiver,      wind=CougarMountain(WindDirMin=225, WindDirMax=320), froude=FrGenE)
    create_yearly_combined_chart(criteria=NachesWest,       wind=SkateCreek(    WindDirMin=215, WindDirMax=320), froude=FrGenE)
# 13

create_monthly_combined=True
# create_monthly_combined=False
if create_monthly_combined:
    FrGenA=FrA5(phi=FrA_phi)
    create_monthly_combined_chart(criteria=NachesRiver,      wind=MeadowsPass(   WindDirMin=210, WindDirMax=315), froude=FrGenA)
    create_monthly_combined_chart(criteria=UpperYakimaSouth, wind=MeadowsPass(   WindDirMin=225, WindDirMax=285), froude=FrGenA)
    create_monthly_combined_chart(criteria=UpperYakimaNorth, wind=FishLake(      WindDirMin=225, WindDirMax=315), froude=FrGenA)
    create_monthly_combined_chart(criteria=UpperYakimaSouth, wind=SasseRidge(    WindDirMin=210, WindDirMax=315), froude=FrGenA)
    create_monthly_combined_chart(criteria=NachesRiver,      wind=CougarMountain(WindDirMin=225, WindDirMax=320), froude=FrGenA)

    FrGenE=FrE5(phi=FrE_phi)
    create_monthly_combined_chart(criteria=RainierWest,      wind=BurntMountain( WindDirMin=225, WindDirMax=315), froude=FrGenE)
    create_monthly_combined_chart(criteria=NachesRiver,      wind=MeadowsPass(   WindDirMin=210, WindDirMax=315), froude=FrGenE)
    create_monthly_combined_chart(criteria=NachesEast,       wind=CayusePass(    WindDirMin=225, WindDirMax=315), froude=FrGenE)
    create_monthly_combined_chart(criteria=NachesEast,       wind=BumpingRidge(  WindDirMin=240, WindDirMax=320), froude=FrGenE)
    create_monthly_combined_chart(criteria=RainierEast,      wind=CorralPass(    WindDirMin=225, WindDirMax=320), froude=FrGenE)
    create_monthly_combined_chart(criteria=NachesWest,       wind=PotatoHill(    WindDirMin=225, WindDirMax=320), froude=FrGenE)
    create_monthly_combined_chart(criteria=NachesRiver,      wind=CougarMountain(WindDirMin=225, WindDirMax=320), froude=FrGenE)
    create_monthly_combined_chart(criteria=NachesWest,       wind=SkateCreek(    WindDirMin=215, WindDirMax=320), froude=FrGenE)
# 13
# ----
# 51
# 60
