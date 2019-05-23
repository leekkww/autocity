#!/usr/bin/env python3

import os
import random
import sys
import xml.etree.ElementTree as ET

# importing all config values from autocityconfig
from autocityconfig import *

# check that we are using python 3, because integer division is bad
if not (sys.version_info[0] ==3):
    raise Exception("Must be using Python 3")

# ensure that we have deterministic generation
random.seed(0)

# defining output location
OUTPUT_OBJ_FOLDER = ROOT_FOLDER + "buildings/"
OUTPUT_OBJ_FILE = ROOT_FOLDER + "east_cam_med.obj"

# if output folder is not created, create it
if not os.path.isdir(OUTPUT_OBJ_FOLDER):
	os.mkdir(OUTPUT_OBJ_FOLDER)

# helper variables to help center our obj file
X_AVG = 0
Y_AVG = 0

def parseXML(xml_file):
	'''
		Parse an XML file (GML, specifically) to find footprints of buildings
	'''

	# that means we have bounds of -90,90 and -180,180
	# see https://spatialreference.org/ref/epsg/wgs-84/
	#if "EPSG:4326" in xml_file:

	tree = ET.parse(xml_file)
	root = tree.getroot()

	xmin = float(root[0][0][0][0].text)
	xmax = float(root[0][0][1][0].text)
	xavg = (xmin + xmax) / 2

	ymin = float(root[0][0][0][1].text)
	ymax = float(root[0][0][1][1].text)
	yavg = (ymin + ymax) / 2

	footprints = []

	for featureMember in root.iter("{http://www.opengis.net/gml}featureMember"):
		# this step is basically filtering away buildings that are circular
		building = featureMember[0]
		man_made_info = building.find("{http://ogr.maptools.org/}man_made")
		if man_made_info is not None and man_made_info.text == "smokestack":
			# I only currently know that smokestacks are circular
			# TODO figure out a better way of knowing if a building is circular
			print("stack")
			continue
		
		for coordinates in building.iter("{http://www.opengis.net/gml}coordinates"):
			coord_list = [tuple([float(x) for x in coord.split(",")]) for coord in coordinates.text.split()]
			footprints.append(coord_list)

	# TODO eventually determine how tall buildings should be based on GML type
	height = MAX_HEIGHT

	return xavg, yavg, height, footprints

def addDimension(vertex, val):
	return (-(vertex[0]-X_AVG)*SCALE, val, (vertex[1]-Y_AVG)*SCALE)

def distance(p1, p2):
	return float((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

def createDumbBuildings(footprints, building_start = 0, building_total = -1):
	'''
		Given footprints of a building (parsed by parseXML), create a list of faces
		building start is what index of building we want

		Output: list of objects, where each object is a list of faces,
				where each face is a list of coordinates stored in clockwise order
	'''
	listofObjs = []
	building_count = 0

	for building in footprints:
		if len(building) < 3:
			# we need at least 3 points to have a building...
			continue

		if building_count < building_start:
			building_count += 1
			continue

		height = HEIGHT

		if not SAME_HEIGHT:
			# we first determine how big the building is by the max edge
			# so that we can decide if we need to height adjust
			max_edge_len = 0
			for i in range(len(building) - 1):
				# this point and the next point in the footprint
				p1 = building[i]
				p2 = building[i+1]
				max_edge_len = max(max_edge_len, distance(p1, p2) * SCALE)

			height = min(HEIGHT, max_edge_len)

		listOfFaces = []

		# for every pair of vertices, create a rectangle
		roof = []
		floor = []

		for i in range(len(building) - 1):
			# p1 and p2 are this point and the next point in the footprint
			# note that we don't need to wrap around because GML contains
			# an extra vertex at the end that's a duplicate of the first vertex
			p1 = building[i]
			p2 = building[i+1]

			roof.append(addDimension(p1, height))
			floor.append(addDimension(p1, 0))

			face = []
			v1 = addDimension(p1, 0)
			v2 = addDimension(p2, 0)
			v3 = addDimension(p2, height)
			v4 = addDimension(p1, height)
			
			face.append(v4)
			face.append(v3)
			face.append(v2)
			face.append(v1)

			listOfFaces.append(face)

		# dumb versions of roof
		if GEN_ROOFS and len(building) - 1 == 4 and random.random() < ROOF_PROB:
			# we currently only add a roof if there are exactly 4 vertices
			# and also the probability has to be right

			# calculate center of mass
			x_sum = 0
			y_sum = 0
			for i in range(len(building) - 1):
				x_sum += building[i][0]
				y_sum += building[i][1]
			center = (x_sum / 4, y_sum / 4)

			# add 4 roofs
			for i in range(len(building) - 1):
				p1 = building[i]
				p2 = building[i+1]

				roof = []
				v1 = addDimension(p1, height)
				v2 = addDimension(p2, height)
				v3 = addDimension(center, height * (1+ROOF_HEIGHT_FACTOR))

				roof.append(v3)
				roof.append(v2)
				roof.append(v1)

				listOfFaces.append(roof)
		else:
			roof.reverse()
			listOfFaces.append(roof)

		# we need a floor
		listOfFaces.append(floor)

		listofObjs.append(listOfFaces)
		building_count += 1
		if building_count == building_start + building_total:
			break

	return listofObjs


class VertexSet:
	def __init__(self):
		# 1-indexing, as with obj files
		self.vertices = {}
		self.vertex_list = []
	
	def add(self, ver):
		if ver in self.vertices:
			return self.vertices[ver]

		size = len(self.vertices) + 1
		self.vertices[ver] = size
		self.vertex_list.append(ver)
		return size

	def size(self):
		return len(self.vertices)


def facesToOBJ(listofObjs, output_path, output_dir, building_start = 0):
	'''
		Given a list of objs, write OBJ output to output_path.
		Also write individual OBJ output to output_dir

		Input: list of faces, where each face is a list of coordinates
		       stored in counter-clockwise order
	'''

	# dummy variables for writing large OBJ file with all buildings
	vertices = VertexSet()
	objsOutput = []

	for listOfFaces in listofObjs:
		facesOutput = []
		for face in listOfFaces:

			indices = []
			for i in range(len(face)):
				ind = vertices.add(face[i])
				indices.append(ind)

			facesOutput.append(indices)
		objsOutput.append(facesOutput)

	# actually writing overall OBJ file
	with open(output_path,"w+") as file_out:
		for vertex in vertices.vertex_list:
			file_out.write("v %f %f %f\n" % (vertex[0],vertex[1],vertex[2]))
		for i in range(len(objsOutput)):
			obj = objsOutput[i]
			file_out.write("g building_%d\n" % i)
			for face in obj:
				vertices = " ".join([str(x) for x in face])
				file_out.write("f %s\n" % vertices)
			file_out.write("\n")

	# writing todo.list file
	todo_list_path = os.path.join(output_dir, "todo.list")
	with open(todo_list_path, "w+") as todo_out:
		for obj_ind in range(len(listofObjs)):
			todo_out.write("%04d.obj\n" % (obj_ind + building_start))

	# for writing individual small OBJ files
	for obj_ind in range(len(listofObjs)):
		listOfFaces = listofObjs[obj_ind]
		vertices = VertexSet()
		facesOutput = []
		for face in listOfFaces:
			indices = []
			for i in range(len(face)):
				ind = vertices.add(face[i])
				indices.append(ind)

			facesOutput.append(indices)
		objsOutput.append(facesOutput)

		obj_output_path = os.path.join(output_dir, "%04d.obj" % (obj_ind + building_start))
		with open(obj_output_path, "w+") as file_out:
			for vertex in vertices.vertex_list:
				file_out.write("v %f %f %f\n" % (vertex[0],vertex[1],vertex[2]))
			file_out.write("g building_%04d\n" % i)
			for face in facesOutput:
				vertices = " ".join([str(x) for x in face])
				file_out.write("f %s\n" % vertices)
			file_out.write("\n")


X_AVG, Y_AVG, HEIGHT, footprints = parseXML(GML_FILE)
listofObjs = createDumbBuildings(footprints, START_POINT, NUM_BUILDINGS)
facesToOBJ(listofObjs, OUTPUT_OBJ_FILE, OUTPUT_OBJ_FOLDER, START_POINT)
print("%d buildings generated!" % len(listofObjs))
print("To make sure everything ran correctly, view the following file in Blender:")
print("%s" % OUTPUT_OBJ_FILE)