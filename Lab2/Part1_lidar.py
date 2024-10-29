import io
import os
import sys
import arcpy
import laspy
from zipfile import ZipFile
import pandas as pd
import requests
import ftplib
from bs4 import BeautifulSoup as bs
from arcgis.features import GeoAccessor, GeoSeriesAccessor, FeatureCollection, FeatureSet

DOMAIN = "https://resources.gisdata.mn.gov"
URL = "https://resources.gisdata.mn.gov/pub/data/elevation/lidar/county/winona/laz/"
FILETYPE = ".laz"

# Directory where the .laz files will be saved
save_folder = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab2\laz_files"
os.makedirs(save_folder, exist_ok=True)  # Create the folder if it doesn't exist

# Function to fetch and parse the HTML from the URL
def get_laz(url):
    return bs(requests.get(url).text, 'html.parser')

# Loop through all links on the page and download the ones that contain the specified file type (.laz)
for link in get_laz(URL).find_all('a'):
    laz_link = link.get('href')
    if laz_link and FILETYPE in laz_link:  # Check if laz_link is not None
        
        # Construct a full URL using URL if relative path
        if laz_link.startswith('/'):
            full_url = URL + laz_link  # Relative link, add URL
        else:
            full_url = laz_link  # Absolute link, use it as is
        
        # Append the filename if needed
        if not full_url.startswith('http'):
            full_url = f"{URL}/{laz_link}"  # Ensure it has the correct structure

        filename = os.path.basename(laz_link)  # Extract the filename from the URL
        
        # Full path to save the .laz file
        file_path = os.path.join(save_folder, filename)
        
        # Download and save the .laz file
        print(f"Downloading {full_url}...")
        try:
            response = requests.get(full_url)
            response.raise_for_status()  # Message for any errors produced
            
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print(f"Saved to {file_path}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to download {full_url}: {e}")

# Specify the folder containing LAZ files and output paths
input_laz_folder = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab2\laz_files"  # Path to your folder with .laz files
output_las_folder = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab2\las_files"  # Output folder for .las files
lasd_output = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab2\las_dataset.lasd"  # Output .lasd file

# Define the spatial reference using EPSG:26915 (NAD83 / UTM zone 15N)
spatial_ref = arcpy.SpatialReference(26915)  # EPSG:26915 for NAD83 / UTM zone 15N

# Ensure the output LAS folder exists
if not os.path.exists(output_las_folder):
    os.makedirs(output_las_folder)

# Remove existing LAS dataset if it exists
if os.path.exists(lasd_output):
    arcpy.management.Delete(lasd_output)  # Delete the existing LAS dataset to avoid errors

# Loop through all .laz files in the input folder
for laz_file in os.listdir(input_laz_folder):
    if laz_file.endswith(".laz"):
        input_laz_file = os.path.join(input_laz_folder, laz_file)

        # Convert LAZ to LAS using ConvertLas tool
        arcpy.conversion.ConvertLas(
            input_laz_file, 
            output_las_folder,  # Specify the target folder for .las files
            compression="NO_COMPRESSION",  # Disable compression
            define_coordinate_system="ALL_FILES",  # Define coordinate system for all files
            in_coordinate_system=spatial_ref  # Set the input coordinate system to EPSG:26915
        )
        print(f"Converted {laz_file} and added to {output_las_folder}")

# Create a LAS dataset (.lasd) from the LAS files and apply the spatial reference EPSG:26915
las_files = [os.path.join(output_las_folder, f) for f in os.listdir(output_las_folder) if f.endswith(".las")]

# Check if there are any LAS files to create a LAS dataset
if las_files:
    arcpy.management.CreateLasDataset(
        las_files,
        lasd_output,
        spatial_reference=spatial_ref,  # Apply EPSG:26915 spatial reference
        folder_recursion="NO_RECURSION",
        in_surface_constraints=""
    )
    print(f"LAS dataset created at {lasd_output} with EPSG:26915")
else:
    print("No LAS files found for creating LAS dataset.")

print("Process complete!")

# Define the path to the LAS dataset
lasd_file_path = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab2\las_dataset.lasd"

# Check if the LAS dataset exists
if os.path.exists(lasd_file_path):
    print(f"Retrieving statistics for LAS dataset at {lasd_file_path}...")

    try:
        # Use Describe to get the properties of the LAS dataset
        desc = arcpy.Describe(lasd_file_path)

        # Display the statistics
        print("LAS Dataset Statistics:")
        print(f"Point Count: {desc.pointCount}")
        print(f"Bounding Box: {desc.extent.XMin}, {desc.extent.YMin}, {desc.extent.XMax}, {desc.extent.YMax}")
        print(f"Z Min: {desc.zMin}")
        print(f"Z Max: {desc.zMax}")
        print(f"Average Return Number: {desc.avgReturnNumber}")
        print(f"Number of Returns: {desc.numberOfReturns}")

    except Exception as e:
        print(f"Failed to retrieve LAS dataset statistics: {e}")
else:
    print("LAS dataset not found.")

# Convert the .lasd to a DEM

# Paths to input LAS dataset and output DEM
las_dataset = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab2\las_dataset.lasd"  # Your LAS dataset file
output_dem = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab2\DEM\output_dem.tif"  # Output DEM (raster)

# Ensure the output DEM directory exists
output_dir = os.path.dirname(output_dem)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Convert LAS dataset to Raster (DEM) using Binning interpolation
arcpy.conversion.LasDatasetToRaster(
    las_dataset,
    output_dem,
    value_field="ELEVATION",  # Use ELEVATION field for DEM creation
    data_type="FLOAT",  # Set output raster data type to FLOAT
    z_factor=1,  # No vertical exaggeration
    )

print(f"DEM successfully created at: {output_dem}")


# Convert the DEM to a TIN

# Input DEM (from LAS dataset conversion) - Using raw string to avoid backslash issues
las_dataset = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab2\las_files\4342-26-62.las"  # Your LAS dataset file

# Output TIN path - Ensure it's a valid path and use raw string as well
output_tin = r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab2\TIN\output_tin.tin"

# Convert Raster (DEM) to TIN using arcpy.3d.RasterToTIN
arcpy.ddd.LasDatasetToTin(
    in_las_dataset=las_dataset,  # Input DEM raster
    out_tin=output_tin,  # Output TIN path
    thinning_type="RANDOM",
    thinning_method="NODE_COUNT",
    max_nodes=15,  
    z_factor=1
)

print(f"TIN created successfully at: {output_tin}")

# Output TIN Layout as PDF
aprx = arcpy.mp.ArcGISProject(r"C:\Users\ethan\Documents\ArcGIS\Projects\GIS5571_Lab2\GIS5571_Lab2.aprx")
lyt = aprx.listLayouts("TIN*")[0]
lyt.exportToPDF(r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab2\PDF_export\SE-MN_TIN.pdf", resolution=300)

# Output DEM Layout as PDF
aprx = arcpy.mp.ArcGISProject(r"C:\Users\ethan\Documents\ArcGIS\Projects\GIS5571_Lab2\GIS5571_Lab2.aprx")
lyt = aprx.listLayouts("DEM*")[0]
lyt.exportToPDF(r"C:\Users\ethan\Desktop\ARLT_MGIS\GIS5571\Lab2\PDF_export\SE-MN_DEM.pdf", resolution=300)


