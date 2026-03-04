import numpy as np
import xarray as xr
import cartopy
import matplotlib.pyplot as plt
import netCDF4 as nc
# from wrf import to_np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os
import geocat.viz as gv
import geopandas as gpd
# from matplotlib.colors import LinearSegmentedColormap
# import proplot as pplt
import seaborn as sns
import seaborn.objects as so
# from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import datetime
import pandas as pd
import json
import datetime
import logging
import re
import pandas as pd
from rich.logging import RichHandler
from rich.traceback import install
import json
import collections
import rich_click as click
import enum
import inspect
import math

from matplotlib.animation import FuncAnimation
import matplotlib.animation as animation 
from rich.console import Console
from rich.syntax import Syntax
from rich.table import (Column, Table)
import matplotlib.ticker as ticker
import matplotlib
from matplotlib.colors import ListedColormap
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
from matplotlib.collections import LineCollection

import cartopy.feature
from cartopy.mpl.patch import geos_to_path
import cartopy.crs as ccrs

from netCDF4 import Dataset as netcdf_dataset
import matplotlib.colors as colors

import itertools

import datetime
from datetime import date
from datetime import timedelta

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm

import matplotlib.image as mpimg
from PIL import Image

matplotlib.rcParams['mathtext.fontset'] = 'stix'
matplotlib.rcParams['font.family'] = 'STIXGeneral'

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
# handlers=[RichHandler(console=Console(width=255, force_terminal=True)])


logger=logging.getLogger(__name__)

root_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
data_dir=os.path.join(root_dir, 'data')
shape_dir=os.path.join(data_dir, 'shapefiles')
background_dir=os.path.join(data_dir, 'background')

os.environ.setdefault('CARTOPY_USER_BACKGROUNDS', background_dir)

def _build_data_ensemble(sv_data, avg=False, frq=False):
    def _build_strata_ensemble(strata):
        _rv = DotMap(
            temperature=sv_data.AS_Tc if strata == ChartStrataType.AIR else sv_data.GS_Tc,
            lwc=sv_data.AS_LWC if strata == ChartStrataType.AIR else sv_data.GS_LWC,
            average=DotMap(), 
            frequency=DotMap())

        if avg:
            _rv.average.temperature=sv_data.AS_Tc.mean('Time') if strata == ChartStrataType.AIR else sv_data.GS_Tc.mean('Time')
            _rv.average.lwc=sv_data.AS_LWC.mean('Time') if strata == ChartStrataType.AIR else sv_data.GS_LWC.mean('Time')

        if frq:
            _rv.frequency.temperature=np.mean(np.where((_rv.temperature >-18) & (_rv.temperature <-6), 1, 0),0)*100
            _rv.frequency.lwc=np.mean(np.where(_rv.lwc > 0.01, 1, 0),0)*100
            _rv.frequency.tlwc=np.mean(np.where((_rv.lwc > 0.01) & (_rv.temperature >-18) & (_rv.temperature < -6), 1, 0),0)*100

        return _rv
    _de=DotMap(air=_build_strata_ensemble(ChartStrataType.AIR), ground=_build_strata_ensemble(ChartStrataType.GROUND))
    _de.limits.temperature=(min([_de.air.temperature.min().values.flatten()[0], _de.ground.temperature.min().values.flatten()[0]]) , max([_de.air.temperature.max().values.flatten()[0], _de.ground.temperature.max().values.flatten()[0]]))
    _de.limits.lwc=(min([_de.air.lwc.min().values.flatten()[0], _de.ground.lwc.min().values.flatten()[0]]) , max([_de.air.lwc.max().values.flatten()[0], _de.ground.lwc.max().values.flatten()[0]]))
    _de.limits.frequency=(
        min([
            _de.air.frequency.lwc.min(), 
            _de.ground.frequency.lwc.min(),
            _de.air.frequency.tlwc.min(), 
            _de.ground.frequency.tlwc.min(),
            _de.air.frequency.temperature.min(), 
            _de.ground.frequency.temperature.min(),
            ]) , 
        max([
            _de.air.frequency.lwc.max(), 
            _de.ground.frequency.lwc.max(),
            _de.air.frequency.tlwc.max(), 
            _de.ground.frequency.tlwc.max(),
            _de.air.frequency.temperature.max(), 
            _de.ground.frequency.temperature.max(),
            ]))
    return _de

def makedirs(*dirs):
    """
    Make directories with open permissions if they don't exist, else ensure the perms

    Args:
        dirs: directory paths

    Returns:
        The same directory paths that were input
    """
    _umask = os.umask(0)
    _mode = 0o7777 # stat.S_ISUID|stat.S_ISGID|stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO
    def _mk(_dir):
        _=os.chmod(_dir, _mode) if os.path.exists(_dir) else os.makedirs(_dir, _mode)
    try:
        list(map(_mk, dirs))
    finally:
        os.umask(_umask)
        return dirs[0] if (len(dirs)==1) else dirs
    

class Base(object):
    @property
    def file(self):
        _val=self._file
        if (_val is None) or not(os.path.exists(_val)): return self.logger.error(f'Invalid (or missing) file: "{_val}"')
        return _val
    @file.setter
    def file(self, value):  self._file=value
    @property
    def _qualname(self):
        if self.__qualname is None:
            module = self.__class__.__module__
            self._qualname=self.__class__.__name__ if ((module is(None)) or (module == str.__class__.__module__)) else '.'.join([module, self.__class__.__name__])
        return self.__qualname
    @_qualname.setter
    def _qualname(self, value): self.__qualname = value
    @property
    def logger(self):
        if self._logger is None: self.logger = logging.getLogger(self._qualname)
        return self._logger
    @logger.setter
    def logger(self, value): self._logger = value if not(isinstance(value, str)) else None
    def __getattr__(self, name): return self.__dict__.get(name, None)
    def __init__(self, *args, **kwargs): [self.__setattr__(kk,vv) for kk,vv in kwargs.items()]
    def __call__(self, *args, **kwargs):
        [self.__setattr__(kk,vv) for kk,vv in kwargs.items()]
        return self

class DotMap(collections.abc.MutableMapping, collections.OrderedDict, Base):
    """
        Data structure class with key/value and class attribute accessors
    """
    __ignore_re=[r'^_.*$', r'^awehoi.*$']
    def __delitem__(self, key): 
        odict=super(DotMap, self).__getattribute__('_odict')
        del odict[key]
    def __init__(self, *args, **kwargs):
        super(DotMap, self).__setattr__( '_odict', collections.OrderedDict() )
        list(map(lambda x: [self.__setattr__(kk,vv) for kk,vv in (x.items() if hasattr(x, 'items') else {}.items())], list(args) + [kwargs]))
    def __getattr__(self, key, *args, **kwargs):
        odict = super(DotMap, self).__getattribute__('_odict')
        return odict.get(key, odict.setdefault(key,DotMap()))
    def __setattr__(self, key, val, *args, **kwargs):
        if isinstance(val, collections.abc.Mapping): return self._odict.update({key: DotMap(val)})
        elif isinstance(val,tuple) and hasattr(val, '_asdict'):return self.__setattr__(key, val._asdict(), *args, **kwargs)
        else:return self._odict.update({key:val})
    def __iter__(self, *args, **kwargs):
        for kk in self.keys(): yield kk
    def __len__(self, *args, **kwargs): return len(self.keys())
    @property
    def __dict__(self): return self._odict
    def __setstate__(self, state):
        super(DotMap, self).__setattr__( '_odict', collections.OrderedDict() )
        self._odict.update( state )
    def __eq__(self, other): return self.__dict__ == other.__dict__
    def __ne__(self, other): return not self.__eq__(other)
    def __setitem__(self, *args, **kwargs): return self.__setattr__(*args, **kwargs)
    def __getitem__(self, *args, **kwargs): return self.__getattr__(*args, **kwargs)
    def __repr__(self):
        def _default(x):
            if callable(x) and hasattr(x, '_asdict') and not(x._asdict is None):
                return x()._asdict()
            return repr(x)
        # return json.dumps(self.__dict__, default=lambda x:x()._asdict() if hasattr(x, '_asdict') else repr(x), indent = 4)
        return json.dumps(self.__dict__, default=_default, indent = 4)
    def __call__(self, *args, **kwargs):
        if args and isinstance(args[0], collections.abc.Mapping):
            [self.__setattr__(kk,vv) for kk,vv in args[0].items()]
        [self.__setattr__(kk,vv) for kk,vv in kwargs.items()]
        return self
    def _resolve_attributes(self, obj=None, ignore=None):
        obj=obj if obj else self
        ignore=ignore if ignore is not None else []
        _props = list(filter(lambda x: isinstance(getattr(obj.__class__,x),property) and not(re.match(r'^_.*$', x)), dir(obj.__class__)))
        _keys = list(filter(lambda x: not(x.startswith('_')), obj.__dict__.keys()))
        return collections.OrderedDict([(kk,getattr(obj, kk)) for kk in sorted(list(set(_keys + _props) - set(ignore) ))])
    def _asjson(self): return json.dumps(self._asdict(), indent=4)
    def _asdict(self, obj=None, ignore=None):
        if isinstance(ignore, str): ignore=[ignore]
        if ignore is(None): ignore=[]
        if obj is None:
            _dd=self._resolve_attributes()
        else:
            _dd = obj._asdict() if hasattr(obj, '_asdict') else (obj if isinstance(obj, collections.abc.Mapping) else (obj.__dict__ if hasattr(obj, '__dict__') else dict(obj)))
        def _yield(obj):
            if hasattr(obj, '_asdict'):
                if isinstance(obj, tuple):
                    return collections.OrderedDict([(kk,_yield(vv)) for kk,vv in obj._asdict().items()])
                else:
                    return obj._asdict()
            if isinstance(obj, collections.abc.Mapping): return collections.OrderedDict([(kk,_yield(vv)) for kk,vv in obj.items()])
            elif isinstance(obj, list): return [_yield(_obj) for _obj in obj]
            elif isinstance(obj, datetime.datetime): return '{}'.format(obj)
            elif isinstance(obj, bytes): return obj.decode('utf8')
            elif hasattr(obj, '__dict__'): return _yield(obj.__dict__)
            else: return obj
        _dd = collections.OrderedDict([(kk, _yield(vv) ) for kk,vv in _dd.items() if ( (vv is not(None)) and ( not(kk.startswith('_')) or any([re.match(_re, kk) for _re in self.__ignore_re]) ) ) ])
        return _dd
    def __format__(self, spec, *args, **kwargs):
        if 'json' in spec.lower(): return self._asjson()
        return super(DotMap, self).__format__(spec, *args, **kwargs)
    def pop(self, *args, **kwargs): return self.__dict__.pop(*args, **kwargs)
    def items(self, *args, **kwargs): return self.__dict__.items(*args, **kwargs)
    def keys(self, *args, **kwargs): return self.__dict__.keys(*args, **kwargs)
    def get(self, name, *args, **kwargs): return self.__getattr__(name, *args, **kwargs)
    def values(self, *args, **kwargs): return self.__dict__.values(*args, **kwargs)
    def setdefault(self, *args, **kwargs): return self.__dict__.setdefault(*args, **kwargs)
    def match(self,key_val, *args, **kwargs): return [result for result in self.imatch(key_val, *args, **kwargs)]
    def imatch(self, key_val, *args, **kwargs):
        key,val=key_val
        maintain_structure=kwargs.get('maintain_structure',False)
        def _yield(dd=self):
            if isinstance(dd, collections.abc.Mapping):
                for kk,vv in dd.items():
                    if isinstance(vv,str):
                        if all([re.match(key,kk),re.match(val,vv)]):
                            yield dd
                    else:
                        for _match in _yield(vv):
                            if maintain_structure:
                                yield DotMap(dict(dd, **{kk:_match}))
                            else:
                                yield _match
            elif isinstance(dd, (list,tuple)):
                for ii in dd:
                    for _match in _yield(ii): yield _match
            elif isinstance(dd,str): pass
            else: self.logger.error('Unhandled Type: {}'.format(type(dd)))
        for result in _yield(): yield result
    def find(self, *keys, **kwargs): return [result for result in self.ifind(*keys, **kwargs)]
    def ifind(self, *keys, **kwargs):
        maintain_structure=kwargs.get('maintain_structure',False)
        def _yield(dd=self):
            for kk,vv in dd.items():
                if kk in keys:
                    if maintain_structure: yield DotMap({kk:vv})
                    else: yield DotMap(vv) if isinstance(vv, collections.abc.Mapping) else vv
                if isinstance(vv,collections.abc.Mapping):
                    for _match in _yield(vv):
                        if maintain_structure: yield DotMap({kk:_match})
                        else: yield _match
        for result in _yield(): yield result
    def update(self, *args, **kwargs):
        [self.__setattr__(kk,vv) for arg in args for kk,vv in arg.items() if isinstance(arg, collections.abc.Mapping)]
        [self.__setattr__(kk,vv) for kk,vv in kwargs.items()]
        return self
    def merge(self, other, *args, **kwargs):
        if not isinstance(other, collections.abc.Mapping): raise RuntimeError("Attempting to merge DotMap with type {}... i dunno how to do that".format(type(other)))
        def _update(_d, _u):
            [_d.__setitem__(kk, (_update(_d.get(kk, {}), vv) if isinstance(vv, collections.abc.Mapping) else vv)) for kk,vv in _u.items()]
            return _d
        _update(self.__dict__, other)
        return self

class SmartDict(DotMap):
    def __setattr__(self, name, value): return super(SmartDict, self).__setattr__(name, value) if value is not(None) else None

class DomainFile(Base):
    @property
    def data(self):
        if self._data is None: 
            logger.info(f'Loading Domain File "{self.file}"')
            self.data = nc.Dataset(self.file)
            logger.info(f'Done.')
        return self._data
    @data.setter
    def data(self, value): self._data=value
    @property
    def lat(self):
        if self._lat is None: self.lat=self.data.variables['XLAT'][:].squeeze()
        return self._lat
    @lat.setter
    def lat(self, value): self._lat = value
    @property
    def lon(self):
        if self._lon is None: self.lon=self.data.variables['XLONG'][:].squeeze()
        return self._lon
    @lon.setter
    def lon(self, value): self._lon = value
    @property
    def height(self):
        if self._height is None: self.height=self.data.variables['HGT'][:]
        return self._height
    @height.setter
    def height(self, value): self._height = value
    
class ShapeFile(Base):
    @property
    def file(self):
        if self._file is None:
            self.file = '/glade/work/meghan/Montana/Montana_Terrain/data/Big_Hole.shp'
        _val=self._file
        if (_val is None) or not(os.path.exists(_val)): self.logger.error(f'Invalid (or missing) file: "{_val}"')
        return _val
    @file.setter
    def file(self, value): self._file=value
    @property
    def data(self):
        if self._data is None:
            logger.info(f'Loading Shapefile "{self.file}"')
            self.data = gpd.read_file(self.file)
            logger.info(f'Done.')
        return self._data
    @data.setter
    def data(self, value): self._data=value

    def plot(self, *args, **kwargs):
        return
        return self.data.plot(*args, **kwargs)

class SvFile(Base):
    @property
    def data(self):
        if self._data is None:
            logger.info(f'Loading SV File "{self.file}"')
            self.data = xr.open_dataset(self.file, engine = 'netcdf4')
            logger.info('Done.')
        return self._data
    @data.setter
    def data(self, value): self._data=value

    @property
    def time(self):
        if self._time is None:
            self.time = self.data.Time
        return self._time
    @time.setter
    def time(self, value): self._time = value

    @property
    def data_ensemble(self):
        if self._data_ensemble is None:
            logger.info('Building Data Ensemble')
            self.data_ensemble = self._build_data_ensemble()
            logger.info('Done.')
        return self._data_ensemble
    @data_ensemble.setter
    def data_ensemble(self, value): self._data_ensemble=value

    @property
    def data_range(self):
        if self._data_range is None:
            self.data_range = self._get_data_range()
        return self._data_range
    @data_range.setter
    def data_range(self, value): self._data_range=value

    def _get_data_range(self):
        if re.match(r'^.*Season.*nc$', os.path.basename(self.file), flags=re.I):
            return ChartRangeType.SEASON
        mm=re.match(r'^.*?(?P<month>[\d]{2}).nc$', os.path.basename(self.file), flags=re.I)
        if mm:
            return ChartRangeType(int(mm.groupdict().get('month')))
        if re.match(r'^.*(Jan).*nc$', os.path.basename(self.file), flags=re.I):
            return ChartRangeType.JANUARY
        elif re.match(r'^.*(Feb).*nc$', os.path.basename(self.file), flags=re.I):
            return ChartRangeType.FEBRUARY
        elif re.match(r'^.*(Mar).*nc$', os.path.basename(self.file), flags=re.I):
            return ChartRangeType.MARCH
        elif re.match(r'^.*(Apr).*nc$', os.path.basename(self.file), flags=re.I):
            return ChartRangeType.APRIL
        elif re.match(r'^.*(MAY).*nc$', os.path.basename(self.file), flags=re.I):
            return ChartRangeType.MAY
        elif re.match(r'^.*(JUN).*nc$', os.path.basename(self.file), flags=re.I):
            return ChartRangeType.JUNE
        elif re.match(r'^.*(JUL).*nc$', os.path.basename(self.file), flags=re.I):
            return ChartRangeType.JULY
        elif re.match(r'^.*(Aug).*nc$', os.path.basename(self.file), flags=re.I):
            return ChartRangeType.AUGUST
        elif re.match(r'^.*(Seq).*nc$', os.path.basename(self.file), flags=re.I):
            return ChartRangeType.SEPTEMBER
        elif re.match(r'^.*(Oct).*nc$', os.path.basename(self.file), flags=re.I):
            return ChartRangeType.OCTOBER
        elif re.match(r'^.*(Nov).*nc$', os.path.basename(self.file), flags=re.I):
            return ChartRangeType.NOVEMBER
        elif re.match(r'^.*(Dec).*nc$', os.path.basename(self.file), flags=re.I):
            return ChartRangeType.DECEMBER
        
    def _build_data_ensemble(self):
        def _build_strata_ensemble(strata):
            _rv = DotMap(
                # temperature=self.data.AS_Tc if strata == ChartStrataType.AIR else self.data.GS_Tc,
                # lwc=self.data.AS_LWC if strata == ChartStrataType.AIR else self.data.GS_LWC,
                temperature=self.data.AS_Tc if strata == ChartStrataType.AIR else self.data.GS_Tc2,
                lwc=self.data.AS_LWC if strata == ChartStrataType.AIR else self.data.GS_LWC2,
                average=DotMap(), 
                frequency=DotMap())

            if self.avg:
                # _rv.average.temperature=self.data.AS_Tc.mean('Time') if strata == ChartStrataType.AIR else self.data.GS_Tc.mean('Time')
                # _rv.average.lwc=self.data.AS_LWC.mean('Time') if strata == ChartStrataType.AIR else self.data.GS_LWC.mean('Time')

                _rv.average.temperature=self.data.AS_Tc.mean('Time') if strata == ChartStrataType.AIR else self.data.GS_Tc2.mean('Time')
                _rv.average.lwc=self.data.AS_LWC.mean('Time') if strata == ChartStrataType.AIR else self.data.GS_LWC2.mean('Time')

                # _lwc=self.data.AS_LWC.mean('Time') if strata == ChartStrataType.AIR else self.data.GS_LWC.mean('Time')
                # _rv.average.lwc=np.where(_lwc > 0.009999, _lwc, np.nan)

            if self.frq:
                _tmp=np.mean(np.where((_rv.temperature >-17.9999) & (_rv.temperature <-6.0001), 1, 0),0)*100
                _rv.frequency.temperature=np.where(_tmp > 5, _tmp, np.nan)
                # _rv.frequency.temperature=np.mean(np.where((_rv.temperature >-18) & (_rv.temperature <-6), 1, 0),0)*100

                _lwc=np.mean(np.where(_rv.lwc > 0.009999, 1, 0),0)*100
                _rv.frequency.lwc=np.where(_lwc > 5, _lwc, np.nan)

                _tlwc=np.mean(np.where((_rv.lwc > 0.009999) & (_rv.temperature >-17.9999) & (_rv.temperature < -6.0001), 1, 0),0)*100
                _rv.frequency.tlwc=np.where(_tlwc > 5, _tlwc, np.nan)

            return _rv
        
        def _build_wind_ensemble(strata):
            suffix=wind_suffix_map.get(strata)
            
            _rv=DotMap(
                temperature=self.data[f'Tc_{suffix}'],
                u=self.data[f'U_{suffix}'],
                v=self.data[f'V_{suffix}'],
                z=self.data[f'Z_{suffix}'],
                speed=np.sqrt(self.data[f'U_{suffix}']**2 + self.data[f'V_{suffix}']**2))
            
            if self.avg:
                _rv.average.temperature=_rv.temperature.mean('Time')
                _rv.average.u=_rv.u.mean('Time')
                _rv.average.v=_rv.v.mean('Time')
                _rv.average.z=_rv.z.mean('Time')
                _rv.average.speed=_rv.speed.mean('Time')
                

            return _rv
        
        if self.wind:
            _de=DotMap(
                mb250=_build_wind_ensemble(ChartStrataType.MB250) if self.mb250 else DotMap(),
                mb500=_build_wind_ensemble(ChartStrataType.MB500) if self.mb500 else DotMap(), 
                mb700=_build_wind_ensemble(ChartStrataType.MB700) if self.mb700 else DotMap(), 
                mb850=_build_wind_ensemble(ChartStrataType.MB850) if self.mb850 else DotMap())
        else:
            _de=DotMap(air=_build_strata_ensemble(ChartStrataType.AIR), ground=_build_strata_ensemble(ChartStrataType.GROUND))
        self.logger.debug(f'Data Ensemble:\n\t{_de}')
        return _de


class ChartStrataType(enum.IntEnum):
    GROUND=0
    AIR=1
    MB250=2
    MB500=3
    MB700=4
    MB850=5

wind_suffix_map={
    ChartStrataType.MB250:'250MB',
    ChartStrataType.MB500:'500MB',
    ChartStrataType.MB700:'700MB',
    ChartStrataType.MB850:'850MB'}
class ChartVariableType(enum.IntEnum):
    TEMPERATURE=0
    LWC=1
    TLWC=2
    WIND=3
    Z=4

class ChartMeasurementType(enum.IntEnum):
    FREQUENCY=0
    AVERAGE=1
    ANIMATION=2

class ChartRangeType(enum.IntEnum):
    SEASON=0
    JANUARY=1
    FEBRUARY=2
    MARCH=3
    APRIL=4
    MAY=5
    JUNE=6
    JULY=7
    AUGUST=8
    SEPTEMBER=9
    OCTOBER=10
    NOVEMBER=11
    DECEMBER=12

class MapHandler(Base):
    @property
    def all(self):
        return self._all
    @all.setter
    def all(self, value):
        self._all=value
    @property
    def extent(self):
        if self._extent is None:
            self.extent=(-122.5,-119, 45.5, 47.9)
        return self._extent
    @extent.setter
    def extent(self, value):
        self._extent=value
    @property
    def dom_file(self):
        if self._dom_file is None:
            self.dom_file=self.context.dom_file
        return self._dom_file
    @dom_file.setter
    def dom_file(self, value):
        self._dom_file=value if isinstance(value, DomainFile) else DomainFile(file=value)
    @property
    def sv_file(self):
        if self._sv_file is None:
            self.sv_file=self.context.sv_file
        return self._sv_file
    @sv_file.setter
    def sv_file(self, value):
        self._sv_file=value if isinstance(value, SvFile) else SvFile(file=value)
    @property
    def shp_file(self):
        if self._shp_file is None:
            self.shp_file=self.context.shp_file
        return self._shp_file
    @shp_file.setter
    def shp_file(self, value):
        self._shp_file=value if isinstance(value, ShapeFile) else ShapeFile(file=value)
    @property
    def roza_shapes(self):
        if self._roza_shapes is None:
            self.roza_shapes=DotMap(
                RozaFullBasin=gpd.read_file(os.path.join(shape_dir,'RozaFullBasin','RozaFullBasin.shp')),
                RozaSubBasin01=gpd.read_file(os.path.join(shape_dir,'RozaSubBasin01','RozaSubBasin01.shp')),
                RozaSubBasin02=gpd.read_file(os.path.join(shape_dir,'RozaSubBasin02','RozaSubBasin02.shp')),
                RozaSubBasin03=gpd.read_file(os.path.join(shape_dir,'RozaSubBasin03','RozaSubBasin03.shp')))
        return self._roza_shapes
    @roza_shapes.setter
    def roza_shapes(self, value):
        self._roza_shapes=value

def number_formatter(x, pos):
    return r'${} \times 10^{{{}}}$'.format(*('{:.3e}'.format(x).split('e')))

def get_all_blacks_cmap():
    N = 256
    vals = np.ones((N, 4))
    vals[:, 0] = np.linspace(0, 0, N)
    vals[:, 1] = np.linspace(0, 0, N)
    vals[:, 2] = np.linspace(0, 0, N)
    return ListedColormap(vals)

class CoolHandler(MapHandler):
    @property
    def model(self):
        if self._model is None:
            self.model='CONUS404 Current Climate'
        return self._model
    @model.setter
    def model(self, value):
        self._model=value
        
    def _create_chart(self, strata=ChartStrataType.AIR, variable=ChartVariableType.TEMPERATURE, measurement=ChartMeasurementType.FREQUENCY, cache=True):
        conditions=[]
        conditions.append(self.air if strata == ChartStrataType.AIR else self.gnd)
        conditions.append(self.tmp if variable == ChartVariableType.TEMPERATURE else self.lwc)
        conditions.append(self.frq if measurement == ChartMeasurementType.FREQUENCY else self.avg)

        data_range=self.sv_file.data_range
        self.logger.debug(f'Checking conditions for {data_range.name} {strata.name} {variable.name} {measurement.name}\n\t{conditions=}')
        if not(conditions and all(conditions)):
            self.logger.info(f'Conditions for {data_range.name} {strata.name} {variable.name} {measurement.name} Plot are not met, skipping.')
            return

        logger.info(f'Creating {strata.name} {variable.name} {measurement.name} ({data_range.name}) Plot')

        fig = plt.figure(figsize=(18.5, 10.5))
        ax = plt.axes(projection=ccrs.PlateCarree())
        # ax.background_img(name='ROZA', resolution='high')

        ax.set_extent(self.extent, crs=ccrs.PlateCarree())
        ax.add_feature(cfeature.STATES)

        _cmap={
            ChartVariableType.TEMPERATURE: 'ColdHot',
            ChartVariableType.TLWC: 'rainbow',
            ChartVariableType.LWC: 'viridis_r'}.get(
                variable, 
                'nipy_spectral',
                )
        try:
            self.sv_file.data_ensemble[strata.name.lower()][measurement.name.lower()][variable.name.lower()]
        except TypeError:
            _var=self.sv_file.data_ensemble
            if strata==ChartStrataType.AIR:
                _var=_var.air
            else:
                _var=_var.ground
            if measurement == ChartMeasurementType.AVERAGE:
                _var=_var.average
            else:
                _var=_var.frequency
            if variable == ChartVariableType.TEMPERATURE:
                _var=_var.temperature
            elif variable == ChartVariableType.TLWC:
                _var=_var.tlwc
            else:
                _var=_var.lwc
        
        _var=self.sv_file.data_ensemble[strata.name.lower()][measurement.name.lower()][variable.name.lower()]
        self.logger.info(f'{_var=}')
        _vara=_var
        if hasattr(_vara, 'to_numpy'):
            _vara=_vara.to_numpy()
        if hasattr(_vara, 'flatten'):
            _vara=_vara.flatten()
        self.logger.info(f'{_vara=}')
        data_max=np.nanmax(_vara)
        data_min=np.nanmin(_vara)

        data_limits=(math.floor(data_min), math.ceil(data_max))
        self.logger.info(f'{data_limits=}')
        data_buff=int((max(data_limits)-min(data_limits))/10.)

        _cont_kwargs={
            # (ChartVariableType.TEMPERATURE, ChartMeasurementType.AVERAGE): DotMap(norm=colors.CenteredNorm(vcenter=0)),
            # ChartVariableType.TEMPERATURE: DotMap(levels=np.linspace(-26,20, 21)),
            (ChartVariableType.TLWC, ChartMeasurementType.FREQUENCY): DotMap(levels=np.linspace(min(min(data_limits), 0), 50, 11),),
            (ChartVariableType.LWC, ChartMeasurementType.FREQUENCY): DotMap(levels=np.linspace(min(min(data_limits), 0), 50, 11),),
            (ChartVariableType.TEMPERATURE, ChartMeasurementType.FREQUENCY): DotMap(levels=np.linspace(min(min(data_limits), 0), 50, 11),),
            # (ChartVariableType.LWC, ChartMeasurementType.FREQUENCY): DotMap(),
            (ChartVariableType.LWC, ChartMeasurementType.AVERAGE): DotMap(
                levels=np.linspace(min(min(data_limits), 0), 0.1, 11),
                # extend=True,
                ),
            # (ChartVariableType.LWC, ChartMeasurementType.FREQUENCY): DotMap(),
            }.get((variable, measurement), DotMap(
                levels=np.linspace(min(min(data_limits), 0), max(data_limits), 11),
            ))
        _fvar=_var
        if (variable == ChartVariableType.LWC):
            # if (measurement==ChartMeasurementType.FREQUENCY):
            #     _fvar=np.where(_var > 0.009999, _var, np.nan)

            if (measurement==ChartMeasurementType.AVERAGE):
                _fvar=np.where(_var > 0.009999, _var, np.nan)
        
        if (variable == ChartVariableType.TEMPERATURE) and (measurement==ChartMeasurementType.AVERAGE):
            _cont_var = _fvar
            _cont_var_flat=_cont_var
            if hasattr(_cont_var_flat, 'to_numpy'):
                _cont_var_flat=_cont_var_flat.to_numpy()
            if hasattr(_cont_var_flat, 'flatten'):
                _cont_var_flat=_cont_var_flat.flatten()

            self.logger.info(f'{_cont_var_flat=}')
            
            _max=np.nanmax(_cont_var_flat)
            _min=np.nanmin(_cont_var_flat)
            
            _mmax = -1*_min if _min<0 else _max
            _mmin = -1*_max if _max>0 else _min
            _cmap_max=max(_max, _mmax)
            _cmap_min=min(_min, _mmin)
            _cont_kwargs.levels=np.linspace(_cmap_min,   _cmap_max,   30)


        _cont=plt.contourf(
            to_np(self.dom_file.lon),
            to_np(self.dom_file.lat),
            _fvar,
            extend='both',
            cmap=_cmap,
            zorder=9,
            alpha = 0.8 if (variable == ChartMeasurementType.FREQUENCY) else 0.5,
            **_cont_kwargs)
        
        if (variable == ChartVariableType.LWC) and (measurement==ChartMeasurementType.AVERAGE):
            CS = ax.contour(
                to_np(self.dom_file.lon),
                to_np(self.dom_file.lat),
                _var,
                [0.01],
                # cmap=_cmap,
                colors='blue',
                zorder=10,
                alpha=1)
            ax.clabel(CS, inline=True, fontsize=10)
        
        if (variable == ChartVariableType.TEMPERATURE) and (measurement==ChartMeasurementType.AVERAGE):
            CS = ax.contour(
                to_np(self.dom_file.lon),
                to_np(self.dom_file.lat),
                _var,
                [-6.0],
                # cmap=_cmap,
                colors='blue',
                zorder=10,
                alpha=1)
            ax.clabel(CS, inline=True, fontsize=10)

        _topo = plt.contour(
            to_np(self.dom_file.lon),
            to_np(self.dom_file.lat),
            self.dom_file.height[0],
            alpha = 1,
            linewidths=0.3,
            zorder=9,
            cmap ='gray',
            levels = 50)
        
        
        # ax.clabel(_topo, inline = 1, fontsize = 6)
        _cbar = plt.colorbar(
            _cont,
            orientation="vertical",
            # ticks=np.arange(min(data_limits), max(data_limits)+data_buff, ((max(data_limits)+data_buff)-min(data_limits))/10  ),
            # drawedges=True,
            extendrect=True,
            shrink=0.9)
        
        _cbar.ax.tick_params(size=1, labelsize=14)
        _cbar_label=r'$Frequency\ \left(\%\right)$' if measurement==ChartMeasurementType.FREQUENCY else (r'$Temperature\ \left(^{\circ}C\right)$' if variable == ChartVariableType.TEMPERATURE else r'$LWC\ \left(\frac{g}{kg}\right)$')
        _cbar.set_label(_cbar_label, fontsize = 20)
        _gl = ax.gridlines(crs=ccrs.PlateCarree(),
                        draw_labels=True,
                        dms=False,
                        x_inline=False,
                        y_inline=False,
                        linewidth=1,
                        color="k",
                        alpha=0.25,
                        zorder=4)
        
        _gl.top_labels = False
        _gl.right_labels = False
        _gl.xlabel_style = {"rotation": 45, "size": 16}
        _gl.ylabel_style = {"rotation": 0, "size": 16}
        _gl.xlines = True
        _gl.ylines = True


        RozaFullBasin=gpd.read_file(os.path.join(shape_dir,'RozaFullBasin','RozaFullBasin.shp'))
        RozaSubBasin01=gpd.read_file(os.path.join(shape_dir,'RozaSubBasin01','RozaSubBasin01.shp'))
        RozaSubBasin02=gpd.read_file(os.path.join(shape_dir,'RozaSubBasin02','RozaSubBasin02.shp'))
        RozaSubBasin03=gpd.read_file(os.path.join(shape_dir,'RozaSubBasin03','RozaSubBasin03.shp'))
        ax.plot(RozaSubBasin01.Lon.to_list(), RozaSubBasin01.Lat.to_list(), linewidth=1, color='k')
        ax.plot(RozaSubBasin02.Lon.to_list(), RozaSubBasin02.Lat.to_list(), linewidth=1, color='k')
        ax.plot(RozaSubBasin03.Lon.to_list(), RozaSubBasin03.Lat.to_list(), linewidth=1, color='k')
        ax.plot(RozaFullBasin.Lon.to_list(),  RozaFullBasin.Lat.to_list(),  linewidth=2, color='k')

        # ax.plot(self.roza_shapes.RozaSubBasin01.Lon.to_list(), self.roza_shapes.RozaSubBasin01.Lat.to_list(), linewidth=1, color='k')
        # ax.plot(self.roza_shapes.RozaSubBasin02.Lon.to_list(), self.roza_shapes.RozaSubBasin02.Lat.to_list(), linewidth=1, color='k')
        # ax.plot(self.roza_shapes.RozaSubBasin02.Lon.to_list(), self.roza_shapes.RozaSubBasin02.Lat.to_list(), linewidth=1, color='k')
        # ax.plot(self.roza_shapes.RozaFullBasin.Lon.to_list(), self.roza_shapes.RozaFullBasin.Lat.to_list(), linewidth=2, color='k')

        title_strata='Airborne' if strata in [ChartStrataType.AIR] else 'Ground'
        title_variable='Temperature' if variable in [ChartVariableType.TEMPERATURE] else 'LWC'
        title_range = 'Nov - Apr' if data_range in [ChartRangeType.SEASON] else data_range.name.capitalize()
        title_detail=f'{title_strata} {measurement.name.capitalize()} of Seedable Conditions ({title_range})' if ((measurement == ChartMeasurementType.FREQUENCY) and (variable==ChartVariableType.TLWC)) else f'{title_strata} {title_variable} {measurement.name.capitalize()} ({title_range})'
        title=f'{self.model}\n{title_detail}'

        gv.set_titles_and_labels(ax,maintitle=title,maintitlefontsize=22)
        self.shp_file.plot(ax=ax, alpha = 1, color = 'black',label = 'Yakima_Basin')

        fig.patch.set_facecolor('white')
        model_name=self.model.split()[0].upper()
        output_dir=os.path.abspath('.')
        output_file=f"RZ_{model_name}_{data_range.name}_{strata.name}_{variable.name}_{measurement.name}.png"
        output_path=os.path.join(output_dir, output_file)
        
        logger.info(f'Saving Plot to "{output_path}"...')
        plt.savefig(output_path, dpi=300, transparent=False)
        logger.info('Saved.')
        plt.close()
        
        return output_path
    def create_chart(self, strata=ChartStrataType.AIR, variable=ChartVariableType.TEMPERATURE, measurement=ChartMeasurementType.FREQUENCY, cache=True):
        """
        Create the actual Map

        Args:
            strata: Where is the data (ChartStrataType)
            variable: What is the data (ChartVariableType)
            measurement: How is the data represented (ChartMeasurementType)
            cache: Use a data cache from a previous run (bool)

        Returns:
            Location of the output map
        """

        # Condition check -- do we really want to make this map?
        # Probably obsolete
        conditions=[]
        conditions.append(self.air if strata == ChartStrataType.AIR else self.gnd)
        conditions.append(self.tmp if variable == ChartVariableType.TEMPERATURE else self.lwc)
        conditions.append(self.frq if measurement == ChartMeasurementType.FREQUENCY else self.avg)

        data_range=self.sv_file.data_range
        self.logger.debug(f'Checking conditions for {data_range.name} {strata.name} {variable.name} {measurement.name}\n\t{conditions=}')
        if not(conditions and all(conditions)):
            self.logger.info(f'Conditions for {data_range.name} {strata.name} {variable.name} {measurement.name} Plot are not met, skipping.')
            return

        # Create the Figure and Axes
        logger.info(f'Creating {strata.name} {variable.name} {measurement.name} ({data_range.name}) Plot')
        model_name=self.model.split()[0].upper()
        output_name=f"RZ_{model_name}_{data_range.name}_{strata.name}_{variable.name}_{measurement.name}"
        fig = plt.figure(figsize=(18.5, 10.5))
        ax = plt.axes(projection=ccrs.PlateCarree())

        # Set Extent and add State lines
        ax.set_extent(self.extent, crs=ccrs.PlateCarree())
        ax.add_feature(cfeature.STATES)

        # Set the colormap based on the variable
        if measurement==ChartMeasurementType.FREQUENCY:
            _cmap='cubehelix_r'
        else:
            _cmap={
                ChartVariableType.TEMPERATURE: 'ColdHot',
                ChartVariableType.TLWC: 'rainbow',
                ChartVariableType.LWC: 'viridis_r'}.get(
                    variable, 
                    'nipy_spectral',
                    )
        
        # Get the data from a cache file if it exists
        _cache_dir=makedirs(os.path.join(root_dir, 'cache', output_name))
        _cache_file=os.path.join(_cache_dir, f'{output_name}.nc')
        if cache and os.path.exists(_cache_file):
            self.logger.info(f'Loading data from cache "{_cache_file}"')
            data = xr.open_dataset(_cache_file, engine = 'netcdf4')
            _var=data.data
            self.logger.info(f'Loaded data from cache "{_cache_file}"')

        # If no cache, generate from the SV File object
        else:
            try:
                self.sv_file.data_ensemble[strata.name.lower()][measurement.name.lower()][variable.name.lower()]
            except TypeError:
                _var=self.sv_file.data_ensemble
                if strata==ChartStrataType.AIR:
                    _var=_var.air
                else:
                    _var=_var.ground
                if measurement == ChartMeasurementType.AVERAGE:
                    _var=_var.average
                else:
                    _var=_var.frequency
                if variable == ChartVariableType.TEMPERATURE:
                    _var=_var.temperature
                elif variable == ChartVariableType.TLWC:
                    _var=_var.tlwc
                elif variable == ChartVariableType.TLPLWC:
                    _var=_var.tlplwc
                elif variable == ChartVariableType.TALLLWC:
                    _var=_var.talllwc
                elif variable == ChartVariableType.TEMPERATURE_ALL_RANGE:
                    _var=_var.temperature_all_range
                elif variable == ChartVariableType.TEMPERATURE_LP_RANGE:
                    _var=_var.temperature_lp_range
                elif variable == ChartVariableType.LWC:
                    _var=_var.lwc
                else:
                    self.logger.error(f'UNHANDLED VARIABLE "{variable}"')
                    _var=_var.lwc

            # Save the data to cache, regardless
            _var=self.sv_file.data_ensemble[strata.name.lower()][measurement.name.lower()][variable.name.lower()]
            self.logger.info(f'Saving data to cache "{_cache_file}"')
            _cvar = _var if isinstance(_var, np.ndarray) else _var.to_numpy()
            dataset = xr.Dataset(data_vars = dict(
                    data=(["south_north","west_east"],_cvar),
                ),
                coords = dict(
                    XLONG = (["south_north","west_east"],self.dom_file.lon),
                    XLAT  = (["south_north","west_east"],self.dom_file.lat),
                ),
            )
            dataset.to_netcdf(_cache_file)
            self.logger.info(f'Saved data to cache "{_cache_file}"')


        # Get the data limits    
        self.logger.info(f'{_var=}')
        _vara=_var
        if hasattr(_vara, 'to_numpy'):
            _vara=_vara.to_numpy()
        if hasattr(_vara, 'flatten'):
            _vara=_vara.flatten()
        self.logger.info(f'{_vara=}')
        data_max=np.nanmax(_vara)
        data_min=np.nanmin(_vara)

        data_limits=(math.floor(data_min), math.ceil(data_max))
        self.logger.info(f'{data_limits=}')

        # Set the common contour ranges for the data types being mapped
        _cont_kwargs={
            (ChartVariableType.TLWC, ChartMeasurementType.FREQUENCY): DotMap(levels=np.linspace(min(min(data_limits), 0), 50, 11),),
            (ChartVariableType.LWC, ChartMeasurementType.FREQUENCY): DotMap(levels=np.linspace(min(min(data_limits), 0), 50, 11),),
            (ChartVariableType.TEMPERATURE, ChartMeasurementType.FREQUENCY): DotMap(levels=np.linspace(min(min(data_limits), 0), 50, 11),),
            (ChartVariableType.LWC, ChartMeasurementType.AVERAGE): DotMap(
                levels=np.linspace(min(min(data_limits), 0), 0.1, 11),
                ),
            }.get((variable, measurement), DotMap(
                levels=np.linspace(min(min(data_limits), 0), max(data_limits), 11),
            ))
        if measurement==ChartMeasurementType.FREQUENCY:
            _cont_kwargs= DotMap(levels=np.linspace(min(min(data_limits), 0), 50, 11),)
        # Mask LWC.AVERAGE lower than the criteria
        _fvar=_var
        if (variable == ChartVariableType.LWC):
            if (measurement==ChartMeasurementType.AVERAGE):
                _fvar=np.where(_var > 0.009999, _var, np.nan)
        
        # Create the contour levels with 0 in the middle for TEMPERATURE.AVERAGE
        if (variable == ChartVariableType.TEMPERATURE) and (measurement==ChartMeasurementType.AVERAGE):
            _cont_var = _fvar
            _cont_var_flat=_cont_var
            if hasattr(_cont_var_flat, 'to_numpy'):
                _cont_var_flat=_cont_var_flat.to_numpy()
            if hasattr(_cont_var_flat, 'flatten'):
                _cont_var_flat=_cont_var_flat.flatten()

            self.logger.info(f'{_cont_var_flat=}')
            
            _max=np.nanmax(_cont_var_flat)
            _min=np.nanmin(_cont_var_flat)
            
            _mmax = -1*_min if _min<0 else _max
            _mmin = -1*_max if _max>0 else _min
            _cmap_max=max(_max, _mmax)
            _cmap_min=min(_min, _mmin)
            _cont_kwargs.levels=np.linspace(_cmap_min,   _cmap_max,   30)

        # Plot the actual CONTOURF
        _cont=plt.contourf(
            self.dom_file.lon,
            self.dom_file.lat,
            # to_np(self.dom_file.lon),
            # to_np(self.dom_file.lat),
            _fvar,
            extend='both',
            cmap=_cmap,
            zorder=9,
            alpha = 0.7 if (variable == ChartMeasurementType.FREQUENCY) else 0.5,
            **_cont_kwargs)
        
        # Plot the criteria line for LWC.AVERAGE
        if (variable == ChartVariableType.LWC) and (measurement==ChartMeasurementType.AVERAGE):
            CS = ax.contour(
                self.dom_file.lon,
                self.dom_file.lat,
                # to_np(self.dom_file.lon),
                # to_np(self.dom_file.lat),
                _var,
                [0.01],
                colors='blue',
                zorder=10,
                alpha=1)
            ax.clabel(CS, inline=True, fontsize=10)
        
        # Plot the criteria line for TEMPERATURE.AVERAGE
        if (variable == ChartVariableType.TEMPERATURE) and (measurement==ChartMeasurementType.AVERAGE):
            CS = ax.contour(
                self.dom_file.lon,
                self.dom_file.lat,
                # to_np(self.dom_file.lon),
                # to_np(self.dom_file.lat),
                _var,
                [-6.0],
                colors='blue',
                zorder=10,
                alpha=1)
            ax.clabel(CS, inline=True, fontsize=10)

        # Plot the topo lines
        _topo = plt.contour(
            self.dom_file.lon,
            self.dom_file.lat,
            # to_np(self.dom_file.lon),
            # to_np(self.dom_file.lat),
            self.dom_file.height[0],
            alpha = 1,
            linewidths=0.3,
            zorder=9,
            cmap ='gray',
            levels = 50)
        
        # Generate the colorbar
        _cbar = plt.colorbar(
            _cont,
            orientation="vertical",
            extendrect=True,
            shrink=0.9)
        _cbar.ax.tick_params(size=1, labelsize=14)
        _cbar_label=r'$Frequency\ \left(\%\right)$' if measurement==ChartMeasurementType.FREQUENCY else (r'$Temperature\ \left(^{\circ}C\right)$' if variable == ChartVariableType.TEMPERATURE else r'$LWC\ \left(\frac{g}{kg}\right)$')
        _cbar.set_label(_cbar_label, fontsize = 20)

        # Create the gridlines
        _gl = ax.gridlines(crs=ccrs.PlateCarree(),
                        draw_labels=True,
                        dms=False,
                        x_inline=False,
                        y_inline=False,
                        linewidth=1,
                        color="k",
                        alpha=0.25,
                        zorder=4)
        _gl.top_labels = False
        _gl.right_labels = False
        _gl.xlabel_style = {"rotation": 45, "size": 16}
        _gl.ylabel_style = {"rotation": 0, "size": 16}
        _gl.xlines = True
        _gl.ylines = True


        RozaFullBasin=gpd.read_file(os.path.join(shape_dir,'RozaFullBasin','RozaFullBasin.shp'))
        RozaSubBasin01=gpd.read_file(os.path.join(shape_dir,'RozaSubBasin01','RozaSubBasin01.shp'))
        RozaSubBasin02=gpd.read_file(os.path.join(shape_dir,'RozaSubBasin02','RozaSubBasin02.shp'))
        RozaSubBasin03=gpd.read_file(os.path.join(shape_dir,'RozaSubBasin03','RozaSubBasin03.shp'))
        ax.plot(RozaSubBasin01.Lon.to_list(), RozaSubBasin01.Lat.to_list(), linewidth=1, color='k')
        ax.plot(RozaSubBasin02.Lon.to_list(), RozaSubBasin02.Lat.to_list(), linewidth=1, color='k')
        ax.plot(RozaSubBasin03.Lon.to_list(), RozaSubBasin03.Lat.to_list(), linewidth=1, color='k')
        ax.plot(RozaFullBasin.Lon.to_list(),  RozaFullBasin.Lat.to_list(),  linewidth=2, color='k')

        # ax.plot(self.roza_shapes.RozaSubBasin01.Lon.to_list(), self.roza_shapes.RozaSubBasin01.Lat.to_list(), linewidth=1, color='k')
        # ax.plot(self.roza_shapes.RozaSubBasin02.Lon.to_list(), self.roza_shapes.RozaSubBasin02.Lat.to_list(), linewidth=1, color='k')
        # ax.plot(self.roza_shapes.RozaSubBasin02.Lon.to_list(), self.roza_shapes.RozaSubBasin02.Lat.to_list(), linewidth=1, color='k')
        # ax.plot(self.roza_shapes.RozaFullBasin.Lon.to_list(), self.roza_shapes.RozaFullBasin.Lat.to_list(), linewidth=2, color='k')

        title_strata='Airborne' if strata in [ChartStrataType.AIR] else 'Ground'
        title_variable='Temperature' if variable in [ChartVariableType.TEMPERATURE] else 'LWC'
        title_range = 'Nov - Apr' if data_range in [ChartRangeType.SEASON] else data_range.name.capitalize()
        title_detail=f'{title_strata} {measurement.name.capitalize()} of Seedable Conditions ({title_range})' if ((measurement == ChartMeasurementType.FREQUENCY) and (variable==ChartVariableType.TLWC)) else f'{title_strata} {title_variable} {measurement.name.capitalize()} ({title_range})'
        title=f'{self.model}\n{title_detail}'

        gv.set_titles_and_labels(ax,maintitle=title,maintitlefontsize=22)
        self.shp_file.plot(ax=ax, alpha = 1, color = 'black',label = 'Yakima_Basin')

        fig.patch.set_facecolor('white')
        model_name=self.model.split()[0].upper()
        output_dir=os.path.abspath('.')
        output_file=f"RZ_{model_name}_{data_range.name}_{strata.name}_{variable.name}_{measurement.name}.png"
        output_path=os.path.join(output_dir, output_file)
        
        logger.info(f'Saving Plot to "{output_path}"...')
        plt.savefig(output_path, dpi=300, transparent=False)
        logger.info('Saved.')
        plt.close()
        
        return output_path
    
    def _process(self):
        self.air=bool(self.air or self.all)
        self.gnd=bool(self.gnd or self.all)
        self.frq=bool(self.frq or self.all)
        self.avg=bool(self.avg or self.all)
        self.lwc=bool(self.lwc or self.all)
        self.tmp=bool(self.tmp or self.all)
        self.sv_file(air=self.air,gnd=self.gnd,frq=self.frq,avg=self.avg,lwc=self.lwc,tmp=self.tmp)
    
    def _create_charts(self):
        self.logger.debug(f'Generating charts with conditions:\n\t{self.all=}\n\t{self.air=}\n\t{self.gnd=}\n\t{self.frq=}\n\t{self.avg=}\n\t{self.lwc=}\n\t{self.tmp=}')
        _desired_charts=[
            dict(strata=ChartStrataType.AIR, 
                variable=ChartVariableType.TLWC, 
                measurement=ChartMeasurementType.FREQUENCY),
            dict(strata=ChartStrataType.AIR, 
                variable=ChartVariableType.LWC, 
                measurement=ChartMeasurementType.FREQUENCY),
            dict(strata=ChartStrataType.AIR, 
                variable=ChartVariableType.TEMPERATURE, 
                measurement=ChartMeasurementType.FREQUENCY),
            # dict(strata=ChartStrataType.AIR, 
            #     variable=ChartVariableType.LWC, 
            #     measurement=ChartMeasurementType.AVERAGE),
            # dict(strata=ChartStrataType.AIR, 
            #     variable=ChartVariableType.TEMPERATURE, 
            #     measurement=ChartMeasurementType.AVERAGE),
            dict(strata=ChartStrataType.GROUND, 
                variable=ChartVariableType.TLWC, 
                measurement=ChartMeasurementType.FREQUENCY),
            dict(strata=ChartStrataType.GROUND, 
                variable=ChartVariableType.LWC, 
                measurement=ChartMeasurementType.FREQUENCY),
            dict(strata=ChartStrataType.GROUND, 
                variable=ChartVariableType.TEMPERATURE, 
                measurement=ChartMeasurementType.FREQUENCY),
            # dict(strata=ChartStrataType.GROUND, 
            #     variable=ChartVariableType.LWC, 
            #     measurement=ChartMeasurementType.AVERAGE),
            # dict(strata=ChartStrataType.GROUND, 
            #     variable=ChartVariableType.TEMPERATURE, 
            #     measurement=ChartMeasurementType.AVERAGE)
            ]
        return [self.create_chart(**dd) for dd in _desired_charts]

    def __call__(self, *args, **kwargs):
        self._process()
        self.output_paths=self._create_charts()
        return self


class CacheHandler(MapHandler):
    @property
    def model(self):
        if self._model is None:
            self.model='CONUS404 Current Climate'
        return self._model
    @model.setter
    def model(self, value):
        self._model=value

    def create_chart(self, strata=ChartStrataType.AIR, variable=ChartVariableType.TEMPERATURE, measurement=ChartMeasurementType.FREQUENCY, data_range=ChartRangeType.SEASON):
        """
        Create the actual Map

        Args:
            strata: Where is the data (ChartStrataType)
            variable: What is the data (ChartVariableType)
            measurement: How is the data represented (ChartMeasurementType)
            cache: Use a data cache from a previous run (bool)

        Returns:
            Location of the output map
        """

        # Condition check -- do we really want to make this map?
        # Probably obsolete
        conditions=[]
        conditions.append(self.air if strata == ChartStrataType.AIR else self.gnd)
        conditions.append(self.tmp if variable == ChartVariableType.TEMPERATURE else self.lwc)
        conditions.append(self.frq if measurement == ChartMeasurementType.FREQUENCY else self.avg)

        self.logger.debug(f'Checking conditions for {data_range.name} {strata.name} {variable.name} {measurement.name}\n\t{conditions=}')
        if not(conditions and all(conditions)):
            self.logger.info(f'Conditions for {data_range.name} {strata.name} {variable.name} {measurement.name} Plot are not met, skipping.')
            return

        # Create the Figure and Axes
        logger.info(f'Creating {strata.name} {variable.name} {measurement.name} ({data_range.name}) Plot')
        model_name=self.model.split()[0].upper()
        output_name=f"RZ_{model_name}_{data_range.name}_{strata.name}_{variable.name}_{measurement.name}"
        
        # Set Extent and add State lines
        fig = plt.figure(figsize=(18, 16))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_extent(self.extent, crs=ccrs.PlateCarree())
        ax.set_aspect(1 / np.cos(np.deg2rad(np.mean([self.extent[-2], self.extent[-1]]))))
        ax.add_feature(cfeature.STATES)

        # Set the colormap based on the variable
        if measurement==ChartMeasurementType.FREQUENCY:
            _cmap='cubehelix_r'
        else:
            _cmap={
                ChartVariableType.TEMPERATURE: 'ColdHot',
                ChartVariableType.TLWC: 'rainbow',
                ChartVariableType.LWC: 'viridis_r'}.get(
                    variable, 
                    'nipy_spectral',
                    )
        
        # Get the data from a cache file if it exists
        _cache_dir=makedirs(os.path.join(root_dir, 'cache', output_name))
        _cache_file=os.path.join(_cache_dir, f'{output_name}.nc')
        if os.path.exists(_cache_file):
            self.logger.info(f'Loading data from cache "{_cache_file}"')
            data = xr.open_dataset(_cache_file, engine = 'netcdf4')
            _var=data.data
            self.logger.info(f'Loaded data from cache "{_cache_file}"')

        # If no cache, generate from the SV File object
        else:
            self.logger.error(f'Cache not found for "{_cache_file}"')
            return 
            

        # Get the data limits    
        self.logger.info(f'{_var=}')
        _vara=_var
        if hasattr(_vara, 'to_numpy'):
            _vara=_vara.to_numpy()
        if hasattr(_vara, 'flatten'):
            _vara=_vara.flatten()
        self.logger.info(f'{_vara=}')
        data_max=np.nanmax(_vara)
        data_min=np.nanmin(_vara)

        data_limits=(math.floor(data_min), math.ceil(data_max))
        self.logger.info(f'{data_limits=}')

        # Set the common contour ranges for the data types being mapped
        _cont_kwargs={
            (ChartVariableType.TLWC, ChartMeasurementType.FREQUENCY): DotMap(levels=np.linspace(min(min(data_limits), 0), 50, 11),),
            (ChartVariableType.LWC, ChartMeasurementType.FREQUENCY): DotMap(levels=np.linspace(min(min(data_limits), 0), 50, 11),),
            (ChartVariableType.TEMPERATURE, ChartMeasurementType.FREQUENCY): DotMap(levels=np.linspace(min(min(data_limits), 0), 50, 11),),
            (ChartVariableType.LWC, ChartMeasurementType.AVERAGE): DotMap(
                levels=np.linspace(min(min(data_limits), 0), 0.1, 11),
                ),
            }.get((variable, measurement), DotMap(
                levels=np.linspace(min(min(data_limits), 0), max(data_limits), 11),
            ))
        if measurement==ChartMeasurementType.FREQUENCY:
            _cont_kwargs= DotMap(levels=np.linspace(min(min(data_limits), 0), 50, 11),)
        # Mask LWC.AVERAGE lower than the criteria
        _fvar=_var
        if (variable == ChartVariableType.LWC):
            if (measurement==ChartMeasurementType.AVERAGE):
                _fvar=np.where(_var > 0.009999, _var, np.nan)
        
        # Create the contour levels with 0 in the middle for TEMPERATURE.AVERAGE
        if (variable == ChartVariableType.TEMPERATURE) and (measurement==ChartMeasurementType.AVERAGE):
            _cont_var = _fvar
            _cont_var_flat=_cont_var
            if hasattr(_cont_var_flat, 'to_numpy'):
                _cont_var_flat=_cont_var_flat.to_numpy()
            if hasattr(_cont_var_flat, 'flatten'):
                _cont_var_flat=_cont_var_flat.flatten()

            self.logger.info(f'{_cont_var_flat=}')
            
            _max=np.nanmax(_cont_var_flat)
            _min=np.nanmin(_cont_var_flat)
            
            _mmax = -1*_min if _min<0 else _max
            _mmin = -1*_max if _max>0 else _min
            _cmap_max=max(_max, _mmax)
            _cmap_min=min(_min, _mmin)
            _cont_kwargs.levels=np.linspace(_cmap_min,   _cmap_max,   30)

        # Plot the actual CONTOURF
        _cont=plt.contourf(
            self.dom_file.lon,
            self.dom_file.lat,
            _fvar,
            extend='both',
            cmap=_cmap,
            zorder=9,
            alpha = 0.7 if (variable == ChartMeasurementType.FREQUENCY) else 0.5,
            **_cont_kwargs)
        
        # Plot the criteria line for LWC.AVERAGE
        if (variable == ChartVariableType.LWC) and (measurement==ChartMeasurementType.AVERAGE):
            CS = ax.contour(
                self.dom_file.lon,
                self.dom_file.lat,
                _var,
                [0.01],
                colors='blue',
                zorder=10,
                alpha=1)
            ax.clabel(CS, inline=True, fontsize=10)
        
        # Plot the criteria line for TEMPERATURE.AVERAGE
        if (variable == ChartVariableType.TEMPERATURE) and (measurement==ChartMeasurementType.AVERAGE):
            CS = ax.contour(
                self.dom_file.lon,
                self.dom_file.lat,
                _var,
                [-6.0],
                colors='blue',
                zorder=10,
                alpha=1)
            ax.clabel(CS, inline=True, fontsize=10)

        # Plot the topo lines
        _topo = plt.contour(
            self.dom_file.lon,
            self.dom_file.lat,
            self.dom_file.height[0],
            alpha = 1,
            linewidths=0.3,
            zorder=9,
            cmap ='gray',
            levels = 50)
        
        # Generate the colorbar
        import matplotlib.colors as mcolors
        _cbar = plt.colorbar(
            _cont,
            orientation="vertical",
            extendrect=True,
            shrink=0.9)
        _cbar.ax.tick_params(size=1, labelsize=14)
        ticks = np.linspace(0, 50, 11)  # increase number as needed
        _cbar.set_ticks(ticks)
        _cbar_label=r'$Frequency\ \left(\%\right)$' if measurement==ChartMeasurementType.FREQUENCY else (r'$Temperature\ \left(^{\circ}C\right)$' if variable == ChartVariableType.TEMPERATURE else r'$LWC\ \left(\frac{g}{kg}\right)$')
        _cbar.set_label(_cbar_label, fontsize = 20)

        # Create the gridlines
        _gl = ax.gridlines(crs=ccrs.PlateCarree(),
                        draw_labels=True,
                        dms=False,
                        x_inline=False,
                        y_inline=False,
                        linewidth=1,
                        color="k",
                        alpha=0.25,
                        zorder=4)
        _gl.top_labels = False
        _gl.right_labels = False
        _gl.xlabel_style = {"rotation": 45, "size": 16}
        _gl.ylabel_style = {"rotation": 0, "size": 16}
        _gl.xlines = True
        _gl.ylines = True


        RozaFullBasin=gpd.read_file(os.path.join(shape_dir,'RozaFullBasin','RozaFullBasin.shp'))
        RozaSubBasin01=gpd.read_file(os.path.join(shape_dir,'RozaSubBasin01','RozaSubBasin01.shp'))
        RozaSubBasin02=gpd.read_file(os.path.join(shape_dir,'RozaSubBasin02','RozaSubBasin02.shp'))
        RozaSubBasin03=gpd.read_file(os.path.join(shape_dir,'RozaSubBasin03','RozaSubBasin03.shp'))
        ax.plot(RozaSubBasin01.Lon.to_list(), RozaSubBasin01.Lat.to_list(), linewidth=1, color='k')
        ax.plot(RozaSubBasin02.Lon.to_list(), RozaSubBasin02.Lat.to_list(), linewidth=1, color='k')
        ax.plot(RozaSubBasin03.Lon.to_list(), RozaSubBasin03.Lat.to_list(), linewidth=1, color='k')
        ax.plot(RozaFullBasin.Lon.to_list(),  RozaFullBasin.Lat.to_list(),  linewidth=2, color='k')

        title_strata='Airborne' if strata in [ChartStrataType.AIR] else 'Ground'
        title_variable='Temperature' if variable in [ChartVariableType.TEMPERATURE] else 'LWC'
        title_range = 'Nov - Apr' if data_range in [ChartRangeType.SEASON] else data_range.name.capitalize()
        title_detail=f'{title_strata} {measurement.name.capitalize()} of Seedable Conditions ({title_range})' if ((measurement == ChartMeasurementType.FREQUENCY) and (variable==ChartVariableType.TLWC)) else f'{title_strata} {title_variable} {measurement.name.capitalize()} ({title_range})'
        title=f'{self.model}\n{title_detail}'

        gv.set_titles_and_labels(ax,maintitle=title,maintitlefontsize=22)
        self.shp_file.plot(ax=ax, alpha = 1, color = 'black',label = 'Yakima_Basin')

        fig.patch.set_facecolor('white')
        model_name=self.model.split()[0].upper()
        output_dir=os.path.abspath('.')
        output_file=f"RZ_{model_name}_{data_range.name}_{strata.name}_{variable.name}_{measurement.name}.png"
        output_path=os.path.join(output_dir, output_file)
        
        logger.info(f'Saving Plot to "{output_path}"...')
        plt.savefig(output_path, dpi=300, transparent=False)
        logger.info('Saved.')
        plt.close()
        
        return output_path
    
    def _process(self):
        self.air=bool(self.air or self.all)
        self.gnd=bool(self.gnd or self.all)
        self.frq=bool(self.frq or self.all)
        self.avg=bool(self.avg or self.all)
        self.lwc=bool(self.lwc or self.all)
        self.tmp=bool(self.tmp or self.all)
        self.sv_file(air=self.air,gnd=self.gnd,frq=self.frq,avg=self.avg,lwc=self.lwc,tmp=self.tmp)
    
    def _create_charts(self):
        self.logger.debug(f'Generating charts with conditions:\n\t{self.all=}\n\t{self.air=}\n\t{self.gnd=}\n\t{self.frq=}\n\t{self.avg=}\n\t{self.lwc=}\n\t{self.tmp=}')
        _desired_charts=[
            dict(strata=ChartStrataType.AIR, 
                variable=ChartVariableType.TLWC, 
                measurement=ChartMeasurementType.FREQUENCY),
            dict(strata=ChartStrataType.AIR, 
                variable=ChartVariableType.LWC, 
                measurement=ChartMeasurementType.FREQUENCY),
            dict(strata=ChartStrataType.AIR, 
                variable=ChartVariableType.TEMPERATURE, 
                measurement=ChartMeasurementType.FREQUENCY),
            # dict(strata=ChartStrataType.AIR, 
            #     variable=ChartVariableType.LWC, 
            #     measurement=ChartMeasurementType.AVERAGE),
            # dict(strata=ChartStrataType.AIR, 
            #     variable=ChartVariableType.TEMPERATURE, 
            #     measurement=ChartMeasurementType.AVERAGE),
            dict(strata=ChartStrataType.GROUND, 
                variable=ChartVariableType.TLWC, 
                measurement=ChartMeasurementType.FREQUENCY),
            dict(strata=ChartStrataType.GROUND, 
                variable=ChartVariableType.LWC, 
                measurement=ChartMeasurementType.FREQUENCY),
            dict(strata=ChartStrataType.GROUND, 
                variable=ChartVariableType.TEMPERATURE, 
                measurement=ChartMeasurementType.FREQUENCY),
            # dict(strata=ChartStrataType.GROUND, 
            #     variable=ChartVariableType.LWC, 
            #     measurement=ChartMeasurementType.AVERAGE),
            # dict(strata=ChartStrataType.GROUND, 
            #     variable=ChartVariableType.TEMPERATURE, 
            #     measurement=ChartMeasurementType.AVERAGE)
            ]
        # return [self.create_chart(**dd) for dd in _desired_charts]
        _var_range=[ChartVariableType.LWC, ChartVariableType.TEMPERATURE, ChartVariableType.TLWC]
        _data_range=[ChartRangeType.SEASON, ChartRangeType.JANUARY, ChartRangeType.FEBRUARY, ChartRangeType.MARCH, ChartRangeType.APRIL, ChartRangeType.NOVEMBER, ChartRangeType.DECEMBER]
        _strata_range=[ChartStrataType.AIR, ChartStrataType.GROUND]
        return [self.create_chart(strata=_strata, variable=_variable, measurement=ChartMeasurementType.FREQUENCY, data_range=_range) for _strata in _strata_range for _variable in _var_range for _range in _data_range]

    def __call__(self, *args, **kwargs):
        self._process()
        self.output_paths=self._create_charts()
        return self


class WindHandler(MapHandler):
    def create_chart(self, strata=ChartStrataType.MB700, variable=ChartVariableType.WIND, measurement=ChartMeasurementType.ANIMATION):
        if measurement==ChartMeasurementType.ANIMATION:
            self.create_animated_map(strata, variable, measurement)
        else:
            self.create_static_map(strata, variable, measurement)


    def create_animated_map(self, strata=ChartStrataType.MB700, variable=ChartVariableType.WIND, measurement=ChartMeasurementType.ANIMATION):
        conditions=[]
        conditions.append(self.__getattr__(strata.name.lower()))
        conditions.append(self.ani)

        data_range=self.sv_file.data_range
        self.logger.debug(f'Checking conditions for {data_range.name} {strata.name} {variable.name} {measurement.name}\n\t{conditions=}')
        if not(conditions and all(conditions)):
            self.logger.info(f'Conditions for {data_range.name} {strata.name} {variable.name} {measurement.name} Plot are not met, skipping.')
            return
        
        strata_name=wind_suffix_map.get(strata)
        # U-component of wind with respect to model grid
        U=self.sv_file.data_ensemble[strata.name.lower()]['u']

        # V-component of wind with respect to model grid
        V=self.sv_file.data_ensemble[strata.name.lower()]['v']
        
        # Geopotential height (PH + PHB)/9.81
        Z=self.sv_file.data_ensemble[strata.name.lower()]['z']

        # Wind Speed
        S=self.sv_file.data_ensemble[strata.name.lower()]['speed']

        # self.logger.info(f'{self.sv_file.data_ensemble[strata.name.lower()]=}')
        # self.logger.info(f'{strata.name.lower()=}')

        # self.logger.info(f'{U=}')
        # self.logger.info(f'{V=}')
        # self.logger.info(f'{Z=}')

        def get_data(ii):
            return S[ii], U[ii], V[ii]
        
        s, u, v = get_data(0)

        # data_max=max([max(xx) for tt in sv_data['Z_700MB'].values for xx in tt])
        # data_min=min([min(xx) for tt in sv_data['Z_700MB'].values for xx in tt])
        data_max=max([max(xx[np.isfinite(xx)]) for tt in S.values for xx in tt])
        data_min=min([min(xx[np.isfinite(xx)]) for tt in S.values for xx in tt])

        data_limits=(math.ceil(data_min)-1, math.ceil(data_max))
        data_buff=int((max(data_limits)-min(data_limits))/10)
        stagger=5
        qscale=500
        date_time=datetime.datetime.utcfromtimestamp( int((self.sv_file.data.Time[0] - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's')) )
        start=date_time
        end=datetime.datetime.utcfromtimestamp( int((self.sv_file.data.Time[-1] - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's')) )
        fig = plt.figure(figsize=(7.5, 4))
        # fig = plt.figure(figsize=(15, 8))
        # fig = plt.figure(figsize=(18.5, 10.5))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_extent(self.extent, crs=ccrs.PlateCarree())
        ax.add_feature(cfeature.STATES)
        scope_name='Roza'
        title=ax.set_title(f"{scope_name} Wind Contours ( {strata_name} )\n{date_time:%Y} {date_time:%B} {date_time:%d} {date_time:%H}:{date_time:%M}:{date_time:%S}", fontsize=14)
        _cmap='viridis_r'
        cont=[
            plt.contourf(
                to_np(self.dom_file.lon),
                to_np(self.dom_file.lat),
                s, 
                # levels=np.linspace(min(data_limits), max(data_limits), 11),
                cmap=_cmap,
                zorder=9,
                alpha = 0.5)]
        
        _topo = plt.contour(
            to_np(self.dom_file.lon),
            to_np(self.dom_file.lat),
            self.dom_file.height[0],
            alpha = 0.8,
            linewidths=0.3,
            zorder=9,
            cmap ='gray',
            levels = 50)
        
        _cbar = plt.colorbar(
            cont[0],
            label='Wind Speed (m/s)',
            orientation="vertical",
            ticks=np.arange(min(data_limits), max(data_limits)+data_buff, data_buff  ),
            drawedges=True,
            extendrect=True,
            shrink=0.9,
            format=ticker.FuncFormatter(number_formatter)
            )

        _q=plt.quiver(
            to_np(self.dom_file.lon)[::stagger, ::stagger], 
            to_np(self.dom_file.lat)[::stagger, ::stagger], 
            u[::stagger, ::stagger], 
            v[::stagger, ::stagger], 
            scale=qscale, 
            zorder=9,
            alpha=0.8,
            animated=True)

        plt.quiverkey(_q, 0.853, 0.9, 10, r'$5 \frac{m}{s}$', labelpos='E', coordinates='figure')

        _cbar.ax.tick_params(size=1, labelsize=10)
        _cbar.set_label(r'$Wind Speed ( \frac{m}{s} )$',fontsize = 12)
        _gl = ax.gridlines(
            crs=ccrs.PlateCarree(),
            draw_labels=True,
            dms=False,
            x_inline=False,
            y_inline=False,
            linewidth=1,
            color="k",
            alpha=0.25,
            zorder=4)
        _gl.top_labels = False
        _gl.right_labels = False
        _gl.xlabel_style = {"rotation": 45, "size": 10}
        _gl.ylabel_style = {"rotation": 0, "size": 10}
        _gl.xlines = True
        _gl.ylines = True


        def animate(ii):
            date_time=datetime.datetime.utcfromtimestamp( int((self.sv_file.data.Time[ii] - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's')) )
            pcnt=(ii/len(self.sv_file.data.Time))*100
            self.logger.info(f'Currently processing frame for {date_time} :: {pcnt:02.2f}%')
            _=[c.remove() for c in cont[0].collections]
            s, u, v = get_data(ii)
            cont[0] = ax.contourf(to_np(self.dom_file.lon), to_np(self.dom_file.lat), s, cmap=_cmap, zorder=4 ,alpha = 0.8)
            _q.set_UVC(u[::stagger, ::stagger], v[::stagger, ::stagger])
            # title.set_text(f"{date_time:%Y} - {scope_name} Wind Contours ({strata_name}) {date_time:%B} {date_time:%d} {date_time:%H}:{date_time:%M}:{date_time:%S} ")
            title.set_text(f"{scope_name} Wind Contours ( {strata_name} )\n{date_time:%Y} {date_time:%B} {date_time:%d} {date_time:%H}:{date_time:%M}:{date_time:%S}")
            
            return cont[0].collections+[title, _q]

        self.gif = True if not(any([self.gif, self.mov])) else self.gif
        if self.gif:
            self.logger.info(f'Creating Wind Contour Animated GIF ( {start} -- {end} )')
            ani = FuncAnimation(fig, animate, frames=len(self.sv_file.data.Time), blit=True, repeat=True)
            ani.save(f'WIND_{strata_name}_{scope_name}_{start:%Y}{start:%m}{start:%d}{start:%H}{start:%M}_{end:%Y}{end:%m}{end:%d}{end:%H}{end:%M}.gif')

        elif self.mov:
            self.logger.info(f'Creating Wind Contour Movie ( {start} -- {end} )')
            ani = FuncAnimation(fig, animate, frames=len(self.sv_file.data.Time), blit=False, repeat=True)
            writervideo = animation.FFMpegWriter(fps=5)
            ani.save(f'WIND_{strata_name}_{scope_name}_{start:%Y}{start:%m}{start:%d}{start:%H}{start:%M}_{end:%Y}{end:%m}{end:%d}{end:%H}{end:%M}.mp4', writer=writervideo)

    def create_static_map(self, strata=ChartStrataType.MB700, variable=ChartVariableType.WIND, measurement=ChartMeasurementType.AVERAGE):
        conditions=[]
        conditions.append(self.__getattr__(strata.name.lower()))
        conditions.append(self.avg)

        data_range=self.sv_file.data_range
        self.logger.debug(f'Checking conditions for {data_range.name} {strata.name} {variable.name} {measurement.name}\n\t{conditions=}')
        if not(conditions and all(conditions)):
            self.logger.info(f'Conditions for {data_range.name} {strata.name} {variable.name} {measurement.name} Plot are not met, skipping.')
            return
        
        strata_name=wind_suffix_map.get(strata)
        # U-component of wind with respect to model grid
        U=(self.sv_file.data_ensemble[strata.name.lower()]).average.u

        # V-component of wind with respect to model grid
        V=(self.sv_file.data_ensemble[strata.name.lower()]).average.v
        
        # Geopotential height (PH + PHB)/9.81
        Z=(self.sv_file.data_ensemble[strata.name.lower()]).average.z

        # Wind Speed
        S=(self.sv_file.data_ensemble[strata.name.lower()]).average.speed

        # data_max=max([max(xx[np.isfinite(xx)]) for tt in S.values for xx in tt])
        # data_min=min([min(xx[np.isfinite(xx)]) for tt in S.values for xx in tt])
        # data_max=max([max(xx[np.isfinite(xx)]) for tt in gnd_tmp.values for xx in tt])
        # data_limits=(math.ceil(data_min)-1, math.ceil(data_max))
        # data_buff=int((max(data_limits)-min(data_limits))/10)
        stagger=5
        qscale=500
        date_time=datetime.datetime.utcfromtimestamp( int((self.sv_file.data.Time[0] - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's')) )
        start=date_time
        end=datetime.datetime.utcfromtimestamp( int((self.sv_file.data.Time[-1] - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's')) )
        # fig = plt.figure(figsize=(7.5, 4))
        # fig = plt.figure(figsize=(15, 8))
        fig = plt.figure(figsize=(18.5, 10.5))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_extent(self.extent, crs=ccrs.PlateCarree())
        ax.add_feature(cfeature.STATES)
        scope_name='Roza'
        if f"{start:%Y} {start:%B}" == f"{end:%Y} {end:%B}":
            _time_deets=f'for {start:%Y} {start:%B}'
        else:
            _time_deets=f'from {start:%Y} {start:%B} to {end:%Y} {end:%B}'
        title_range = 'Nov - Apr' if data_range in [ChartRangeType.SEASON] else data_range.name.capitalize()
        title=ax.set_title(f"{scope_name} Wind Contours ( {strata_name} )\nAverage Winds ({title_range})", fontsize=22)
        _cmap='viridis_r'
        _cont=plt.contourf(
                to_np(self.dom_file.lon),
                to_np(self.dom_file.lat),
                S, 
                # levels=np.linspace(min(data_limits), max(data_limits), 11),
                cmap=_cmap,
                zorder=9,
                alpha = 0.6)
        
        _topo = plt.contour(
            to_np(self.dom_file.lon),
            to_np(self.dom_file.lat),
            self.dom_file.height[0],
            alpha = 0.6,
            linewidths=0.3,
            zorder=9,
            cmap = get_all_blacks_cmap(),
            levels = 50)
        
        _cbar = plt.colorbar(
            _cont,
            label=r'$Wind\ Speed\ \left(\frac{m}{s}\right)$',
            orientation="vertical",
            # ticks=np.arange(min(data_limits), max(data_limits)+data_buff, data_buff  ),
            drawedges=True,
            extendrect=True,
            shrink=0.9,
            # format=ticker.FuncFormatter(number_formatter)
            )

        _q=plt.quiver(
            to_np(self.dom_file.lon)[::stagger, ::stagger], 
            to_np(self.dom_file.lat)[::stagger, ::stagger], 
            U[::stagger, ::stagger], 
            V[::stagger, ::stagger], 
            scale=qscale, 
            zorder=9,
            alpha=0.8,
            animated=True)

        plt.quiverkey(_q, 0.853, 0.9, 10, r'$5 \frac{m}{s}$', labelpos='E', coordinates='figure')

        

        _cbar.ax.tick_params(size=1, labelsize=14)
        _cbar.set_label(r'$Wind\ Speed\ \left(\frac{m}{s}\right)$', fontsize=20)
        _gl = ax.gridlines(
            crs=ccrs.PlateCarree(),
            draw_labels=True,
            dms=False,
            x_inline=False,
            y_inline=False,
            linewidth=1,
            color="k",
            alpha=0.25,
            zorder=4)
        _gl.top_labels = False
        _gl.right_labels = False
        _gl.xlabel_style = {"rotation": 45, "size": 16}
        _gl.ylabel_style = {"rotation": 0, "size": 16}
        _gl.xlines = True
        _gl.ylines = True

        ax.plot(self.roza_shapes.RozaSubBasin01.Lon.to_list(), self.roza_shapes.RozaSubBasin01.Lat.to_list(), linewidth=1, color='k')
        ax.plot(self.roza_shapes.RozaSubBasin02.Lon.to_list(), self.roza_shapes.RozaSubBasin02.Lat.to_list(), linewidth=1, color='k')
        ax.plot(self.roza_shapes.RozaSubBasin02.Lon.to_list(), self.roza_shapes.RozaSubBasin02.Lat.to_list(), linewidth=1, color='k')
        ax.plot(self.roza_shapes.RozaFullBasin.Lon.to_list(), self.roza_shapes.RozaFullBasin.Lat.to_list(), linewidth=2, color='k')

        fig.patch.set_facecolor('white')
        
        output_dir=os.path.abspath('.')
        output_file=f"RZ_{data_range.name}_{strata.name}_{variable.name}_{measurement.name}.png"
        output_path=os.path.join(output_dir, output_file)
        
        logger.info(f'Saving Plot to "{output_path}"...')
        plt.savefig(output_path, dpi=300, transparent=False)
        logger.info('Saved.')
        plt.close()
        
        return output_path


    
    def _process(self):
        self.mb250=bool(self.mb250 or self.all)
        self.mb500=bool(self.mb500 or self.all)
        self.mb700=bool(self.mb700 or self.all)
        self.mb850=bool(self.mb850 or self.all)
        self.avg=bool(self.avg or self.all)
        self.ani=bool(self.ani or self.all)
        self.sv_file(
            wind=True,
            avg=self.avg,
            mb250=self.mb250,
            mb500=self.mb500,
            mb700=self.mb700,
            mb850=self.mb850)
    
    def _create_charts(self):
        self.logger.debug(f'Generating charts with conditions:\n\t{self.mb250=}\n\t{self.mb500=}\n\t{self.mb700=}\n\t{self.mb850=}')
        _desired_charts=[
            dict(strata=ChartStrataType.MB250, 
                variable=ChartVariableType.WIND, 
                measurement=ChartMeasurementType.ANIMATION),
            dict(strata=ChartStrataType.MB500, 
                variable=ChartVariableType.WIND, 
                measurement=ChartMeasurementType.ANIMATION),
            dict(strata=ChartStrataType.MB700, 
                variable=ChartVariableType.WIND, 
                measurement=ChartMeasurementType.ANIMATION),
            dict(strata=ChartStrataType.MB850, 
                variable=ChartVariableType.WIND, 
                measurement=ChartMeasurementType.ANIMATION),
            dict(strata=ChartStrataType.MB250, 
                variable=ChartVariableType.WIND, 
                measurement=ChartMeasurementType.AVERAGE),
            dict(strata=ChartStrataType.MB500, 
                variable=ChartVariableType.WIND, 
                measurement=ChartMeasurementType.AVERAGE),
            dict(strata=ChartStrataType.MB700, 
                variable=ChartVariableType.WIND, 
                measurement=ChartMeasurementType.AVERAGE),
            dict(strata=ChartStrataType.MB850, 
                variable=ChartVariableType.WIND, 
                measurement=ChartMeasurementType.AVERAGE),
                ]
        return [self.create_chart(**dd) for dd in _desired_charts]

    def __call__(self, *args, **kwargs):
        self._process()
        self.output_paths=self._create_charts()
        return self


class ZHandler(MapHandler):
    def create_chart(self, strata=ChartStrataType.MB700, variable=ChartVariableType.Z, measurement=ChartMeasurementType.ANIMATION):

        conditions=[]
        conditions.append(self.__getattr__(strata.name.lower()))

        data_range=self.sv_file.data_range
        self.logger.debug(f'Checking conditions for {data_range.name} {strata.name} {variable.name} {measurement.name}\n\t{conditions=}')
        if not(conditions and all(conditions)):
            self.logger.info(f'Conditions for {data_range.name} {strata.name} {variable.name} {measurement.name} Plot are not met, skipping.')
            return
        
        # Create a 3d plot with x, y limits the icon-eu maximum/minimum coordinates
        # z limit results from the new variable possible values, see line 102
        plt.figure(figsize=(30, 15))

        ax = plt.axes(projection="3d", xlim=[-122.5,-119], ylim=[45.5, 47.9], zlim=[0, 350])
        target_projection = ccrs.PlateCarree()

        feature = cartopy.feature.NaturalEarthFeature("physical", "coastline", "50m")
        geoms = feature.geometries()

        geoms = [target_projection.project_geometry(geom, feature.crs)
                for geom in geoms]

        paths = list(itertools.chain.from_iterable(geos_to_path(geom) for geom in geoms))
        segments = []
        for path in paths:
            vertices = [vertex for vertex, _ in path.iter_segments()]
            vertices = np.asarray(vertices)
            segments.append(vertices)

        lc = LineCollection(segments, color="black", zorder=0)
        resolution=2
        Z=self.sv_file.data_ensemble[strata.name.lower()]['z'][0, ::resolution, ::resolution]
        date_time=datetime.datetime.utcfromtimestamp( int((self.sv_file.data.Time[0] - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's')) )
        gh=Z
        lons=self.dom_file.lon[::resolution, ::resolution]
        lats=self.dom_file.lat[::resolution, ::resolution]

        ax.add_collection3d(lc)
        gh_3d = Z/100
        gh_3d = np.exp(gh_3d)
        x = lons
        y = lats

        x2 = np.append(0, x.flatten())
        y2 = np.append(0, y.flatten())

        x2, y2 = np.meshgrid(lons, lats)
        gh_3d_np=gh_3d.to_numpy()
        self.logger.info(f'{gh_3d_np=}')
        self.logger.info(f'{dir(gh_3d_np)}')
        z2 = np.append(0, gh_3d_np.flatten())
        z2 = np.delete(z2, 0)

        max_z2 = max(z2)
        # self.logger.info(f'{z2=}')
        # self.logger.info(f'{z2[30243]=}')
        surf = ax.plot_trisurf(x2.flatten(), y2.flatten(), z2, cmap=cm.nipy_spectral, linewidth=0.1, vmin=min(z2), vmax=max_z2, alpha=0.6, antialiased=False)

        min_gh = 1000
        for i in range(len(gh)):
            for j in range(len(gh[i])):
                if gh[i][j] < min_gh:
                    min_gh = gh[i][j]

        max_gh = 0
        for i in range(len(gh)):
            for j in range(len(gh[i])):
                if gh[i][j] > max_gh:
                    max_gh = gh[i][j]
        
        levels_contourf = np.linspace(min_gh, max_gh, 1000)
        levels_contour = np.linspace(min_gh, max_gh, 25)

        ax.contourf(x2, y2, gh, levels_contourf, zdir="z", offset=0, cmap="nipy_spectral", alpha=0.4, zorder=10, antialiased=False)
        ax.contour(x2, y2, gh, levels_contour, zdir="z", offset=0, colors="black", linewidths=2, zorder=100)

        cbar = plt.colorbar(mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(vmin=min_gh, vmax=max_gh), cmap="nipy_spectral"), shrink=0.5, aspect=5, pad=0.0001)
        cbar.ax.tick_params(labelsize=20) 
        cbar.ax.locator_params(nbins=10)
        cbar.set_label(label=f"Geopotential Height ({strata.name})", fontsize=20)
        ax.view_init(25, 270)

        # Titles, subtitles and further labels
        ax.set(xlabel="Longitude", ylabel="Latitude", zlabel="Height (exp(gpdm/1000))")
        plt.title(f"Geopotential Height ({strata.name.lower()})\n{date_time} UTC", y=0.93, fontsize=20)
        output_dir=os.path.abspath('.')
        output_file=f"RZ_{data_range.name}_{strata.name}_{variable.name}_{measurement.name}.png"
        output_path=os.path.join(output_dir, output_file)
        
        logger.info(f'Saving Plot to "{output_path}"...')
        plt.savefig(output_path, dpi=300, transparent=False)
        logger.info('Saved.')
        plt.close()
        
        return output_path




    
    def _process(self):
        self.mb250=bool(self.mb250 or self.all)
        self.mb500=bool(self.mb500 or self.all)
        self.mb700=bool(self.mb700 or self.all)
        self.mb850=bool(self.mb850 or self.all)
        self.sv_file(
            wind=True,
            mb250=self.mb250,
            mb500=self.mb500,
            mb700=self.mb700,
            mb850=self.mb850)
    
    def _create_charts(self):
        self.logger.debug(f'Generating charts with conditions:\n\t{self.mb250=}\n\t{self.mb500=}\n\t{self.mb700=}\n\t{self.mb850=}')
        _desired_charts=[
            dict(strata=ChartStrataType.MB250, 
                variable=ChartVariableType.Z, 
                measurement=ChartMeasurementType.ANIMATION),
            dict(strata=ChartStrataType.MB500, 
                variable=ChartVariableType.Z, 
                measurement=ChartMeasurementType.ANIMATION),
            dict(strata=ChartStrataType.MB700, 
                variable=ChartVariableType.Z, 
                measurement=ChartMeasurementType.ANIMATION),
            dict(strata=ChartStrataType.MB850, 
                variable=ChartVariableType.Z, 
                measurement=ChartMeasurementType.ANIMATION)]
        return [self.create_chart(**dd) for dd in _desired_charts]

    def __call__(self, *args, **kwargs):
        self._process()
        self.output_paths=self._create_charts()
        return self
    

class LwcHandler(MapHandler):
    def create_chart(self, lat_index=None, lat=None):
        self.logger.info(f'Creating LWC Cross-Section for {lat}')
        data_range=self.sv_file.data_range
        
        gs_lwc = self.sv_file.data_ensemble['ground']['average']['lwc']
        as_lwc = self.sv_file.data_ensemble['air']['average']['lwc']
        height=self.dom_file.height[0]

        _lwcg  =  gs_lwc[lat_index, :]
        _lwca =  as_lwc[lat_index, :]
        _lon  =  self.dom_file.lon[lat_index, :]
        _hgt  =  height[lat_index, :]
        

        fig, ax1 = plt.subplots()
        fig.set_size_inches(18.5, 10.5)

        ax1.plot(_lon, _hgt, color='tab:brown')#, label='Terrain')

        ax1.fill_between(_lon, _hgt, 0, alpha=0.3, color='tab:brown')
        ax1.set_xlabel(r'$Longitude\ \degree W$', fontsize=20)
        ax1.set_ylabel(r'$Altitude\ \left(\ meters\ \right)$', fontsize=20)
        ax1.grid(True)
        ax1.tick_params(size=1, labelsize=18)
        # ax1.tick_params('y', colors='b')

        ax2 = ax1.twinx()
        ax2.plot(_lon, _lwca, label='LWC Air', color='b')
        # ax2.plot(_lon, _lwc2, label=r'$LWC\ @\ HGT\ \leq \ 2100m$', color='b')
        ax2.plot(_lon, _lwcg, label='LWC Ground', color='g')

        # ax2.stackplot(_lon, _lwc2, _lwca)#, baseline='weighted_wiggle')

        # print(f'{_lwc1=}')
        # print(f'{_lwc2=}')
        # ax2.plot([0,1e-5], [0,1e-5], color='tab:brown', label='Terrain')
        ax2.set_ylabel(r'$LWC\ \left(\frac{g}{kg}\right)$', fontsize=20)
        ax2.grid(False)
        ax2.tick_params(size=1, labelsize=18)
        # ax2.tick_params('y', colors='r')
        # ax2.set_ylim(-0.06, 0.06)

        # plt.title(r'$Vertical Cross-Section \newline LWC and Terrain\newline \right(\ Latitude \ 47.5 \degree\ N\ \right)$')
        title_range = 'Nov - Apr' if data_range in [ChartRangeType.SEASON] else data_range.name.capitalize()
        lat_name = f'{lat}'.replace('.','_')
        _prefix=f'Vertical Cross-Section\nLWC and Terrain ( {title_range} )\n'
        _tex=r'$\left(\ Latitude \  ' + f'{lat}' + r' \degree \ N\right)$'
        plt.title(f'{_prefix}{_tex}', fontsize=26)

        plt.legend(fontsize=18)
        # plt.xlim(-121.6, -120.9)#-120.9)
        fig.patch.set_facecolor('white')
        # plt.show()

        # Titles, subtitles and further labels
        output_dir=os.path.abspath('.')
        output_file=f"RZ_{data_range.name}_LWC_XSECTION_{lat_name}.png"
        output_path=os.path.join(output_dir, output_file)
        
        logger.info(f'Saving Plot to "{output_path}"...')
        plt.savefig(output_path, dpi=300, transparent=False)
        logger.info('Saved.')
        plt.close()
        
        return output_path

    
    def _process(self):
        self.sv_file(air=True,gnd=True,frq=False,avg=True,lwc=True,tmp=False)
        # self.all=True
        # self.air=bool(self.air or self.all)
        # self.gnd=bool(self.gnd or self.all)
        # self.frq=bool(self.frq or self.all)
        # self.avg=bool(self.avg or self.all)
        # self.lwc=bool(self.lwc or self.all)
        # self.tmp=bool(self.tmp or self.all)
        # self.sv_file(air=self.air,gnd=self.gnd,frq=self.frq,avg=self.avg,lwc=self.lwc,tmp=self.tmp)
    
    def _create_charts(self):
        _desired_charts=[
            dict(lat_index=70, lat=47.5),
            dict(lat_index=60, lat=46.8),
            dict(lat_index=50, lat=46.5)]
        return [self.create_chart(**dd) for dd in _desired_charts]

    def __call__(self, *args, **kwargs):
        self._process()
        self.output_paths=self._create_charts()
        return self
    
@click.group()
@click.option('--debug/--no-debug', default=False)
@click.option('--sv-file',      help="Seed Variable NC File to use", show_default=True, default='/glade/derecho/scratch/meghan/Roza/data/CONUS404/cat/SV_Season.nc')
@click.option('--dom-file',     help="Domain NC File to use", show_default=True, default='/glade/derecho/scratch/meghan/Roza/data/CONUS404/cut/wrfconstants_usgs404_roza.nc')
@click.option('--shp-file',     help="Shapefile(s) to add to maps", show_default=True, default='/glade/derecho/scratch/meghan/Roza/roza/data/shapefiles/RozaBasin.shp')
@click.pass_context
def cli(ctx, *args, **kwargs):
    _fname=inspect.currentframe().f_code.co_name
    opts = SmartDict({kk:None if vv in [tuple(), None] else vv for kk,vv in kwargs.items() }, dict())
    ctx.obj=DotMap()
    ctx.obj(**opts)
    logging.getLogger(_fname).debug(f"{kwargs=}")
    logging.getLogger(_fname).debug(f"{opts=}")
    logging.getLogger(_fname).debug(f"Debug mode is {'on' if opts.debug else 'off'}")

@cli.command()
@click.option('--air/--no-air', is_flag=True, show_default=True, default=False, help="Create AIR Plots")
@click.option('--gnd/--no-gnd', is_flag=True, show_default=True, default=False, help="Create GROUND Plots")
@click.option('--tmp/--no-tmp', is_flag=True, show_default=True, default=False, help="Create TEMP Plots")
@click.option('--lwc/--no-lwc', is_flag=True, show_default=True, default=False, help="Create LWC Plots")
@click.option('--frq/--no-frq', is_flag=True, show_default=True, default=False, help="Create FREQUENCY Plots")
@click.option('--avg/--no-avg', is_flag=True, show_default=True, default=False, help="Create AVERAGE Plots")
@click.option('--all',          is_flag=True, show_default=True, default=False, help="Create ALL THE EFFIN Plots")
@click.option('-m','--model',   default=None, help="The data model (e.g., 'PGW' or 'CONUS404 Current Climate')")
@click.pass_context
def cool(ctx, *args, **kwargs):
    _fname=inspect.currentframe().f_code.co_name
    opts=SmartDict(**{kk:None if vv in [tuple(), None] else vv for kk,vv in kwargs.items() }, **dict(context=ctx.obj))
    logging.getLogger(_fname).debug(f"{kwargs=}")
    logging.getLogger(_fname).debug(f"{opts=}")
    ch=CoolHandler(**opts)
    ch()

@cli.command()
@click.option('--air/--no-air', is_flag=True, show_default=True, default=False, help="Create AIR Plots")
@click.option('--gnd/--no-gnd', is_flag=True, show_default=True, default=False, help="Create GROUND Plots")
@click.option('--tmp/--no-tmp', is_flag=True, show_default=True, default=False, help="Create TEMP Plots")
@click.option('--lwc/--no-lwc', is_flag=True, show_default=True, default=False, help="Create LWC Plots")
@click.option('--frq/--no-frq', is_flag=True, show_default=True, default=False, help="Create FREQUENCY Plots")
@click.option('--avg/--no-avg', is_flag=True, show_default=True, default=False, help="Create AVERAGE Plots")
@click.option('--all',          is_flag=True, show_default=True, default=False, help="Create ALL THE EFFIN Plots")
@click.option('-m','--model',   default=None, help="The data model (e.g., 'PGW' or 'CONUS404 Current Climate')")
@click.pass_context
def cache(ctx, *args, **kwargs):
    _fname=inspect.currentframe().f_code.co_name
    opts=SmartDict(**{kk:None if vv in [tuple(), None] else vv for kk,vv in kwargs.items() }, **dict(context=ctx.obj))
    logging.getLogger(_fname).debug(f"{kwargs=}")
    logging.getLogger(_fname).debug(f"{opts=}")
    ch=CacheHandler(**opts)
    ch()

@cli.command()
@click.pass_context
def lwc(ctx, *args, **kwargs):
    _fname=inspect.currentframe().f_code.co_name
    opts=SmartDict(**{kk:None if vv in [tuple(), None] else vv for kk,vv in kwargs.items() }, **dict(context=ctx.obj))
    logging.getLogger(_fname).debug(f"{kwargs=}")
    logging.getLogger(_fname).debug(f"{opts=}")
    ch=LwcHandler(**opts)
    ch()

@cli.command()
@click.option('--mb250/--no-mb250', is_flag=True, show_default=True, default=False, help="U 250MB Data")
@click.option('--mb500/--no-mb500', is_flag=True, show_default=True, default=False, help="Use 500MB Data")
@click.option('--mb700/--no-mb700', is_flag=True, show_default=True, default=False, help="Use 700MB Data")
@click.option('--mb850/--no-mb850', is_flag=True, show_default=True, default=False, help="Use 850MB Data")
@click.option('--avg/--no-avg', is_flag=True, show_default=True, default=False, help="Static Averaged Plot")
@click.option('--ani/--no-ani', is_flag=True, show_default=True, default=False, help="Dynamic Super Awesome Animated Plot")
@click.option('--gif/--no-gif', is_flag=True, show_default=True, default=False, help="Output animated gif")
@click.option('--mov/--no-mov', is_flag=True, show_default=True, default=False, help="Output video (mp4)")
@click.option('--all',          is_flag=True, show_default=True, default=False, help="Create ALL THE EFFIN Plots")
@click.pass_context
def wind(ctx, *args, **kwargs):
    _fname=inspect.currentframe().f_code.co_name
    opts=SmartDict(**{kk:None if vv in [tuple(), None] else vv for kk,vv in kwargs.items() }, **dict(context=ctx.obj))
    logging.getLogger(_fname).debug(f"{kwargs=}")
    logging.getLogger(_fname).debug(f"{opts=}")
    ch=WindHandler(**opts)
    ch()

@cli.command()
@click.option('--mb250/--no-mb250', is_flag=True, show_default=True, default=False, help="U 250MB Data")
@click.option('--mb500/--no-mb500', is_flag=True, show_default=True, default=False, help="Use 500MB Data")
@click.option('--mb700/--no-mb700', is_flag=True, show_default=True, default=False, help="Use 700MB Data")
@click.option('--mb850/--no-mb850', is_flag=True, show_default=True, default=False, help="Use 850MB Data")
@click.option('--all',          is_flag=True, show_default=True, default=False, help="Create ALL THE EFFIN Plots")
@click.pass_context
def geop(ctx, *args, **kwargs):
    _fname=inspect.currentframe().f_code.co_name
    opts=SmartDict(**{kk:None if vv in [tuple(), None] else vv for kk,vv in kwargs.items() }, **dict(context=ctx.obj))
    logging.getLogger(_fname).debug(f"{kwargs=}")
    logging.getLogger(_fname).debug(f"{opts=}")
    ch=ZHandler(**opts)
    ch()


if __name__ == "__main__":
    cli()



def animate_wind(ds_3d=None, domain=None, scope=None, **kwargs):
    # Plot Wind Contours

    lat = domain.variables['XLAT'][:]
    lon = domain.variables['XLONG'][:]
    hgt = domain.variables['HGT'][:]
    
    uwind = ds_3d.U_500MB
    vwind = ds_3d.V_500MB

    wspd = np.sqrt(uwind**2+vwind**2)
    wdir = np.arctan2(uwind.values,vwind.values)*180/math.pi+180

    def get_data(ii):
        return wspd[ii], uwind[ii], vwind[ii]
    
    z, u, v = get_data(0)

    data_limits=(math.ceil(wspd.min())-1, math.ceil(wspd.max()))
    data_buff=int((max(data_limits)-min(data_limits))/10)
    stagger=5 if scope == FigureScope.LOCAL else 20
    qscale=500 if scope == FigureScope.LOCAL else 4500
    date_time=datetime.datetime.utcfromtimestamp( int((ds_3d.Time[0] - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's')) )
    start=date_time
    end=datetime.datetime.utcfromtimestamp( int((ds_3d.Time[-1] - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's')) )
    if scope == FigureScope.LOCAL:
        fig = plt.figure(figsize=(7.5, 4))
    else:
        fig = plt.figure(figsize=(12, 4))
    ax = plt.axes(projection=ccrs.PlateCarree())
    if scope == FigureScope.LOCAL:
        ax.set_extent((-109.5,-101.8, 36.5, 41.5), crs=ccrs.PlateCarree())
    else:
        ax.set_extent((-130, -65, 25, 50), crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.STATES)
    if scope == FigureScope.LOCAL:
        scope_name=scope.name.capitalize()
    else:
        scope_name=scope.name
    title=ax.set_title(f"{date_time:%Y} Colorado Snowstorm - {scope_name} Wind Contours {date_time:%B} {date_time:%d} {date_time:%H}:{date_time:%M}:{date_time:%S} ", fontsize=14)

    cont=[plt.contourf(
        to_np(lon),
        to_np(lat),
        z, 
        levels=np.linspace(min(data_limits), max(data_limits), 21),
        cmap='YlGnBu',
        zorder=7,
        alpha = 0.6)]
    _topo = plt.contour(
        to_np(lon),
        to_np(lat),
        hgt[0],
        alpha = 0.4,
        linewidths=0.3,
        zorder=3,
        cmap ='gray',
        levels = 100)
    _cbar = plt.colorbar(
        cont[0],
        label='Wind Speed (m/s)',
        orientation="vertical",
        ticks=np.arange(min(data_limits), max(data_limits)+data_buff, data_buff  ),
        drawedges=True,
        extendrect=True,
        shrink=0.9)

    _q=plt.quiver(
        to_np(lon)[::stagger, ::stagger], 
        to_np(lat)[::stagger, ::stagger], 
        u[::stagger, ::stagger], 
        v[::stagger, ::stagger], 
        scale=qscale, 
        zorder=4,
        alpha=0.7,
        animated=True
    )

    if scope == FigureScope.CONUS:
        plt.quiverkey(_q, 0.8, 0.9, 30, r'$30 \frac{m}{s}$', labelpos='E', coordinates='figure')
    else:
        plt.quiverkey(_q, 0.853, 0.9, 10, r'$5 \frac{m}{s}$', labelpos='E', coordinates='figure')

    _cbar.ax.tick_params(size=1, labelsize=10)
    _cbar.set_label('Wind Speed',fontsize = 12)
    _gl = ax.gridlines(
        crs=ccrs.PlateCarree(),
        draw_labels=True,
        dms=False,
        x_inline=False,
        y_inline=False,
        linewidth=1,
        color="k",
        alpha=0.25,
        zorder=4)
    _gl.top_labels = False
    _gl.right_labels = False
    _gl.xlabel_style = {"rotation": 45, "size": 10}
    _gl.ylabel_style = {"rotation": 0, "size": 10}
    _gl.xlines = True
    _gl.ylines = True


    plt.plot(*Denver, 'ko', markersize=3, zorder=4)
    plt.text(*Denver, ' Denver', fontsize=8, zorder=4)

    def animate(ii):
        date_time=datetime.datetime.utcfromtimestamp( int((ds_3d.Time[ii] - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's')) )
        _=[c.remove() for c in cont[0].collections]
        z, u, v = get_data(ii)
        cont[0] = ax.contourf(to_np(lon), to_np(lat), z, cmap='YlGnBu', zorder=4 ,alpha = 0.8)
        _q.set_UVC(u[::stagger, ::stagger], v[::stagger, ::stagger])
        title.set_text(f"{date_time:%Y} Colorado Snowstorm - {scope_name} Wind Contours {date_time:%B} {date_time:%d} {date_time:%H}:{date_time:%M}:{date_time:%S} ")
        return cont[0].collections+[title, _q]

    # ani = FuncAnimation(fig, animate, frames=len(ds_3d.Time), interval=50, blit=True, repeat=True)
    ani = FuncAnimation(fig, animate, frames=len(ds_3d.Time), blit=True, repeat=True)
    plt.show()
    ani.save(f'WIND_{scope.name}_{start:%m}{start:%d}{start:%H}_{end:%m}{end:%d}{end:%H}.gif')


    # python bin/create_maps.py --dom-file data/wrfconstants_usgs404_roza.nc cache --all