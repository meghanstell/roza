
import numpy as np
import os
import xarray as xr
from rich.logging import RichHandler
from rich.traceback import install
from rich.console import Console
from rich.syntax import Syntax
from rich.table import (Column, Table)
import rich_click as click
from collections import namedtuple
import logging


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

outpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'masks'))

LonLat = namedtuple('LatLon', ['x','y'])

generators={
    "A1":LonLat(-121.71, 47.40),
    "A2":LonLat(-121.67, 47.45),
    "A3":LonLat(-121.80, 47.34),
    "A4":LonLat(-121.75, 47.46),
    "A5":LonLat(-121.83, 47.40),
    "A6":LonLat(-121.60, 47.49),
    "E1":LonLat(-121.40, 47.22),
    "E2":LonLat(-121.43, 47.17),
    "E3":LonLat(-121.48, 47.21),
    "E4":LonLat(-121.30, 47.21),
    "E5":LonLat(-121.20, 47.16),
    "E6":LonLat(-121.10, 47.15),
    "E7":LonLat(-121.25, 47.20),
    # "IndianRock": LonLat(y=45.99,x=-120.81),
    # "SatusPass": LonLat(y=45.99,x=-120.68),
    # "SurpriseLakes": LonLat(y=46.09,x=-121.76),
    # "PepperCreek": LonLat(y=46.1, x=-121.96),
    # "SpencerMeadow": LonLat(y=46.18,x=-121.93),
    # "LonePine": LonLat(y=46.27,x=-121.96),
    # "PintoRock": LonLat(y=46.32,x=-121.94),
    # "PotatoHill": LonLat(y=46.35,x=-121.51),
    # "LostHorse": LonLat(y=46.36,x=-121.08),
    # "GreenLake": LonLat(y=46.55,x=-121.17),
    # "PigtailPeak": LonLat(y=46.62,x=-121.39),
    # "SkateCreek": LonLat(y=46.64,x=-121.83),
    # "WhitePassES": LonLat(y=46.64,x=-121.38),
    # "Paradise": LonLat(y=46.78,x=-121.75),
    # "BumpingRidge": LonLat(y=46.81,x=-121.33),
    # "CayusePass": LonLat(y=46.87,x=-121.53),
    # "MorseLake": LonLat(y=46.91,x=-121.48),
    # "Mowich": LonLat(y=46.93,x=-121.95),
    # "CorralPass": LonLat(y=47.02,x=-121.46),
    # "BurntMountain": LonLat(y=47.04,x=-121.94),
    # "HuckleberryCreek": LonLat(y=47.07,x=-121.59),
    # "SawmillRidge": LonLat(y=47.16,x=-121.42),
    # "LynnLake": LonLat(y=47.2, x=-121.78),
    # "Trough": LonLat(y=47.23,x=-120.29),
    # "StampedePass": LonLat(y=47.27,x=-121.34),
    # "CougarMountain": LonLat(y=47.28,x=-121.67),
    # "GrouseCamp": LonLat(y=47.28,x=-120.49),
    # "MeadowsPass": LonLat(y=47.28,x=-121.47),
    # "UpperWheeler": LonLat(y=47.29,x=-120.37),
    # "RexRiver": LonLat(y=47.3, x=-121.6),
    # "TinkhamCreek": LonLat(y=47.33,x=-121.47),
    # "BlewettPass": LonLat(y=47.35,x=-120.68),
    # "MountGardner": LonLat(y=47.36,x=-121.57),
    # "OlallieMeadows": LonLat(y=47.37,x=-121.44),
    # "SasseRidge": LonLat(y=47.38,x=-121.06),
    # "FishLake": LonLat(y=47.54,x=-121.09),
    # "PotatoHill":LonLat(y=46.35, x=-121.51),
    # "SkateCreek":LonLat(y=46.64, x=-121.83),
}
# _sv_file='/glade/derecho/scratch/meghan/Roza/data/CONUS404/cat/SV_Season.nc'
# _sv_file='/glade/work/meghan/Lemhi/CONUS404/data/CONUS404_Data/Seeding_Variables/Montana/average/SV_Season_avg.nc'

_logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])

# _logger.info(f'Loading {_sv_file}')
# sv_data = xr.open_dataset(_sv_file)
# sv_data=sv_data.squeeze()
# _logger.info('Done.')

# _domain_file='/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/wrfconstants_usgs404_roza.nc'

_domain_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'ncfiles', 'domain'))
_domain_file='wrfconstants_usgs404_roza.nc'
_domain_path=os.path.join(_domain_dir, _domain_file)

_logger.info(f'Loading {_domain_path}')
domain_data=xr.open_dataset(_domain_path)
domain_data=domain_data.squeeze()
_logger.info('Done.')

for gen_name, llo in generators.items():
    outfile = os.path.join(outpath, "{}.nc".format(gen_name))
    alat=llo.y
    alon=llo.x
    _logger.info(f'{alat=}, {alon=}, {outfile=}')

    abslat  = np.abs(domain_data.XLAT-alat)
    abslon  = np.abs(domain_data.XLONG-alon)
    c       = np.maximum(abslon,abslat)
    ([xloc],[yloc]) = np.where(c == np.min(c))
    _logger.info(f'{[xloc]=},{[yloc]=}')

    maskzero = np.zeros((domain_data.sizes['south_north'],domain_data.sizes['west_east']))
    maskzero[xloc,yloc] = 1

    _logger.info('Building Dataset')
    mask = xr.Dataset(data_vars = dict(
            mask=(["south_north","west_east"],maskzero),
            # AS_LWC=(["south_north","west_east"],maskzero*sv_data.AS_LWC.values),
            # AS_Tc=(["south_north","west_east"],maskzero*sv_data.AS_Tc.values),
            # AS_U=(["south_north","west_east"],maskzero*sv_data.AS_U.values),
            # AS_V=(["south_north","west_east"],maskzero*sv_data.AS_V.values),
            # GS_LWC=(["south_north","west_east"],maskzero*sv_data.GS_LWC.values),
            # GS_Tc=(["south_north","west_east"],maskzero*sv_data.GS_Tc.values),
            # GS_U=(["south_north","west_east"],maskzero*sv_data.GS_U.values),
            # GS_V=(["south_north","west_east"],maskzero*sv_data.GS_V.values),
            # Tc_250MB=(["south_north","west_east"],maskzero*sv_data.Tc_250MB.values),
            # U_250MB=(["south_north","west_east"],maskzero*sv_data.U_250MB.values),
            # V_250MB=(["south_north","west_east"],maskzero*sv_data.V_250MB.values),
            # Z_250MB=(["south_north","west_east"],maskzero*sv_data.Z_250MB.values),
            # Tc_500MB=(["south_north","west_east"],maskzero*sv_data.Tc_500MB.values),
            # U_500MB=(["south_north","west_east"],maskzero*sv_data.U_500MB.values),
            # V_500MB=(["south_north","west_east"],maskzero*sv_data.V_500MB.values),
            # Z_500MB=(["south_north","west_east"],maskzero*sv_data.Z_500MB.values),
            # Tc_700MB=(["south_north","west_east"],maskzero*sv_data.Tc_700MB.values),
            # U_700MB=(["south_north","west_east"],maskzero*sv_data.U_700MB.values),
            # V_700MB=(["south_north","west_east"],maskzero*sv_data.V_700MB.values),
            # Z_700MB=(["south_north","west_east"],maskzero*sv_data.Z_700MB.values),
            # Tc_850MB=(["south_north","west_east"],maskzero*sv_data.Tc_850MB.values),
            # U_850MB=(["south_north","west_east"],maskzero*sv_data.U_850MB.values),
            # V_850MB=(["south_north","west_east"],maskzero*sv_data.V_850MB.values),
            # Z_850MB=(["south_north","west_east"],maskzero*sv_data.Z_850MB.values),
            HGT=(["south_north","west_east"],maskzero*domain_data.HGT.values),
        ),
        coords = dict(
            XLONG = (["south_north","west_east"],domain_data.XLONG.values),
            XLAT  = (["south_north","west_east"],domain_data.XLAT.values),
        ),
    )
    _logger.info(f'{outfile=}')
    mask.to_netcdf(outfile)
