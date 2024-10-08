from arcgis.gis import GIS
gis = GIS("home")

# Import Libraries
import io
import os
import sys
import arcpy
from zipfile import ZipFile
import pandas as pd
import requests
from arcgis.features import GeoAccessor, GeoSeriesAccessor, FeatureCollection, FeatureSet
from arcgis.geometry import SpatialReference

# Request: NDAWN Data
ndawn_link = r"https://ndawn.ndsu.nodak.edu/table.csv?station=219&station=220&station=223&station=93&station=183&station=156&station=70&variable=wdmxt&variable=wdsr&variable=wdr&variable=wddp&ttype=weekly&quick_pick=&begin_date=2024-09-16&count=1"
ndawn_request = requests.get(ndawn_link)
ndawn_response = ndawn_request.content

#print(ndawn_response)
df = pd.read_csv(io.StringIO(ndawn_response.decode('utf-8')), skiprows=[0,1,2,4], index_col=False)
df.drop(df.columns[[8,9,11,12,14,15,17,18]], axis=1, inplace=True)
df.head()

# Convert DataFrame to SeDF
sedf_ndawn = pd.DataFrame.spatial.from_xy(df, "Longitude", "Latitude", crs=4326)
sedf_ndawn.head()

# Save the SpatialDataFrame to a shapefile
output_file_path = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\sedf_ndawn.shp"
sedf_ndawn.spatial.to_featureclass(output_file_path)

# Example of projecting a shapefile to a different CRS
output_shapefile = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\sedf_ndawn_proj.shp"
spatial_reference = arcpy.SpatialReference(4326)

# Project the Shapefile
arcpy.Project_management(output_file_path, output_shapefile, spatial_reference)

# Shapefile back into a Spatial DataFrame
sedf_ndawn_proj = pd.DataFrame.spatial.from_featureclass(output_shapefile)

# Display the first few rows of the projected Spatial DataFrame
sedf_ndawn_proj.head()

# Request: MN GeoCommons -- MN County Boundaries

# Call CKAN API and Search for Minnesota Counties JSON 
mn_meta = r"https://gisdata.mn.gov/api/3/action/package_search?q=minnesota%20counties"
mn_meta_response = requests.get(mn_meta)

mn_meta_output = mn_meta_response.json()

# Scan JSON for MN County GeoDatabase Zip File
mn_county_zip = mn_meta_output["result"]["results"][0]["resources"][3]["url"]
print(mn_county_zip)

import zipfile

# Save the ZIP file
mn_county_response = requests.get(mn_county_zip)

zip_file_path = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\mn_county_bounds.zip"
with open(zip_file_path, 'wb') as f:
    f.write(mn_county_response.content)  # Write the response content to the ZIP file

# Open the ZIP file and print its contents
with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
    # Print the contents of the ZIP file
    zip_ref.printdir()   # This will show the files inside the ZIP
    
    # Create a directory for extraction if it doesn't exist
    extraction_path = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\extracted_files"
    os.makedirs(extraction_path, exist_ok=True)  # Create the directory if it doesn't exist
    
    # Extract all files to the specified directory
    zip_ref.extractall(extraction_path)

# Show the files you just extracted
print("Files in the extracted directory:")
print(os.listdir(extraction_path))

# Read the shapefile
sedf_cty = pd.DataFrame.spatial.from_featureclass(r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\extracted_files\mn_county_boundaries.shp")
sedf_cty.spatial.project(SpatialReference(4326))
sedf_cty.head()

# Optional: Save the SpatialDataFrame to a shapefile
output_file_path = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\sedf_cty.shp"
sedf_cty.spatial.to_featureclass(output_file_path)

# Display the first few rows of the SpatialDataFrame
sedf_cty.head()

# ArcGIS RestAPI Access
import requests


arc_api_link = r"https://arcgis.dnr.state.mn.us/host/rest/services/Hosted/DOT_Roads/FeatureServer/1/query?where=1%3D1&outFields=*&f=geojson"
arc_response = requests.get(arc_api_link, stream=True).json()

arc_geojson = FeatureSet.from_dict(arc_response)

# Create a SeDF from the GeoJSON data
sedf_streets = arc_geojson.sdf
sedf_streets.head()

# Save the SpatialDataFrame to a shapefile
output_file_path = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\sedf_streets.shp"
sedf_streets.spatial.to_featureclass(output_file_path)

# Example of projecting a shapefile to a different CRS
output_shapefile = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\sedf_streets_proj.shp"
spatial_reference = arcpy.SpatialReference(4326)

# Project the Shapefile
arcpy.Project_management(output_file_path, output_shapefile, spatial_reference)

# Shapefile back into a Spatial DataFrame
sedf_streets_proj = pd.DataFrame.spatial.from_featureclass(output_shapefile)

# Display the first few rows of the SpatialDataFrame
sedf_streets_proj.head()

# Geometry Check:
desc_counties = arcpy.Describe(counties_shp)
desc_cities = arcpy.Describe(cities_shp)
desc_roads = arcpy.Describe(roads_shp)

print(f"Counties Geometry Type: {desc_counties.shapeType}")
print(f"Cities Geometry Type: {desc_cities.shapeType}")
print(f"Roads Geometry Type: {desc_roads.shapeType}")

# Coordinate System, Spatial Reference Check:
print(f"Counties Spatial Reference: {desc_counties.spatialReference.name}")
print(f"Cities Spatial Reference: {desc_cities.spatialReference.name}")
print(f"Roads Spatial Reference: {desc_roads.spatialReference.name}")

# Spatially Join all 3 Layers

# First Spatial Join Layer
target_features = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\sedf_cty.shp"
join_features = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\sedf_ndawn_proj.shp"
out_feature_class_1 = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\join_test1.shp"
out_feature_class_2 = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\join_test2.shp"

arcpy.SpatialJoin_analysis(target_features, join_features, out_feature_class_1)

# Second Spatial Join Layer
additional_join_features = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\sedf_streets_proj.shp"
arcpy.SpatialJoin_analysis(out_feature_class_1, additional_join_features, out_feature_class_2)

# Read the shapefile
sedf_test2 = pd.DataFrame.spatial.from_featureclass(r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\join_test2.shp")
sedf_test2.spatial.project(SpatialReference(4326))
sedf_test2.head()

# Find the counties that contain the NDAWN Data
counties_shp = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\sedf_cty.shp"
cities_shp = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\sedf_ndawn_proj.shp"
roads_shp = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\sedf_streets_proj.shp" 

# Spatial Join to find counties with cities
counties_with_cities = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\counties_with_cities.shp"
arcpy.SpatialJoin_analysis(counties_shp, cities_shp, counties_with_cities, 
                           join_type="KEEP_COMMON", 
                           match_option="INTERSECT")

print(f"Counties with cities saved to {counties_with_cities}")

# Spatial Join to find roads within the filtered counties
roads_within_counties = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\roads_within_counties.shp"
arcpy.SpatialJoin_analysis(roads_shp, counties_with_cities, roads_within_counties, 
                           join_type="KEEP_COMMON", 
                           match_option="INTERSECT")

print(f"Roads within counties saved to {roads_within_counties}")

# Path where you want to create the new geodatabase
gdb_test2_path = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\test2_geodatabase.gdb"

# Create a new file geodatabase
arcpy.CreateFileGDB_management(r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1", "test2_geodatabase")

print(f"Geodatabase created at {gdb_test2_path}")

# Spatial DataFrame Test2 shapefile path
sdf_Test2 = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\join_test2.shp"

# Specify the output feature class name
output_fc_test2 = "sedf_test2"

# Convert the shapefile to a feature class in the geodatabase
arcpy.FeatureClassToGeodatabase_conversion([sdf_Test2], gdb_test2_path)

print(f"Feature class {output_fc_test2} saved to {gdb_test2_path}")

# Re-Define the filepaths:
cities_shp = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\sedf_ndawn_proj.shp"
counties_with_cities = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\counties_with_cities.shp"
roads_within_counties = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\roads_within_counties.shp"

# Spatially Join all 3 Layers

# First Spatial Join Layer
target_features = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\counties_with_cities.shp"
join_features = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\roads_within_counties.shp"
out_fc_cty_roads = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\join_cty_roads.shp"
out_fc_all = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\join_all.shp"

arcpy.SpatialJoin_analysis(target_features, join_features, out_fc_cty_roads)

# Second Spatial Join Layer
additional_join_features = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\sedf_ndawn_proj.shp"
arcpy.SpatialJoin_analysis(out_fc_cty_roads, additional_join_features, out_fc_all)

# Path where you want to create the new geodatabase
gdb_joinAll_path = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\joinAll_geodatabase.gdb"

# Create a new file geodatabase
arcpy.CreateFileGDB_management(r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1", "joinAll_geodatabase")

print(f"Geodatabase created at {gdb_joinAll_path}")

# Spatial DataFrame JoinAll shapefile path
sdf_joinAll = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab1\Joined_Files\join_all.shp"

# Specify the output feature class name
output_fc_joinAll = "sedf_joinAll"

# Convert the shapefile to a feature class in the geodatabase
arcpy.FeatureClassToGeodatabase_conversion([sdf_joinAll], gdb_joinAll_path)

print(f"Feature class {output_fc_joinAll} saved to {gdb_joinAll_path}")


