import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

import io, pickle
import numpy as np

from utils.info import EARTHQUAKE_FIG

class mapper:
    def __init__(self) -> None:
        longitude_min = 119
        longitude_max = 123
        latitude_min = 21
        latitude_max = 26
        res = '10m'



        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={'projection': ccrs.PlateCarree()})
        tick_proj = ccrs.PlateCarree()
        ax.set_xticks(np.arange(longitude_min, longitude_max, 1), crs=tick_proj)
        ax.set_xticks(np.arange(longitude_min, longitude_max, 1), minor=True, crs=tick_proj)
        ax.set_yticks(np.arange(latitude_min, latitude_max, 1), crs=tick_proj)
        ax.set_yticks(np.arange(latitude_min, latitude_max, 1), minor=True, crs=tick_proj)
        ax.xaxis.set_major_formatter(LongitudeFormatter())
        ax.yaxis.set_major_formatter(LatitudeFormatter())

        
        state_boundaries = cfeature.NaturalEarthFeature(
            category='cultural',
            name='admin_1_states_provinces_lines', 
            scale=res, 
            facecolor='none'
        )


        ax.set_extent([longitude_min, longitude_max, latitude_min, latitude_max], crs=tick_proj)

        ax.coastlines(resolution=res)
        ax.add_feature(state_boundaries, edgecolor='black', alpha = 0.3)
        ax.add_feature(cfeature.BORDERS.with_scale(res))
        ax.gridlines(linestyle='--')
        fig.tight_layout()
        self.fig = fig

    def copy_fig(self):
        buf = io.BytesIO()
        pickle.dump(self.fig, buf)
        buf.seek(0)
        return pickle.load(buf) 

    def create_figure(self,lon,lag):
        this_fig = self.copy_fig()
        ax = this_fig.axes[0]
        ax.plot(lon, lag, 'rx', transform=ccrs.Geodetic(), markersize=10)
        this_fig.savefig(EARTHQUAKE_FIG)
        return EARTHQUAKE_FIG
    


if __name__ == "__main__":
    m = mapper()
    m.create_figure(120, 25)
    print("done")