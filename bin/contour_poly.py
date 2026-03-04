import numpy as np
from matplotlib.artist import Artist
from matplotlib.lines import Line2D
import netCDF4 as nc
import numpy as np 
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Pgon
from matplotlib.collections import PatchCollection
import numpy as np
import xarray as xr
import cartopy.crs as ccrs
import netCDF4 as nc
# from wrf import to_np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os
import pandas as pd
# import pygmt 
import shapefile
import geopandas as gpd
import geocat.viz as gv
from shapely.geometry import Point
from shapely.affinity import scale, rotate
from shapely.geometry.polygon import Polygon
import math
import distinctipy

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_data_dir=os.path.join(_root, 'data')
_shp_dir = os.path.join(_data_dir, 'shapefiles')
_shp_tst_dir = os.path.join(_shp_dir, 'test')

def dist_point_to_segment(p, s0, s1):
    """
    Get the distance from the point *p* to the segment (*s0*, *s1*), where
    *p*, *s0*, *s1* are ``[x, y]`` arrays.
    """
    s01 = s1 - s0
    s0p = p - s0
    if (s01 == 0).all():
        return np.hypot(*s0p)
    # Project onto segment, without going past segment ends.
    p1 = s0 + np.clip((s0p @ s01) / (s01 @ s01), 0, 1) * s01
    return np.hypot(*(p - p1))


class PolygonInteractor:
    """
    A polygon editor.

    Key-bindings

      't' toggle vertex markers on and off.  When vertex markers are on,
          you can move them, delete them

      'd' delete the vertex under point

      'i' insert a vertex at point.  You must be within epsilon of the
          line connecting two existing vertices

    """

    showverts = True
    epsilon = 5  # max pixel distance to count as a vertex hit

    def __init__(self, ax, poly, path=None):
        if poly.figure is None:
            raise RuntimeError('You must first add the polygon to a figure '
                               'or canvas before defining the interactor')
        self.ax = ax
        canvas = poly.figure.canvas
        self.poly = poly
        self.path=path

        x, y = zip(*self.poly.xy)
        self.line = Line2D(x, y, color='cyan',
                           marker='o', markerfacecolor='r',
                           animated=True)
        self.ax.add_line(self.line)

        self.cid = self.poly.add_callback(self.poly_changed)
        self._ind = None  # the active vert

        canvas.mpl_connect('draw_event', self.on_draw)
        canvas.mpl_connect('button_press_event', self.on_button_press)
        canvas.mpl_connect('key_press_event', self.on_key_press)
        canvas.mpl_connect('button_release_event', self.on_button_release)
        canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas = canvas

    def on_draw(self, event):
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.ax.draw_artist(self.poly)
        self.ax.draw_artist(self.line)
        # do not need to blit here, this will fire before the screen is
        # updated

    def poly_changed(self, poly):
        """This method is called whenever the pathpatch object is called."""
        # only copy the artist props to the line (except visibility)
        vis = self.line.get_visible()
        Artist.update_from(self.line, poly)
        self.line.set_visible(vis)  # don't use the poly visibility state

    def get_ind_under_point(self, event):
        """
        Return the index of the point closest to the event position or *None*
        if no point is within ``self.epsilon`` to the event position.
        """
        # display coords
        xy = np.asarray(self.poly.xy)
        xyt = self.poly.get_transform().transform(xy)
        xt, yt = xyt[:, 0], xyt[:, 1]
        d = np.hypot(xt - event.x, yt - event.y)
        indseq, = np.nonzero(d == d.min())
        ind = indseq[0]

        if d[ind] >= self.epsilon:
            ind = None

        return ind

    def on_button_press(self, event):
        """Callback for mouse button presses."""
        if not self.showverts:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        self._ind = self.get_ind_under_point(event)

    def on_button_release(self, event):
        """Callback for mouse button releases."""
        if not self.showverts:
            return
        if event.button != 1:
            return
        self._ind = None

    def on_key_press(self, event):
        """Callback for key presses."""
        if not event.inaxes:
            return
        if event.key == 't':
            self.showverts = not self.showverts
            self.line.set_visible(self.showverts)
            if not self.showverts:
                self._ind = None
                self.line.set_color('blue')
            else:
                self.line.set_color('cyan')

        elif event.key == 'd':
            ind = self.get_ind_under_point(event)
            if ind is not None:
                self.poly.xy = np.delete(self.poly.xy,
                                         ind, axis=0)
                self.line.set_data(zip(*self.poly.xy))
        elif event.key == 'i':
            xys = self.poly.get_transform().transform(self.poly.xy)
            p = event.x, event.y  # display coords
            for i in range(len(xys) - 1):
                s0 = xys[i]
                s1 = xys[i + 1]
                d = dist_point_to_segment(p, s0, s1)
                if d <= self.epsilon:
                    self.poly.xy = np.insert(
                        self.poly.xy, i+1,
                        [event.xdata, event.ydata],
                        axis=0)
                    self.line.set_data(zip(*self.poly.xy))
                    break
        elif event.key == 'e':
            print(self.poly.xy)
        elif event.key == 's':
            # self.to_shapefile()
            shapely_polygon = Polygon(self.poly.xy)
            gdf = gpd.GeoDataFrame(geometry=[shapely_polygon], crs=ccrs.PlateCarree())
            gdf.to_file(self.path)
            print(f'Data saved to: "{self.path}" ')
        if self.line.stale:
            self.canvas.draw_idle()

    # def to_shapefile(self):
    #     shapely_polygon = Polygon(self.poly.xy)
    #     gdf = gpd.GeoDataFrame(geometry=[shapely_polygon], crs=ccrs.PlateCarree())
    #     gdf.to_file(self.path)
    #     print(f'Data saved to: "{self.path}" ')

    def on_mouse_move(self, event):
        """Callback for mouse movements."""
        if not self.showverts:
            return
        if self._ind is None:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        x, y = event.xdata, event.ydata

        self.poly.xy[self._ind] = x, y
        if self._ind == 0:
            self.poly.xy[-1] = x, y
        elif self._ind == len(self.poly.xy) - 1:
            self.poly.xy[0] = x, y
        self.line.set_data(zip(*self.poly.xy))

        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.poly)
        self.ax.draw_artist(self.line)
        self.canvas.blit(self.ax.bbox)

def add_rivers_and_lakes(ax):
    def include_shape(bbox):
        extent = [-122.5, 45.5, -119, 47.9]  # [x_min, y_min, x_max, y_max]

        poly1 = Polygon([(extent[0], extent[1]), (extent[2], extent[1]), (extent[2], extent[3]), (extent[0], extent[3])])
        poly2 = Polygon([(bbox[0], bbox[1]), (bbox[2], bbox[1]), (bbox[2], bbox[3]), (bbox[0], bbox[3])])

        iou = poly1.intersection(poly2).area / poly1.union(poly2).area
        return bool(iou>0)

    river_sf = shapefile.Reader(os.path.join(_shp_dir, "rivers.shp"))
    river_shapes=river_sf.shapes()

    lake_sf = shapefile.Reader(os.path.join(_shp_dir, "lakes.shp"))
    lake_shapes=lake_sf.shapes()

    wws = river_shapes + lake_shapes

    map_shapes=[ss for ss in wws if include_shape(ss.bbox)]
    patches = []
    
    for shape in map_shapes:
        if shape.shapeTypeName in ['POLYGON']:

            # pgon = Pgon(shape.points, closed=False)
            pgon = Pgon(shape.points, fill=True, zorder=9, alpha=1)
            pgon.set_color('royalblue')
            patches.append(pgon)
            
            pgon.set(edgecolor='royalblue', facecolor='royalblue')
        else:
            # print(shape.shapeTypeName)
            # print(shape)
            # ax.scatter([pp[0] for pp in shape.points], [pp[1] for pp in shape.points], color='royalblue', marker='o', s=1)
            ax.plot([pp[0] for pp in shape.points], [pp[1] for pp in shape.points], color='royalblue', linewidth=2, alpha=1)

    p = PatchCollection(patches) #, alpha=0.4)
    ax.add_collection(p)

def add_snotels(ax):
    _snotels=[
        {"name":"BumpingRidge",     "id":375,  "lat":46.81, "lon":-121.33, "elv":4610},
        {"name":"CayusePass",       "id":1085, "lat":46.87, "lon":-121.53, "elv":5240},
        {"name":"BlewettPass",      "id":352,  "lat":47.35, "lon":-120.68, "elv":4240},
        {"name":"BurntMountain",    "id":942,  "lat":47.04, "lon":-121.94, "elv":4170},
        {"name":"CorralPass",       "id":418,  "lat":47.02, "lon":-121.46, "elv":5800},
        {"name":"CougarMountain",   "id":420,  "lat":47.28, "lon":-121.67, "elv":3200},
        {"name":"FishLake",         "id":478,  "lat":47.54, "lon":-121.09, "elv":3430},
        {"name":"GrouseCamp",       "id":507,  "lat":47.28, "lon":-120.49, "elv":5390},
        {"name":"MeadowsPass",      "id":897,  "lat":47.28, "lon":-121.47, "elv":3230},
        {"name":"SasseRidge",       "id":734,  "lat":47.38, "lon":-121.06, "elv":4340},
    ]
    colors = distinctipy.get_colors(len(_snotels))
    _=[ax.scatter(_snotel.get('lon'), _snotel.get('lat'), label=_snotel.get('name'), edgecolors='k', s=100, zorder=10, color=colors[ii]) for ii,_snotel in enumerate(_snotels)]
    



if __name__ == '__main__':
    RozaFullBasin=gpd.read_file(os.path.join(_shp_dir,'RozaFullBasin','RozaFullBasin.shp'))
    RozaSubBasin01=gpd.read_file(os.path.join(_shp_dir,'RozaSubBasin01','RozaSubBasin01.shp'))
    RozaSubBasin02=gpd.read_file(os.path.join(_shp_dir,'RozaSubBasin02','RozaSubBasin02.shp'))
    RozaSubBasin03=gpd.read_file(os.path.join(_shp_dir,'RozaSubBasin03','RozaSubBasin03.shp'))
    dom_data=nc.Dataset(os.path.join(_data_dir, 'ncfiles','domain', 'wrfconstants_usgs404_roza.nc'))
    lat=dom_data.variables['XLAT'][:]
    lon=dom_data.variables['XLONG'][:]
    height=dom_data.variables['HGT'][:]

    data_max=max([max(xx[np.isfinite(xx)]) for tt in height[0] for xx in tt])
    data_min=min([min(xx[np.isfinite(xx)]) for tt in height[0] for xx in tt])

    data_limits=(math.ceil(data_min)-1, math.ceil(data_max))
    data_buff=int((max(data_limits)-min(data_limits))/10)

    fig = plt.figure(figsize=(18.5, 10.5))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent((-122.5,-119, 45.5, 47.9), crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.STATES)

    _topo = plt.contour(
        lon,
        lat,
        height[0], 
        alpha = 1,
        linewidths=0.3,
        zorder=9,
        cmap ='gray',
        levels = 50)

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

    ax.plot(RozaSubBasin01.Lon.to_list(), RozaSubBasin01.Lat.to_list(), linewidth=1, color='magenta')
    ax.plot(RozaSubBasin02.Lon.to_list(), RozaSubBasin02.Lat.to_list(), linewidth=1, color='magenta')
    ax.plot(RozaSubBasin02.Lon.to_list(), RozaSubBasin02.Lat.to_list(), linewidth=1, color='magenta')
    ax.plot(RozaFullBasin.Lon.to_list(), RozaFullBasin.Lat.to_list(), linewidth=2, color='magenta')

    add_rivers_and_lakes(ax)
    add_snotels(ax)
    title_detail=f'Domain Topography and Basins'
    title=f'Yakima River Basin Windrose and CFAD Locations\n{title_detail}'

    gv.set_titles_and_labels(ax,maintitle=title,maintitlefontsize=22)
    # self.shp_file.plot(ax=ax, alpha = 1, color = 'black',label = 'Yakima_Basin')
    # ax.legend(loc='upper left', bbox_to_anchor=[1.7, 1])
    ax.legend(loc='center right',bbox_to_anchor=(1.35, 0.5))
    fig.patch.set_facecolor('white')
    _regions = [
        ('Region_Ground_A',True),
        ('Region_Ground_B',False),
        ('Region_Ground_C',False),
        ('Region_Ground_D',False),
        ('Region_Ground_E',False),
        ('Region_Ground_F',False),
        ]
    # patches=[]

    for _region, _modify in _regions:
        _fpath=os.path.join(_shp_tst_dir, _region, f"{_region}.shp")
        gdf = gpd.read_file(_fpath)
        gdf.plot(
            ax=ax,
            legend=True,
            linewidth=2,
            facecolor='none',
            # alpha=0.7,
            # facecolor=color,
            edgecolor='k',
            label=_region,
            # hatch=hatch
            )
        # xy_df = gdf['geometry'].get_coordinates()
        # xs=xy_df.x.to_numpy()
        # ys=xy_df.y.to_numpy()
        # poly = Pgon(np.column_stack([xs, ys]), animated=True, alpha=0.1)
        # poly.set_facecolor('none')
        # patches.append(poly)
        # fig, ax = plt.subplots()
        # ax.add_patch(poly)
    # p = PatchCollection(patches) #, alpha=0.4)
    # ax.add_collection(p)
    for _region, _modify in _regions:
        _fpath=os.path.join(_shp_tst_dir, _region, f"{_region}.shp")
        gdf = gpd.read_file(_fpath)
        xy_df = gdf['geometry'].get_coordinates()
        xs=xy_df.x.to_numpy()
        ys=xy_df.y.to_numpy()
        poly = Pgon(np.column_stack([xs, ys]), animated=True, alpha=0.1)
        # patches.append(poly)
        # fig, ax = plt.subplots()
        # ax.add_patch(poly)
        if _modify:
            ax.add_patch(poly)
            p = PolygonInteractor(ax, poly, path=_fpath)
    
    plt.show()


def misc():
    Domain_Data = nc.Dataset('wrfconstants_conus404_IDWR.nc')
    Domain_Lat =Domain_Data.variables['XLAT'][:][0] #Latitude (South is negative)
    Domain_Lon =Domain_Data.variables['XLONG'][:][0] #Longitude (West is negative)
    Domain_Height =Domain_Data.variables['HGT'][:] #Terrain Height

    topo_data = '@earth_relief_30s' #Topographic basemap

    fig = plt.figure(figsize=(7, 6))
    # Generate axes using Cartopy
    
    pf = 'masks/AnacondaEast.nc'
    ds = xr.open_dataset(pf, engine = 'netcdf4')
    ds=ds.squeeze()
    _dh=Domain_Height[0]
    _dh = _dh/2200
    _el_mask = ds.mask * _dh
    
    # fig = pygmt.Figure()
    ax = plt.axes(projection=ccrs.PlateCarree())
    # ax = plt.axes()
    # ax.set_extent((-114.2, -112.25, 44.85, 46.15), crs=ccrs.PlateCarree())
    ax.set_extent((-114.2, -112.25, 44.85, 47.15), crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.STATES)

    AE=plt.contour(
        to_np(Domain_Lon),
        to_np(Domain_Lat),
        #  ds.V_700MB,
        #  ds.mask,
        _el_mask,
        # levels=np.linspace(0.0, 0.08, 15),
        cmap='gray',
        # vmin=0.5,
        # vmax=0.08,
        zorder=4,
        alpha = 0.5,
        # add_colorbar=False
    )
    pf = 'masks/AnacondaWest.nc'
    ds = xr.open_dataset(pf, engine = 'netcdf4')
    ds=ds.squeeze()
    _dh=Domain_Height[0]
    _dh = _dh/2200
    _el_mask = ds.mask * _dh
    AW=plt.contour(to_np(Domain_Lon),
                to_np(Domain_Lat),
                #  ds.V_700MB,
                #  ds.mask,
                _el_mask,
                # levels=np.linspace(0.0, 0.08, 15),
                cmap='gray',
                # vmin=0.5,
                # vmax=0.08,
                zorder=4,
                alpha = 0.5,
                # add_colorbar=False
                    )

    pf = 'masks/BeaverHeadNorth.nc'
    ds = xr.open_dataset(pf, engine = 'netcdf4')
    ds=ds.squeeze()
    _dh=Domain_Height[0]
    _dh = _dh/2200
    _el_mask = ds.mask * _dh
    BHN=plt.contour(to_np(Domain_Lon),
                to_np(Domain_Lat),
                #  ds.V_700MB,
                #  ds.mask,
                _el_mask,
                # levels=np.linspace(0.0, 0.08, 15),
                cmap='gray',
                # vmin=0.5,
                # vmax=0.08,
                zorder=4,
                alpha = 0.5,
                # add_colorbar=False
                    )

    pf = 'masks/BeaverHeadSouth.nc'
    ds = xr.open_dataset(pf, engine = 'netcdf4')
    ds=ds.squeeze()
    _dh=Domain_Height[0]
    _dh = _dh/2200
    _el_mask = ds.mask * _dh
    BHS=plt.contour(
                to_np(Domain_Lon),
                to_np(Domain_Lat),
                #  ds.V_700MB,
                #  ds.mask,
                 _el_mask,
                 # levels=np.linspace(0.0, 0.08, 15),
                 cmap='gray',
                 # vmin=0.5,
                 # vmax=0.08,
                 zorder=4,
                 alpha = 0.5,
                # add_colorbar=False
                    )
    pf = 'masks/PioneerEast.nc'
    ds = xr.open_dataset(pf, engine = 'netcdf4')
    ds=ds.squeeze()
    _dh=Domain_Height[0]
    _dh = _dh/2200
    _el_mask = ds.mask * _dh
    PE=plt.contour(
                to_np(Domain_Lon),
                to_np(Domain_Lat),
                #  ds.V_700MB,
                #  ds.mask,
                 _el_mask,
                 # levels=np.linspace(0.0, 0.08, 15),
                 cmap='gray',
                 # vmin=0.5,
                 # vmax=0.08,
                 zorder=4,
                 alpha = 0.5,
                # add_colorbar=False
                    )
    pf = 'masks/PioneerWest.nc'
    ds = xr.open_dataset(pf, engine = 'netcdf4')
    ds=ds.squeeze()
    _dh=Domain_Height[0]
    _dh = _dh/2200
    _el_mask = ds.mask * _dh
    PW=plt.contour(
                to_np(Domain_Lon),
                to_np(Domain_Lat),
                #  ds.V_700MB,
                #  ds.mask,
                 _el_mask,
                 # levels=np.linspace(0.0, 0.08, 15),
                 cmap='gray',
                 # vmin=0.5,
                 # vmax=0.08,
                 zorder=4,
                 alpha = 0.5,
                # add_colorbar=False
                    )
    # pf = 'masks/TobaccoRoot.nc'
    # ds = xr.open_dataset(pf, engine = 'netcdf4')
    # ds=ds.squeeze()
    # _dh=Domain_Height[0]
    # _dh = _dh/2200
    # _el_mask = ds.mask * _dh
    # TR=plt.contour(
    #             to_np(Domain_Lon),
    #             to_np(Domain_Lat),
    #             #  ds.V_700MB,
    #             #  ds.mask,
    #              _el_mask,
    #              # levels=np.linspace(0.0, 0.08, 15),
    #              cmap='gray',
    #              # vmin=0.5,
    #              # vmax=0.08,
    #              zorder=4,
    #              alpha = 0.5,
    #             # add_colorbar=False
    #                 )
    def plot_shapefile(shpfile):
        _shp = shapefile.Reader(shpfile)

        for shape in _shp.shapeRecords():
            x = [i[0] for i in shape.shape.points[:]]
            y = [i[1] for i in shape.shape.points[:]]
            plt.plot(x,y)

    plot_shapefile('shapefiles/AnacondaEast.shp')
    plot_shapefile('shapefiles/AnacondaWest.shp')
    plot_shapefile('shapefiles/BeaverHeadNorth.shp')
    plot_shapefile('shapefiles/BeaverHeadSouth.shp')
    plot_shapefile('shapefiles/PioneerEast.shp')
    plot_shapefile('shapefiles/PioneerWest.shp')
    plot_shapefile('shapefiles/TobaccoRoot.shp')
    

    Topo = plt.contour(
        to_np(Domain_Lon),
        to_np(Domain_Lat),
        Domain_Height[0],
        alpha = 0.6,
        # add_colorbar=False,
        cmap ='gray',
        # vmin=5500,
        # vmax=5500,
        # levels = 30
    )
    #zorder=4,)
    ax.clabel(Topo, inline = 1, fontsize = 6)
    gl = ax.gridlines(
        crs=ccrs.PlateCarree(),
        draw_labels=True,
        dms=False,
        x_inline=False,
        y_inline=False,
        linewidth=1,
        color="k",
        alpha=0.25,
        zorder=4)
    gl.top_labels = False
    gl.right_labels = False

    gl.xlabel_style = {"rotation": 45, "size": 10}
    gl.ylabel_style = {"rotation": 0, "size": 10}
    gl.xlines = True
    gl.ylines = True
    fig.patch.set_facecolor('white')

    theta = np.arange(0, 2*np.pi, 1)
    r = .5

    xs = (r * np.cos(theta)) -113.3
    ys = r * np.sin(theta) + 46
    
    poly = Polygon(np.column_stack([xs, ys]), animated=True, alpha=0.5)

    # fig, ax = plt.subplots()
    ax.add_patch(poly)
    p = PolygonInteractor(ax, poly)

    # ax.set_title('Click and drag a point to move it')
    # ax.set_xlim((-2, 2))
    # ax.set_ylim((-2, 2))
    plt.show()
    # fig.show()