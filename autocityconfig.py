"""autocityconfig.py: configuration file """


############################
# Everything below this line (and before the next line) must be defined

# specify the root folder for where we want the intermediate output
ROOT_FOLDER = "OSM/east_cam_med/"

# GML file which contains footprints for the city
GML_FILE = "OSM/east_cam_med/east_cam_med.gml"





########################################
# Everything below this line is default values.
# you can change them if you want.

# scale is multiplicative factor applied to X and Y coordinates
# in order to make the buildings look like a good size when imported
# into Blender. this is usually a function of the GML encoding.
# 20000 sort of works for EPSG:4326.
SCALE = 25000.

# this determines whether all buildings have the same height.
# if this is True, all building will have the same height as determined by MAX_HEIGHT
SAME_HEIGHT = False

# hard coded maximum height for buildings
MAX_HEIGHT = 15.



# this determines whether we will have roofs in our buildings.
GEN_ROOFS = True

# this determines how high our roofs are, as a multiplicative factor of height
ROOF_HEIGHT_FACTOR = 1. / 4

# this determines how likely a roof is to occur on a building
ROOF_PROB = 0.6



# if we want to generate a specific number of buildings
# or we want to start generating at a specific point,
# we can specify here. if NUM_BUILDINGS is -1, we will 
# generate all buildings.
START_POINT = 0
NUM_BUILDINGS = -1