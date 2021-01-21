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


for _, row in roads.iterrows():
	for key, value in row.items():
		if key == 'geometry':
			for i in range(0,len(gdf)):
				for y in value.coords:
					if (Point(y)).within(gdf['geometry'][i]):  
						postalcode = find_postal_code(y)
						df_roads = df_roads.append({"geometry":value, "name":roads['name'][_], "oneway":row['oneway'],
													"lanes":row['lanes'], "highway":row['highway'], "length": row['length'],
													"postalcode":postalcode,"areaGR":gdf['QRTR_NM_G'][i],"areaEN":gdf['QRTR_NM_E'][i]},ignore_index=True)
# 						break
# host = "localhost"
# user = "postgres"
# port = '5432'
# database = "testing"
# password = "9664241907"

engine = create_engine('postgresql+psycopg2://'+user+':'+password+'@'+host+':'+port+'/'+database)

gdf1 = gpd.GeoDataFrame(df_roads, geometry='geometry')
gdf1.drop('geometry', 1, inplace=True)
gdf1.to_sql('roads', engine, if_exists='replace',  dtype={'geom': Geometry(geometry_type='LINESTRING', srid='32633',dimension='3')})
