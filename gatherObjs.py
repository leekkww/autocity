import os
import bpy
import sys

argv = sys.argv
argv = argv[argv.index("--") + 1:]

# put the location to the folder where the objs are located
path_to_obj_dir = argv[0]

#"/Users/leekkww/Documents/School/MEng/OSM/east_cambridge/out_v4/"

# file structure should look like this:
# --path_to_obj_dir
# ----0001
# ------out.mtl
# ------out.obj
# ------[other files...]
# ----0001_glass
# ------glass.mtl
# ------glass.obj
# ------[other files...]
# ----[other building and glass files...]

for folder_name in os.listdir(path_to_obj_dir):
    folder = os.path.join(path_to_obj_dir, folder_name)
    if os.path.isdir(folder):
        obj_list_temp = [item for item in os.listdir(folder) if item == "out.obj"]
        if len(obj_list_temp) == 0:
            continue
        obj_path = os.path.join(folder, obj_list_temp[0])
        bpy.ops.import_scene.obj(filepath = obj_path)