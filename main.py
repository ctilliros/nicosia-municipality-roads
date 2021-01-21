import osmnx as ox
import json
import pandas as pd 
import geopandas as gpd
from geoalchemy2 import Geometry
from shapely.geometry import Point, Polygon, LineString, shape
from shapely import wkt
from sqlalchemy import create_engine
from config import *

place = "Nicosia, Cyprus"
G = ox.graph_from_place(place, simplify=True)
roads = ox.graph_to_gdfs(G, nodes=False)

with open('nicosia_mun_areas.json','r') as f:
	oria = json.load(f)
f.close()


gdf = gpd.GeoDataFrame.from_features(oria["features"])


df_roads = pd.DataFrame(columns={'geometry','name','oneway','lanes','highway','length','postalcode','areaEN','areaGR'})

with open('nicosia_postcodes_with_population.json','r') as f:
	postalcodes = json.load(f)
f.close()

gdfpostal = gpd.GeoDataFrame.from_features(postalcodes["features"])

def find_postal_code(coords):
	for postal in range(0, len(gdfpostal)):
		if (Point(coords)).within(gdfpostal['geometry'][postal]):
			return gdfpostal['post_code'][postal]

coordinates = []

engine = create_engine('postgresql+psycopg2://'+user+':'+password+'@'+host+':'+port+'/'+database)

for _, row in roads.iterrows():
    for key, value in row.items():
        if key == 'geometry':
            for i in range(0,len(gdf)):
                for y in value.coords:
                    if (Point(y)).within(gdf['geometry'][i]):  
                        postalcode = find_postal_code(y)
                        coordinates.append(y)
                if len(coordinates):
                    if len(coordinates)==1:
                        point = "POINT ("+str(coordinates[0][0])+str(coordinates[0][1])+")"
                        df_roads = df_roads.append({"geom":point, "name":roads['name'][_], "oneway":row['oneway'],
                                                "lanes":row['lanes'], "highway":row['highway'], "length": row['length'],
                                                "postalcode":postalcode,"areaGR":gdf['QRTR_NM_G'][i],"areaEN":gdf['QRTR_NM_E'][i]},ignore_index=True)
                        coordinates = []
                    else:
                        line_string = "LINESTRING ("
                        points = []
                        for values in coordinates:
                            line_string = line_string + str(values[0]) + " " + str(values[1])
                            line_string = line_string + ','
                        line_string = line_string[:-1]
                        line_string = line_string + ")"

                        if type(row['lanes']) is list:
                            lanes = max(row['lanes'])
                        else:
                            lanes = row['lanes']

                        df_roads = df_roads.append({"geom":line_string, "name":roads['name'][_], "oneway":row['oneway'],
                                                "lanes":row['lanes'], "highway":row['highway'], "length": row['length'],
                                                "postalcode":postalcode,"areaGR":gdf['QRTR_NM_G'][i],"areaEN":gdf['QRTR_NM_E'][i]},ignore_index=True)
                        coordinates = []                    
df_roads.to_sql('roads', engine, if_exists = 'replace')