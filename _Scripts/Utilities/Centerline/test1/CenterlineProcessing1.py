#    NeuroMorph_Centerline_Procesing.py (C) 2018,  Anne Jorstad
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/

bl_info = {  
    "name": "NeuroMorph Centerline Processing",
    "author": "Anne Jorstad",
    "version": (1, 3, 0),
    "blender": (2, 7, 9),
    "location": "View3D > NeuroMorph > Centerline Processing",
    "description": "Process centerlines",
    "warning": "",  
    "wiki_url": "",  
    "tracker_url": "",  
    "category": "Tool"}  
  
import bpy
from bpy.props import *
import bmesh
from mathutils import Vector  
import mathutils
import math
import os
import sys
import re
from os import listdir
import copy
import numpy as np  # must have Blender > 2.7
import csv
import xml.etree.ElementTree as ET
import datetime


# Define the panel
class CenterlinePanel(bpy.types.Panel):
    bl_label = "Centerline Processing"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "NeuroMorph"

    def draw(self, context):

        row = self.layout.row()
        row.operator("object.preprocess_mesh", text='Clean Mesh for Processing', icon='MESH_UVSPHERE')

        self.layout.label("---------- Get Centerline (3 Methods) ----------")
        # 3 options:  use vmtk, generate approximation via 2 clicked points, or creating something completely by hand
        
        split = self.layout.row().split(percentage=0.1)
        col1 = split.column()
        col2 = split.column()
        col2.prop(context.scene, "npts_centerline")

        # Functions for VMTK command line, "mesh.vtp" from write_vtp, centerline.vtp for load_centerline
        # vmtkcenterlines -ifile mesh.vtp -ofile tmp.vtp; vmtksurfacewriter -mode ascii -ifile tmp.vtp -ofile centerline.vtp
        split1 = self.layout.row().split(percentage=0.07)
        col1a = split1.column()
        col2a = split1.column()
        col1a.label("M1:")
        split = col2a.split(percentage=0.5)
        col1 = split.column()
        col2 = split.column()
        col1.operator("object.write_vtp", text='Write Mesh to vtp', icon='FILESEL')
        col2.operator("object.load_centerline", text='Load Centerline from vtp', icon='FILESEL')
        
        split1 = self.layout.row().split(percentage=0.07)
        col1a = split1.column()
        col2a = split1.column()
        col1a.label("M2:")
        split = col2a.split(percentage=0.5)
        col1 = split.column()
        col2 = split.column()
        col1.operator("object.approx_centerline", text='Approximate Centerline', icon='MOD_CURVE')
        col2.operator("object.update_approx", text='Update Approx. Centerline', icon='MOD_CURVE')


        split1 = self.layout.row().split(percentage=0.07)
        col1a = split1.column()
        col2a = split1.column()
        col1a.label("M3:")
        col2a.operator("object.update_centerline", text='Use Selected Centerline', icon='MOD_CURVE')

        # Functions depending on centerline object in Blender
        self.layout.label("---------- Use Centerline ----------")

        split = self.layout.row().split(percentage=0.1)
        col1 = split.column()
        col2 = split.column()
        col2.prop(context.scene, "search_radius")

        row = self.layout.row()
        row.operator("object.get_surface_areas", text='Get Cross-sectional Surface Areas', icon='FACESEL_HLT')

        row = self.layout.row()
        row.operator("object.max_radii", text='Get Maximum Radius of each Cross Section', icon='FORCE_FORCE')

        row = self.layout.row()
        row.operator("object.project_vesicles", text='Project Spheres to Centerline', icon="FULLSCREEN_EXIT")

        row = self.layout.row()
        row.operator("object.project_areas", text='Project Surface Areas to Centerline', icon="FULLSCREEN_EXIT")

        row = self.layout.row()
        row.operator("object.write_ctrline_data", text='Write Centerline Data', icon='FILESEL')


        self.layout.label("---------- Detect Boutons ----------")
        split = self.layout.row().split(percentage=0.1)
        col1 = split.column()
        col2 = split.column()
        col2.prop(context.scene, "bouton_area_change")
        split = self.layout.row().split(percentage=0.1)
        col1 = split.column()
        col2 = split.column()
        col2.prop(context.scene, "bouton_distance_change")
        split = self.layout.row().split(percentage=0.1)
        col1 = split.column()
        col2 = split.column()
        col2.prop(context.scene, "bouton_max_rad")
        row = self.layout.row()
        row.operator("object.detect_boutons", text='Detect Boutons', icon="OUTLINER_DATA_META")  # OUTLINER_OB_META, MAN_SCALE

        row = self.layout.row()
        row.operator("object.select_volume", text='Get Axon Region Between Points', icon="MESH_CYLINDER")
        # PARTICLE_POINT, STICKY_UVS_VERT, CURVE_DATA, MESH_CYLINDER


        # self.layout.label("--Debugging--") 
        # row = self.layout.row()
        # row.operator("object.separate_spheres", text='Separate Vesicle Spheres')
        # row = self.layout.row()
        # row.operator("object.add_radii_spheres", text='Add radii spheres')
        

        # other icon options
        #centerline:  CURVE_DATA, OUTLINER_DATA_CURVE, OUTLINER_OB_CURVE, MOD_CURVE
        #cross-sectional areas:  FACESEL_HLT, SNAP_FACE, HAIR
        #vesicle projection:  FORCE_HARMONIC, FULLSCREEN_EXIT, STICKY_UVS_DISABLE




# class PreProcessMesh_hack(bpy.types.Operator):
#     """Attempt to clean up non-manifold mesh geometry of selected mesh"""
#     bl_idname = "object.preprocess_mesh_hack"
#     bl_label = "Clean non-manifold mesh geometry"

#     def execute(self, context):
#         mesh = bpy.context.object

#         # De-select all vertices
#         bpy.ops.object.mode_set(mode='EDIT')
#         bpy.ops.mesh.select_mode(type="VERT")
#         bpy.ops.mesh.select_all(action='DESELECT')
        
#         # Collapse non-manifold vertices
#         # non-manifold options:  can select "Vertices", which includes the edges 
#         #     that belong to 3 or more faces from Multple Faces, or leave all on
#         bpy.ops.mesh.select_non_manifold()
#         bpy.ops.mesh.merge(type='COLLAPSE')

#         # returns in edit mode, so can see points that were modified
#         return {'FINISHED'}



class ApproxCenterline(bpy.types.Operator):
    """Heuristic to provide approximate centerline (input mesh object with two endpoints selected)"""
    bl_idname = "object.approx_centerline"
    bl_label = "Heuristic to provide approximate centerline"

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        mesh = bpy.context.object
        
        convert_to_global_coords()

        pts = [v for v in mesh.data.vertices if v.select == True]
        if len(pts) != 2:
            self.report({'INFO'},"Must select exactly 2 endpoints")

        # Calculate the shortest path
        bpy.ops.object.mode_set(mode='EDIT')
        err = bpy.ops.mesh.shortest_path_select()  

        # Create new object from points, to be able to index linearly across curve
        obs_before = list(bpy.context.scene.objects)
        bpy.ops.mesh.duplicate_move()
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        obs_after = list(bpy.context.scene.objects)
        crv = [elt for elt in obs_after if elt not in obs_before][0]
        crv.name = "curve"

        # Reorder indices to be linear down curve
        select_obj(crv)
        bpy.ops.object.convert(target='CURVE')
        bpy.ops.object.convert(target='MESH')

        # Sample indices
        ninds = 25  # if cross sections are too close together, might intersect
        nverts = len(crv.data.vertices)
        delta = math.floor(nverts / (ninds - 1))
        inds = list(range(2, nverts, delta))
        inds.append(nverts-3)

        # Create cross sections at indices

        # Preconstruct kd tree to aid in trimming far away vertices (fast)
        nverts_mesh = len(mesh.data.vertices)
        kd_mesh = mathutils.kdtree.KDTree(nverts_mesh)
        for i1, v1 in enumerate(mesh.data.vertices):
            kd_mesh.insert(v1.co, i1)
        kd_mesh.balance()

        # Define material for cross sectional area slices
        mat = bpy.data.materials.new("cross_section_material")
        mat.diffuse_color = (0.0,1.0,1.0)

        # Interate down curve
        bpy.context.scene.search_radius *= 2
        t0 = datetime.datetime.now()
        for ind in inds:
            print(ind)
            this_area = get_cross_sectional_area(crv, ind, mesh, kd_mesh, self)  # not always correct, working here
        t3 = datetime.datetime.now()
        print("total time: ", t3-t0)
        bpy.context.scene.search_radius /= 2

        # Connect centroids of cross sections for approximate centerline
        ninds = len(crv.children)
        centers = []
        edges = []
        for ii, cross_section in enumerate(crv.children):
            centers.append(cross_section.data.polygons[0].center)
            if ii < (ninds-1):
                edges.append([ii,ii+1])  # todo:  missing one edge?

        # Delete crv and cross sections
        for cross_sec in crv.children:
            select_obj(cross_sec)
            bpy.ops.object.delete() 
        select_obj(crv)
        bpy.ops.object.delete() 

        # Create new mesh object
        mesh_data = bpy.data.meshes.new("centerline_approx")
        mesh_data.from_pydata(centers, edges, [])
        mesh_data.update()
        centerline_approx = bpy.data.objects.new("centerline_approx", mesh_data)

        # Link new object to scene
        scene = bpy.context.scene
        scene.objects.link(centerline_approx)
        select_obj(centerline_approx)

        # Add more centerline points and smooth
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.subdivide()
        bpy.ops.mesh.vertices_smooth()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}


class UpdateApproxCenterline(bpy.types.Operator):
    """After you have adjusted the approximate centerline by hand, add more points and smooth"""
    bl_idname = "object.update_approx"
    bl_label = "After you have adjusted the approximate centerline by hand, add more points and smooth"

    def execute(self, context):
        centerline = bpy.context.object

        # Add more centerline points and smooth
        while (len(centerline.data.vertices) < 1.1*(bpy.context.scene.npts_centerline/2)):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.subdivide()
            bpy.ops.mesh.vertices_smooth()
            bpy.ops.object.mode_set(mode='OBJECT')

        # Reorder indices to be linear down curve
        select_obj(centerline)
        bpy.ops.object.convert(target='CURVE')
        bpy.ops.object.convert(target='MESH')

        # Update number of centerline points
        bpy.context.scene.npts_centerline = len(centerline.data.vertices)

        # Instantiate data containers
        centerline["centerline_min_radii"] = []
        centerline["cross_sectional_areas"] = []
        centerline["centerline_max_radii"] = []
        centerline["vesicle_counts"] = []
        centerline["area_sums"] = []
        centerline["vesicle_list"] = []

        return {'FINISHED'}




class SelectVolume(bpy.types.Operator):
    """Extract axon region between the 2 selected centerline vertices or centerline balls (input: 2 centerline vertices or balls)"""
    bl_idname = "object.select_volume"
    bl_label = "Select Volume"

    def execute(self, context):

        # Define objects and centerline vertex indices
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_obs = [ob for ob in bpy.context.scene.objects if ob.select == True]
        if len(selected_obs) == 1:  # two vertices on centerline
            centerline = selected_obs[0]
            selected_verts = [v.index for v in centerline.data.vertices if v.select == True]
            vi1 = selected_verts[0]
            vi2 = selected_verts[1]
        elif len(selected_obs) == 2:  # two centerline marker balls
            small = 1e-6
            b1 = selected_obs[0]
            centerline = b1.parent.parent
            vc1 = b1.location
            vi1 = [v.index for v in centerline.data.vertices if get_dist(v.co, vc1) < small][0]
            b2 = selected_obs[1]
            vc2 = b2.location
            vi2 = [v.index for v in centerline.data.vertices if get_dist(v.co, vc2) < small][0]
        else:
            infostr = "Expecting input to be 2 selected centerline vertices or 2 selected centerline balls; detected more objects selected"
            self.report({'INFO'}, infostr)
            return {'FINISHED'}

        axon = centerline.parent


        # Make box around axon section
        # 1. Create planes at both ends
        plane1 = make_plane(centerline, vi1)  # todo: increase radius to be sure it's big enough?
        select_obj(plane1)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        plane2 = make_plane(centerline, vi2)
        select_obj(plane2)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.select_all(action='DESELECT')
        plane1.select = True
        plane2.select = True
        bpy.ops.object.join()  # now plane1 DNE
        box = bpy.context.object

        # 2. Create faces to join planes into a box
        for edge_ind in range(0,4):
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            box.data.edges[edge_ind].select = True
            box.data.edges[edge_ind+4].select = True
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.edge_face_add()

        # Intersect axon and box
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        axon.hide = False
        select_obj(axon)
        bpy.ops.object.duplicate()
        axon_sub = bpy.context.object
        select_obj(axon_sub)

        bool_mod = axon_sub.modifiers.new('modifier1', 'BOOLEAN')
        bool_mod.operation = 'INTERSECT'
        bool_mod.object = box
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier = 'modifier1')
        
        # Delete box, hide axon
        select_obj(box)
        bpy.ops.object.delete()
        axon.hide = True

        # Recalculate normals, return as active object
        select_obj(axon_sub)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        axon_sub.name = axon.name + "_bouton"

        return {'FINISHED'}



class DetectBoutons(bpy.types.Operator):
    """Mark centerline vertices corresponding to large cross-sectional radius or large cross-sectional area change over short distances along centerline\n(input: 1 centerline object, with cross-sections already calculated)"""
    bl_idname = "object.detect_boutons"
    bl_label = "Detect Boutons"

    def execute(self, context):
        centerline = bpy.context.object

        areas = centerline["cross_sectional_areas"]
        if len(areas) == 0:
            infostr = "No cross-sectional areas detected with this centerline, must get cross sectional surface areas first"
            self.report({'INFO'}, infostr)
            return {'FINISHED'}

        # Extract necessary variables
        lengths = get_length_along_crv(centerline)
        distance_change = bpy.context.scene.bouton_distance_change
        area_change_factor = bpy.context.scene.bouton_area_change
        area_change_factor_inv = 1/area_change_factor
        max_rad_thresh = bpy.context.scene.bouton_max_rad

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        nverts = len(centerline.data.vertices)

        # Define materials for increasing and decreasing markers
        mat_inc = bpy.data.materials.new("area_increase_material")
        mat_inc.diffuse_color = (0.0,1.0,0.0)
        mat_dec = bpy.data.materials.new("area_decrease_material")
        mat_dec.diffuse_color = (1.0,0.0,0.0)

        mat_rad = bpy.data.materials.new("max_rad_material")
        mat_rad.diffuse_color = (0.0, 0.0, 1.0)
        mat_rad.use_transparency=True
        mat_rad.transparency_method = 'Z_TRANSPARENCY'
        mat_rad.alpha = 0.33

        # Create empty child object of centerline, whose children will be the marker spheres
        sphere_parent = bpy.data.objects.new("SphereMarkers", None)
        bpy.context.scene.objects.link(sphere_parent)
        sphere_parent.parent = centerline

        # Get maximum radius of cross section at each centerline vertex
        max_rads = get_max_rad(centerline)

        # For each centerline vertex, detect points where ratio of change in area > area_change_factor and 
        # distance along centerline < distance_change
        # for v1 in range(0, nverts-1):
        for v1 in range(0, nverts):
            loc = centerline.data.vertices[v1].co

            # Mark points of large radius
            if max_rads[v1] > max_rad_thresh:
                add_sphere_at_loc(loc, distance_change/4, mat_rad, sphere_parent)

            if v1 < nverts-1:
                v1_area = areas[v1]
                v1_dist_start = lengths[v1]

                v2 = v1+1
                v2_dist = lengths[v2] - v1_dist_start
                while (v2_dist < distance_change):
                    v2_area = areas[v2]
                    area_rat = v2_area / v1_area
                    if area_rat > area_change_factor or area_rat < area_change_factor_inv:
                        centerline.data.vertices[v1].select = True
                        if area_rat > area_change_factor:
                            add_sphere_at_loc(loc, distance_change/6, mat_inc, sphere_parent)
                        if area_rat < area_change_factor_inv:
                            add_sphere_at_loc(loc, distance_change/6, mat_dec, sphere_parent)
                        break
                    v2 += 1
                    if v2 >= nverts:
                        break
                    v2_dist = lengths[v2] - v1_dist_start

        # Hide dotted line between parent and child objects
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].show_relationship_lines = False

        return {'FINISHED'}


def get_max_rad(centerline):
    children = centerline.children
    csa_names = [elt for elt in children if elt.name[0:20] == "cross-sectional area"]
    max_rads = []
    for csa in csa_names:
        # csa = bpy.context.scene.objects[this_name]
        verts = [v.co for v in csa.data.vertices]
        centroid = np.mean(verts, axis=0)
        dists = [get_dist(v, centroid) for v in verts]
        max_rads.append(max(dists))
    return(max_rads)



class CalcMaxRadii(bpy.types.Operator):
    """Calculate the maximum radius of each cross section (input: centerline object)"""
    bl_idname = "object.max_radii"
    bl_label = "Calculate the maximum radius of each cross section"

    def execute(self, context):
        centerline = bpy.context.object

        areas = centerline["cross_sectional_areas"]
        if len(areas) == 0:
            infostr = "No cross-sectional areas detected with this centerline, must get cross sectional surface areas first"
            self.report({'INFO'}, infostr)
            return {'FINISHED'}

        max_rads = get_max_rad(centerline)
        centerline["centerline_max_radii"] = max_rads

        return {'FINISHED'}





class PreProcessMesh(bpy.types.Operator):
    """Remove and fill non-manifold mesh geometry of selected mesh"""
    bl_idname = "object.preprocess_mesh"
    bl_label = "Clean non-manifold mesh geometry"

    def execute(self, context):
        mesh = bpy.context.object

        # De-select all vertices
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type="VERT")

        while (True):
            bpy.ops.mesh.select_all(action='DESELECT')

            # Select non-manifold vertices
            bpy.ops.mesh.select_non_manifold()

            # If no non-manifold points, check for hanging faces not detected by manifold tool
            bpy.ops.object.mode_set(mode='OBJECT')
            selected = [v for v in mesh.data.vertices if v.select]
            if len(selected) == 0:

                # Remove any vertices attached to <= 2 faces
                vert_table = faces_per_vertex(mesh)
                hanging_v_inds = [ind for ind, val in enumerate(vert_table) if val <= 2]

                # If all vertices are acceptable, exit loop
                if len(hanging_v_inds) == 0:
                    break
                else:
                    for ind in hanging_v_inds:
                        mesh.data.vertices[ind].select = True


            # Ensure vertex 0 is not about to be deleted (used later with select_linked)
            if mesh.data.vertices[0].select:
                print("Warning: about to delete vertex 0!")
            bpy.ops.object.mode_set(mode='EDIT')

            # Delete bad vertices
            bpy.ops.mesh.delete(type='VERT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.delete_loose()

            # Delete regions that have been disconnected from the main mesh
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            mesh.data.vertices[0].select = True  # this better be part of the main mesh!
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_linked()
            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='VERT')

            # Fill removed holes
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.region_to_loop()
            bpy.ops.mesh.edge_face_add()

        # Divide newly added faces into planar polys
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type="FACE")
        bpy.ops.object.mode_set(mode='OBJECT')
        big_faces = [f for f in mesh.data.polygons if len(f.vertices) > 4]
        for f in big_faces:
            f.select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.vert_connect_nonplanar(angle_limit=0)
        bpy.ops.mesh.select_mode(type="VERT")

        # Return mesh in edit mode with fixed regions highlighted
        return {'FINISHED'}



# Count the number of faces each vertex is a part of
def faces_per_vertex(ob):
    faces = ob.data.polygons
    vert_table = len(ob.data.vertices) * [0]
    for f in faces:
        for v in f.vertices:
            vert_table[v] += 1
    return vert_table


class RedefineCenterline(bpy.types.Operator):
    """Use selected centerline with selected mesh object (must click here after making any changes to centerline, will update Number of Centerline Points)"""
    bl_idname = "object.update_centerline"
    bl_label = "Use modified centerline"

    def execute(self, context):
        err, objs = assign_selected_objects(self)
        if err < 0:
            return {'FINISHED'}
        centerline, meshobj = objs

        # Check if centerline has been modified by hand
        unmodified = False
        nverts = len(centerline.data.vertices)
        if nverts == bpy.context.scene.npts_centerline:
            # if modifications result in original number of points, will assume no modifications
            unmodified = True

        else:
            # Delete minimum radius values, as no longer have a value 
            # for each centerline vertex
            centerline["centerline_min_radii"] = []

            # Instantiate/delete other data containers
            centerline["cross_sectional_areas"] = []
            centerline["centerline_max_radii"] = []
            centerline["vesicle_counts"] = []
            centerline["area_sums"] = []
            centerline["vesicle_list"] = []


        # Remove any centerline points that are outside obj
        inds_to_check = [nverts-1, nverts-2, nverts-3, 0, 1, 2]
        inds_to_delete = []
        for ind in inds_to_check:
            coord = centerline.data.vertices[ind].co
            if point_outside_mesh(coord, meshobj):
                inds_to_delete += [ind]

        activate_an_object(centerline)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        for ind in inds_to_delete:
            centerline.data.vertices[ind].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.object.mode_set(mode='OBJECT')

        if unmodified:  # also remove these points from min radii list
            rs = centerline["centerline_min_radii"]
            for ind in inds_to_delete:
                del rs[ind]
            centerline["centerline_min_radii"] = rs


        # Reorder vertices along curve to run from 0 to nverts
        activate_an_object(centerline)
        bpy.ops.object.convert(target='CURVE')
        bpy.ops.object.convert(target='MESH')

        # Reassign number of centerline points
        nverts = len(centerline.data.vertices)
        bpy.context.scene.npts_centerline = nverts

        return {'FINISHED'}


# Check if point is inside object
def point_outside_mesh(coord, ob):
    # if rays in all 6 directions from pt intersect ob, assume pt is inside ob, else is outside
    axes = [ mathutils.Vector((1,0,0)), mathutils.Vector((0,1,0)), mathutils.Vector((0,0,1)), \
             mathutils.Vector((-1,0,0)), mathutils.Vector((0,-1,0)), mathutils.Vector((0,0,-1)) ]
    coord = mathutils.Vector(coord)
    max_dist = 10000.0
    count = 0
    for axis in axes:  # send out rays, if cross this object in every direction, point is inside
        result,location,normal,index = ob.ray_cast(coord, coord+axis*max_dist)  # will error if ob in different layer
        if index != -1:
            count += 1
    if count < 6:
        return True
    else:
        return False



# Extract centerline and mesh object from selected objects (exactly 2 selected objects expected)
# Perform basic sanity checks
def assign_selected_objects(self):
    these_obs = [ob for ob in bpy.data.objects if ob.select]
    if len(these_obs) != 2:
        infostr = "Must select exactly 2 objects:  1 centerline and 1 surface mesh"
        self.report({'INFO'}, infostr)
        return(-1, [])
    centerline = [ob for ob in these_obs if len(ob.data.polygons) == 0]
    mesh_obj = [ob for ob in these_obs if len(ob.data.polygons) > 0]
    if len(centerline) == 0:
        infostr = "No centerline object selected (expecting curve, but faces detected)"
        self.report({'INFO'}, infostr)
        return(-1, [])
    if len(centerline) > 1:
        infostr = "Detected more than 1 potential centerline; second object must contain faces"
        self.report({'INFO'}, infostr)
        return(-1, [])
    centerline = centerline[0]
    mesh_obj = mesh_obj[0]
    nverts_centerline = len(centerline.data.vertices)
    if nverts_centerline != bpy.context.scene.npts_centerline:
        infostr = "Warning: centerline of " + str(bpy.context.scene.npts_centerline) + " points not selected"
        self.report({'INFO'}, infostr)
        # if nverts_centerline > bpy.context.scene.npts_centerline:
        #     return(-1, [])
    return(0, [centerline, mesh_obj])


class GetSurfaceAreas(bpy.types.Operator):
    """Get cross sectional areas from selected centerline and axon (input: 2 objects)"""
    bl_idname = "object.get_surface_areas"
    bl_label = "Get cross sectional areas from selected centerline and axon"

    def execute(self, context):

        # Extract centerline and mesh object from selected objects (exactly 2 selected objects expected)
        # centerline, meshobj = assign_selected_objects(self)
        err, objs = assign_selected_objects(self)
        if err < 0:
            return {'FINISHED'}
        centerline, meshobj = objs

        # Project objects so 3D coordinates are consistent
        convert_to_global_coords()

        # Preconstruct kd tree to aid in trimming far away vertices (fast)
        nverts_mesh = len(meshobj.data.vertices)
        kd_mesh = mathutils.kdtree.KDTree(nverts_mesh)
        for i1, v1 in enumerate(meshobj.data.vertices):
            kd_mesh.insert(v1.co, i1)
        kd_mesh.balance()

        # Define material for cross sectional area slices
        mat = bpy.data.materials.new("cross_section_material")
        mat.diffuse_color = (0.0,1.0,1.0)

        # Interate down centerline
        areas = []
        t0 = datetime.datetime.now()
        for ind in range(0, len(centerline.data.vertices)):
            print(ind)
            this_area = get_cross_sectional_area(centerline, ind, meshobj, kd_mesh, self)
            areas.append(this_area)
        t3 = datetime.datetime.now()
        print("total time: ", t3-t0)

        # Add areas to centerline object
        centerline["cross_sectional_areas"] = areas

        return {'FINISHED'}


def get_cross_sectional_area(centerline, ind, meshobj, kd_mesh, self):
# Create perpindicular plane to centerline at ind
# Get area of intersection of plane with mesh

    nverts_not_enough = 12

    plane = make_plane(centerline, ind)
    select_obj(plane)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    select_obj(meshobj)
    bpy.ops.object.duplicate()
    cross_section = bpy.context.object
    select_obj(cross_section)

    # # for debugging
    # cross_section = bpy.context.object
    # kd_mesh = mathutils.kdtree.KDTree(len(cross_section.data.vertices))
    # for i1, v1 in enumerate(cross_section.data.vertices):
    #     kd_mesh.insert(v1.co, i1)
    # 
    # kd_mesh.balance()

    # Delete vertices far away from centerline point
    ctrline_vert = centerline.data.vertices[ind].co
    rad = bpy.context.scene.search_radius  # distance is arbitrary
    close_pts = kd_mesh.find_range(ctrline_vert, rad)  # max_rad*4
    if len(close_pts) > 100:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type="VERT")  # need to be in vertex select mode for this to work
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        for cp in close_pts:
            ind = cp[1]  # vector, ind, dist
            cross_section.data.vertices[ind].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.object.mode_set(mode='OBJECT')
        select_obj(cross_section)
    else:
        print("found ", str(len(close_pts)), " close points, expecting more;  deleting nothing")
        x = crash  # deliberatly crash

    bpy.ops.object.duplicate()
    cross_section_backup = bpy.context.object
    select_obj(cross_section)

    # Cut mesh at plane, create new cross sectional face (can take a couple seconds)
    thresh = 1e-5
    apply_intersect(cross_section, plane, thresh = thresh)

    if len(cross_section.data.polygons) == 0 or len(cross_section.data.vertices) < nverts_not_enough:
        no_intersect_area = True
        thresh /= 10
        while (no_intersect_area):
            print("bad threshold? nverts =", str(len(cross_section.data.vertices)), ", trying thresh =", str(thresh))
            # Delete incorrect intersection object
            select_obj(cross_section)
            bpy.ops.object.delete() 
            cross_section = cross_section_backup
            select_obj(cross_section)
            # Copy a new backup object
            bpy.ops.object.duplicate()
            cross_section_backup = bpy.context.object
            select_obj(cross_section)
            # Try a smaller threshold
            apply_intersect(cross_section, plane, thresh = thresh)
            
            if thresh < 1e-10:
                thresh = 1e-4
            elif thresh >= 1e-4:
                thresh *= 10
            else:
                thresh /= 10

            if (len(cross_section.data.polygons) > 0 or 
                len(cross_section.data.vertices) < nverts_not_enough or 
                # thresh < 1e-10 or 
                thresh > 1e-2):
                    no_intersect_area = False
                    select_obj(cross_section_backup)
                    bpy.ops.object.delete() 
                    select_obj(cross_section)

    else:
        select_obj(cross_section_backup)
        bpy.ops.object.delete() 
        select_obj(cross_section)


    # # this second modifier isn't working
    # bool_mod = cross_section.modifiers.new('modifier2', 'BOOLEAN')
    # bool_mod.operation = 'DIFFERENCE'
    # bool_mod.object = plane
    # bpy.ops.object.modifier_apply(apply_as='DATA', modifier = 'modifier2')


    # Find area of new face with lots of verts
    # cap_inds = []
    big_poly_inds = []
    polys = cross_section.data.polygons
    for f_ind in range(0, len(polys)):
        this_face = polys[f_ind]
        if len(this_face.vertices) > 6:  # the cutting plane causes some quads to now have 5 edges, +1 for good measure
            big_poly_inds.append(f_ind)

    if len(big_poly_inds) == 1:
        # cap_ind = big_poly_inds[0]
        cap_inds = big_poly_inds


    elif len(big_poly_inds) > 1:
        print("Warning:  " + str(len(big_poly_inds)) + " polys with > 6 verts, making selection")
        # This can happen when axon bends with high curvature and the plane intersects the mesh twice,
        # or if there is a hole in the cross section, as individual faces cannot have holes, 
        # or if geometry is strange and the entire plane is kept:
        # find face closest to this centerline point;
        # if there is a hole, also find the other part of the cross section on the other side of the hole

        # Remove any faces that contains points on the original plane
        plane_verts = [v.co for v in plane.data.vertices]
        remove_inds = []
        break_flag = False
        for c_ind in big_poly_inds:
            break_flag = False
            for v_ind in polys[c_ind].vertices:
                if not break_flag:
                    this_vert = cross_section.data.vertices[v_ind].co
                    if any(get_dist(this_vert, pv) == 0 for pv in plane_verts):
                        remove_inds.append(c_ind)
                        break_flag = True
        for bad_ind in remove_inds:
            big_poly_inds.remove(bad_ind)

        # Save the face closest to the centerline point
        min_dist = 1000
        cap_ind = -1
        for c_ind in big_poly_inds:
            this_dist = get_dist(ctrline_vert, polys[c_ind].center)
            if this_dist < min_dist:
                min_dist = this_dist
                cap_ind = c_ind
        #print("chose face with center at ", polys[cap_ind].center)
        # this_area = polys[cap_ind].area
        
        # If cross section has a hole, the found cross section poly will not be complete, 
        # as single faces cannot have holes; check if there is another poly with >6 verts 
        # that shares at least 2 edges with found poly
        other_inds = [ii for ii in big_poly_inds if ii != cap_ind]
        cap_edges = polys[cap_ind].edge_keys
        cap_inds = [cap_ind]
        for o_ind in other_inds:
            poly2_edges = polys[o_ind].edge_keys
            overlapping_edges = set(poly2_edges).intersection(set(cap_edges))
            if len(overlapping_edges) >= 2:  # There is a hole, join this face!
                cap_inds.append(o_ind)
        # Now cap_inds is a list of >= 1 face index
        

    else:
        print("ERROR:  found no polys with > 6 verts, something went wrong <-- investigate")
        print(len(big_poly_inds), "/", len(cross_section.data.polygons))
        x = intentional_crash  # force crash

    # Create new object as child object of centerline
    new_face_ob = new_obj_from_polys(cross_section, cap_inds)
    new_face_ob.parent = centerline

    # Calculate area
    this_area = sum(polys[ii].area for ii in cap_inds)

    # Delete temporary plane object and mesh objects
    select_obj(plane)
    bpy.ops.object.delete()
    select_obj(cross_section)
    bpy.ops.object.delete()

    return(this_area)



def new_obj_from_polys(cross_section, cap_inds):
    # Create new cross-section object, often a single face (but not necessarily)
    select_obj(cross_section)
    ob_list_before = [ob_i for ob_i in bpy.data.objects if ob_i.type == 'MESH']
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for ii in cap_inds:
        cross_section.data.polygons[ii].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.duplicate_move()
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    ob_list_after = [ob_i for ob_i in bpy.data.objects if ob_i.type == 'MESH']
    new_face_ob = [ob for ob in ob_list_after if ob not in ob_list_before][0]
    new_face_ob.name = "cross-sectional area"
    mat = bpy.data.materials["cross_section_material"]
    new_face_ob.data.materials.append(mat)  # added for 2.79
    new_face_ob.material_slots[0].material = mat
    return(new_face_ob)


def apply_intersect(obj, plane, thresh = .0001):
# Cut mesh at plane, create new cross sectional face (can take a couple seconds)
    bool_mod = obj.modifiers.new('modifier1', 'BOOLEAN')
    bool_mod.operation = 'INTERSECT'
    bool_mod.object = plane
    bool_mod.double_threshold = thresh  # .0001? .00001? emperical; default e-7 sometimes returns just a few edges
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier = 'modifier1')



def make_plane(centerline, ind):
    # Create plane perpendicular to centerline at vertex ind
    # Side length half length of centerline, arbitrary
    # rad = max(2*max_rad, get_dist(centerline.data.vertices[0].co, centerline.data.vertices[-1].co) / 8)
    rad = bpy.context.scene.search_radius
    
    # Calculate weighted average of two prior and two next normals
    p0 = centerline.data.vertices[ind].co

    if ind == 0 or ind == 1:
        p_1 = centerline.data.vertices[1].co
        p_0 = centerline.data.vertices[0].co
        norm_m1 = p_1 - p_0
        norm_m2 = norm_m1
    else:
        pm1 = centerline.data.vertices[ind-1].co
        pm2 = centerline.data.vertices[ind-2].co
        norm_m1 = p0 - pm1
        norm_m2 = pm1 - pm2

    N = len(centerline.data.vertices)
    if ind == N-1 or ind == N-2:
        p_N = centerline.data.vertices[N-1].co
        p_Nm1 = centerline.data.vertices[N-2].co
        norm_p1 = p_N - p_Nm1
        norm_p2 = norm_p1
    else:
        pp1 = centerline.data.vertices[ind+1].co
        pp2 = centerline.data.vertices[ind+2].co
        norm_p1 = pp1 - p0
        norm_p2 = pp2 - pp1

    norm_m1 = Vector(norm_m1 / np.linalg.norm(norm_m1))
    norm_m2 = Vector(norm_m2 / np.linalg.norm(norm_m2))
    norm_p1 = Vector(norm_p1 / np.linalg.norm(norm_p1))
    norm_p2 = Vector(norm_p2 / np.linalg.norm(norm_p2))
    norm_here = (norm_m1+norm_p1+norm_m2/2+norm_p2/2) / 3

    # Construct plane, assign normal
    bpy.ops.mesh.primitive_plane_add(location = p0, radius = rad)
    plane = bpy.context.object
    plane.rotation_mode = 'QUATERNION'
    plane.rotation_quaternion = norm_here.to_track_quat('Z','Y')

    return(plane)



class RadiiSpheres(bpy.types.Operator):
    """Add radii spheres to selected centerline"""
    bl_idname = "object.add_radii_spheres"
    bl_label = "Add radii spheres to selected centerline"

    def execute(self, context):
        # centerline = bpy.data.objects["centerline"]
        centerline = bpy.context.object
        convert_to_global_coords()
        rs = centerline["centerline_min_radii"]
        print(len(centerline.data.vertices), len(rs))
        step = 1
        for ind in range(0,len(rs), step):
            loc = centerline.data.vertices[ind].co
            rad = rs[ind]
            add_sphere_at_loc(loc, rad, [], [])
        return {'FINISHED'}


def add_sphere_at_loc(loc, rad, mat, parent):
    # assumes image is selected?
    bpy.ops.mesh.primitive_uv_sphere_add(location=loc, size=rad)
    obj = bpy.context.object
    if mat == []:
        mat = bpy.data.materials.new("sphere_material")
        mat.diffuse_color = (1.0, 0.3, 0.0)
        mat.use_transparency=True
        mat.transparency_method = 'Z_TRANSPARENCY'
        mat.alpha = 0.5
    obj.active_material = mat
    obj.show_transparent = True
    obj.name = "sphere"  # "marker"

    

    if parent != []:
        obj.parent = parent

    # turn off origin marker
    bpy.context.space_data.show_manipulator = False



def find_ind_closest_dist(dists, ind_start, dist_to_match):
    min_dist = abs(dists[ind_start] - dist_to_match)
    min_dist_ind = ind_start
    for ind in range(ind_start+1, len(dists)):
        this_dist = abs(dists[ind] - dist_to_match)
        if this_dist < min_dist:
            min_dist = this_dist
            min_dist_ind = ind
    return(min_dist_ind)


def construct_curve(verts, name):
    mesh = bpy.data.meshes.new(name)
    ctrline_obj = bpy.data.objects.new(name, mesh)
    # ctrline_obj.location = obj_ptr.location  # probably not necessary
    # ctrline_obj.scale = obj_ptr.scale
    # ctrline_obj.rotation_euler = obj_ptr.rotation_euler
    bpy.context.scene.objects.link(ctrline_obj)
    edges = [[ii,ii+1] for ii in range(0,len(verts)-1)]
    mesh.from_pydata(verts, edges, [])
    mesh.update()  #calc_edges=True)
    return(ctrline_obj)


# Convert objects to global coordinates, call this in all functions to be safe
def convert_to_global_coords(these_obs = []):
    selected_ob = bpy.context.object
    activate_an_object()
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    if these_obs == []:
        these_obs = bpy.context.scene.objects
    for ob in these_obs:
        select_obj(ob)
        if ob.type == 'MESH' and hasattr(ob, 'data') and ob.location != Vector([0.0,0.0,0.0]):
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    select_obj(selected_ob)


# Count number of vesicles that project to each centerline point
class ProjectVesicles(bpy.types.Operator):
    """Project centers of distinct spheres (vesicles) of selected mesh object onto selected centerline object (input: 2 objects)"""
    bl_idname = "object.project_vesicles"
    bl_label = "Project vesicle spheres onto centerline"

    # directory = bpy.props.StringProperty(subtype="FILE_PATH")
    # filename = bpy.props.StringProperty(subtype="FILE_NAME")

    def execute(self, context):
        # full_filename = define_filename(self, ".csv")

        # Assign centerline and vesicle object from selected objects
        err, objs = assign_selected_objects(self)
        if err < 0:
            return {'FINISHED'}
        centerline, vesicle_obj = objs

        # Convert to global coords
        convert_to_global_coords()

        # if len(bpy.context.scene.vesicle_list) == 0:
        if len(centerline["vesicle_list"]) == 0:
            print("computing vesicle list...")
            vesicle_list = get_vesicle_list(vesicle_obj)
            centerline["vesicle_list"] = vesicle_list
        else:
            print("loading vesicle list...")
            vesicle_list = centerline["vesicle_list"]

        vcounts = proj_vesicles(centerline, vesicle_list)
        centerline["vesicle_counts"] = vcounts

        return {'FINISHED'}


# Count number of vesicles that project to each centerline point
class ProjectAreas(bpy.types.Operator):
    """Project surface area regions of selected mesh object onto selected centerline object (input: 2 objects)"""
    bl_idname = "object.project_areas"
    bl_label = "Project surface areas onto centerline"

    def execute(self, context):

        # Assign centerline and vesicle object from selected objects
        err, objs = assign_selected_objects(self)
        if err < 0:
            return {'FINISHED'}
        centerline, area_obj = objs

        # Convert to global coords
        convert_to_global_coords()

        # Project each polygon of area_obj into centerlne
        vsums = proj_areas(centerline, area_obj)
        centerline["area_sums"] = vsums

        return {'FINISHED'}


class SeparateSpheres(bpy.types.Operator):
    """Separate Spheres of selected object"""
    bl_idname = "object.separate_spheres"
    bl_label = "Separate Spheres of selected object"

    def execute(self, context):
        vesicle_obj = bpy.context.object

        convert_to_global_coords([vesicle_obj.parent, vesicle_obj])
        # for ob in [vesicle_obj.parent, vesicle_obj]:
        #     # bpy.ops.object.select_all(action='DESELECT')
        #     # bpy.context.scene.objects.active = ob
        #     # ob.select = True  # necessary
        #     select_obj(ob)
        #     bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        vesicle_list = get_vesicle_list(vesicle_obj)
        axon = vesicle_obj.parent
        axon["vesicle_list"] = vesicle_list
        return {'FINISHED'}


def get_vesicle_list(vesicle_obj):
    # separate by loose parts converts vesicle mass to separate spheres, then make list of sphere center points
    
    # Deselect everything but the vesicle object
    activate_an_object()
    bpy.ops.object.mode_set(mode='OBJECT')
    # bpy.ops.object.select_all(action='DESELECT')
    # bpy.context.scene.objects.active = vesicle_obj
    # vesicle_obj.select = True
    select_obj(vesicle_obj)
    bpy.ops.object.duplicate()  # operate on copy of obj instead
    vesicle_obj_copy = bpy.context.object
    vesicle_obj_copy.parent = vesicle_obj
    ob_list_before = vesicle_obj.children
    select_obj(vesicle_obj_copy)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Separate the object into loose parts, ie separate spheres
    t1 = datetime.datetime.now()
    bpy.ops.mesh.separate(type='LOOSE')  # slow
    t2 = datetime.datetime.now()
    print("\nTime to separate spheres: ", t2-t1)

    ob_list_after = vesicle_obj.children
    vesicle_list = [ob.name for ob in ob_list_after if (ob not in ob_list_before or ob.name == vesicle_obj_copy.name)]

    # vesicle_list = [ob.name for ob in bpy.context.scene.objects if ob.select == True]  # replaces original vesicle_obj
    return (vesicle_list)


# Return centerpoint of object, defined as mean vertex value
def calc_center(obj):
    v_sum = Vector([0,0,0])
    for v in obj.data.vertices:
        v_sum += v.co
    ctrpt = v_sum / len(obj.data.vertices)
    return(ctrpt)


# Calculate center point of each vesicle (todo: or closest point on surface?)
# Find closest point on centerline to each vesicle center point
# Tally vesicles per centerline vertex
def proj_vesicles(ctrline, vesicle_list):
    nverts = len(ctrline.data.vertices)
    kdt = mathutils.kdtree.KDTree(nverts)
    for ii, vv in enumerate(ctrline.data.vertices):
        kdt.insert(vv.co, ii)
    kdt.balance()

    vcounts = [0] * nverts  # count number vesicles that project to each point
    for vsc_name in vesicle_list:
        vsc_obj = bpy.context.scene.objects[vsc_name]
        vsc_ctr = calc_center(vsc_obj)  # center point of vsc mesh

        # calculate closest ctrline point to center point
        ctrline_co, ii, dist = kdt.find(vsc_ctr)
        #print(vsc_name, dist, ii, vcounts[ii])
        vcounts[ii] += 1

    return (vcounts)

# Same as above, but looping over single mesh object, adding area of each poly
def proj_areas(ctrline, area_obj):
    nverts = len(ctrline.data.vertices)
    kdt = mathutils.kdtree.KDTree(nverts)
    for ii, vv in enumerate(ctrline.data.vertices):
        kdt.insert(vv.co, ii)
    kdt.balance()

    vcounts = [0] * nverts  # count number vesicles that project to each point
    for poly in area_obj.data.polygons:
        this_area = poly.area
        this_ctr = poly.center
        ctrline_co, ii, dist = kdt.find(this_ctr)
        vcounts[ii] += this_area

    return (vcounts)


# Calculates distance along verts (assumed ordered in a curve) from ind0 to each point
def get_length_along_vert_list(verts):
    nverts = len(verts)
    dists = [0] * nverts
    dist_cur = 0
    for ii in range(1,nverts):
        d_here = get_dist(verts[ii-1], verts[ii])
        dist_cur += d_here
        dists[ii] = dist_cur
    return (dists)

def get_length_along_crv(mesh_crv):
    verts = [v.co for v in mesh_crv.data.vertices]
    dists = get_length_along_vert_list(verts)
    return (dists)


class WriteVTP(bpy.types.Operator):
    """Write selected mesh to vtp file format"""
    bl_idname = "object.write_vtp"
    bl_label = "Write selected mesh to vtp file format"

    directory = bpy.props.StringProperty(subtype="FILE_PATH")
    filename = bpy.props.StringProperty(subtype="FILE_NAME")

    def invoke(self, context, event):
        WindowManager = context.window_manager
        WindowManager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        full_filename = define_filename(self, ".vtp")

        # Write actively selected object
        mesh = bpy.context.object
        
        # Convert to global coordinates
        convert_to_global_coords()

        # Construct vtp data, where each vertex of each poly is a new point
        pts_text = ""
        norm_text = ""
        connectivity_text = ""
        offsets_text = ""
        vert_sum = 0
        pt_ind = 0
        min_pts = 1e+299
        max_pts = -1e+299
        min_norm = 1e+299
        max_norm = -1e+299
        min_poly = len(mesh.data.polygons[0].vertices)
        npolys = len(mesh.data.polygons)
        for poly in mesh.data.polygons:
            nverts = len(poly.vertices)
            norm = poly.normal
            norm_str = str(norm[0]) + " " + str(norm[1]) + " " + str(norm[2]) + " "
            vert_sum += nverts
            offsets_text += str(vert_sum) + " "
            for v_ind in range(0,nverts):
                vert_co = mesh.data.vertices[poly.vertices[v_ind]].co
                pts_text += str(vert_co[0]) + " " + str(vert_co[1]) + " " + str(vert_co[2]) + " "
                norm_text += norm_str
                connectivity_text += str(pt_ind) + " "
                pt_ind += 1
            this_norm = norm.length
            if this_norm > max_norm:
                max_norm = this_norm
            if this_norm < min_norm:
                min_norm = this_norm
        for pt in mesh.data.vertices:
            this_pt_norm = get_dist(pt.co, [0,0,0])
            if this_pt_norm > max_pts:
                max_pts = this_pt_norm
            if this_pt_norm < min_pts:
                min_pts = this_pt_norm
        npts = pt_ind

        # Define the xml element structure
        VTKFile = ET.Element("VTKFile", attrib={"type":"PolyData", "version":"0.1", "byte_order":"LittleEndian", "header_type":"UInt32", "compressor":"vtkZLibDataCompressor"})
        PolyData = ET.SubElement(VTKFile, "PolyData")
        Piece = ET.SubElement(PolyData, "Piece", attrib={"NumberOfPoints":str(npts), "NumberOfVerts":"0", "NumberOfLines":"0", "NumberOfStrips":"0", "NumberOfPolys":str(npolys)})
        PointData = ET.SubElement(Piece, "PointData", attrib={"Normals":"Normals_"})
        CellData = ET.SubElement(Piece, "CellData")
        Points = ET.SubElement(Piece, "Points")
        Verts = ET.SubElement(Piece, "Verts")
        Lines = ET.SubElement(Piece, "Lines")
        Strips = ET.SubElement(Piece, "Strips")
        Polys = ET.SubElement(Piece, "Polys")

        # The four elements that hold data
        DataArray_norm = ET.SubElement(PointData, "DataArray", attrib={"type":"Float32", "Name":"Normals_", "NumberOfComponents":"3", "format":"ascii", "RangeMin":str(min_norm), "RangeMax":str(max_norm)})
        DataArray_pts = ET.SubElement(Points, "DataArray", attrib={"type":"Float32", "Name":"Points", "NumberOfComponents":"3", "format":"ascii", "RangeMin":str(min_pts), "RangeMax":str(max_pts)})
        DataArray_connectivity = ET.SubElement(Polys, "DataArray", attrib={"type":"Int64", "Name":"connectivity", "format":"ascii", "RangeMin":"0", "RangeMax":str(npts-1)})
        DataArray_offsets = ET.SubElement(Polys, "DataArray", attrib={"type":"Int64", "Name":"offsets", "format":"ascii", "RangeMin":str(min_poly), "RangeMax":str(npts)})
        DataArray_pts.text = pts_text
        DataArray_norm.text = norm_text
        DataArray_connectivity.text = connectivity_text
        DataArray_offsets.text = offsets_text

        # Other unused elements
        DataArray_NA1 = ET.SubElement(Verts, "DataArray", attrib={"type":"Int64", "Name":"connectivity", "format":"ascii", "RangeMin":"1e+299", "RangeMax":"-1e+299"})
        DataArray_NA2 = ET.SubElement(Verts, "DataArray", attrib={"type":"Int64", "Name":"offsets", "format":"ascii", "RangeMin":"1e+299", "RangeMax":"-1e+299"})
        DataArray_NA3 = ET.SubElement(Lines, "DataArray", attrib={"type":"Int64", "Name":"connectivity", "format":"ascii", "RangeMin":"1e+299", "RangeMax":"-1e+299"})
        DataArray_NA4 = ET.SubElement(Lines, "DataArray", attrib={"type":"Int64", "Name":"offsets", "format":"ascii", "RangeMin":"1e+299", "RangeMax":"-1e+299"})
        DataArray_NA5 = ET.SubElement(Strips, "DataArray", attrib={"type":"Int64", "Name":"connectivity", "format":"ascii", "RangeMin":"1e+299", "RangeMax":"-1e+299"})
        DataArray_NA6 = ET.SubElement(Strips, "DataArray", attrib={"type":"Int64", "Name":"offsets", "format":"ascii", "RangeMin":"1e+299", "RangeMax":"-1e+299"})
        # ET.dump(VTKFile)

        tree = ET.ElementTree(VTKFile)
        # tree.write("/home/anne/Desktop/test_write.vtp", xml_declaration=True)
        tree.write(full_filename, xml_declaration=True)

        return {'FINISHED'}




class LoadCenterline(bpy.types.Operator):
    """Load centerline from vtp file"""
    bl_idname = "object.load_centerline"
    bl_label = "Load centerline from vtp file"

    directory = bpy.props.StringProperty(subtype="FILE_PATH")
    filename = bpy.props.StringProperty(subtype="FILE_NAME")

    def invoke(self, context, event):
        WindowManager = context.window_manager
        WindowManager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        activate_an_object()
        bpy.ops.object.mode_set(mode='OBJECT')  # else is error at end

        this_filename = self.directory + self.filename

        # Load centerline data into mesh object
        #verts, rs = read_csv(bpy.context.scene.ctrline_data_file)
        verts, rs = read_vtp(this_filename)

        subsample_curve = True
        if subsample_curve:
            dists = get_length_along_vert_list(verts)
            len_ctrln = dists[-1]
            npts = bpy.context.scene.npts_centerline  # eg 200
            delta = len_ctrln / (npts-1)

            # Sample points along centerline a distance delta apart 
            inds_to_keep = set([0])
            ind_prev = 0
            len_cur = delta
            while len_cur < len_ctrln:
                ind_prev = find_ind_closest_dist(dists, ind_prev, len_cur)
                inds_to_keep.add(ind_prev)
                len_cur += delta
            inds_to_keep.add(len(dists)-1)
            inds_to_keep = sorted(list(inds_to_keep))

            # Construct new curve with only these points
            verts_sub = [verts[ind] for ind in inds_to_keep]
            rs = [rs[ind] for ind in inds_to_keep]
            ctrline_obj = construct_curve(verts_sub, "centerline")

            nverts_final = len(ctrline_obj.data.vertices)
            if (nverts_final != npts):
                infostr = "Warning:  Incorrect number of centerline points created, value updated."
                self.report({'INFO'}, infostr)
                bpy.context.scene.npts_centerline = nverts_final
            
        else:
            ctrline_obj = construct_curve(verts, "centerline")
            bpy.context.scene.npts_centerline = len(ctrline_obj.data.vertices)

        # Load radii values into scene variable
        # # for r in rs:
        # #    bpy.context.scene.centerline_min_radii.add().name = r  # they are now string values
        ctrline_obj["centerline_min_radii"] = rs

        # Instantiate other data containers
        ctrline_obj["cross_sectional_areas"] = []
        ctrline_obj["centerline_max_radii"] = []
        ctrline_obj["vesicle_counts"] = []
        ctrline_obj["area_sums"] = []
        ctrline_obj["vesicle_list"] = []

        # Return active object
        bpy.context.scene.objects.active = ctrline_obj
        ctrline_obj.select = True

        convert_to_global_coords()  # probably not necessary here

        return {'FINISHED'}


# Read 2D curve from vtp file
def read_vtp(filename):
    # Read vtp centerline file saved in ascii mode, assumes data to be single ordered curve
    # If data is not single ordered curve, must also load connectivity data:
    #   connectivity_elt = [elt for elt in root.findall('.//DataArray') if elt.attrib['Name']=="connectivity"][0]
    #   connectivity = (np.fromstring(connectivity_elt.text, sep=' ', dtype=int))
    tree = ET.parse(filename)
    root = tree.getroot()
    min_rad_elt = [elt for elt in root.findall('.//DataArray') if elt.attrib['Name']=="MaximumInscribedSphereRadius"][0]
    points_elt = [elt for elt in root.findall('.//DataArray') if elt.attrib['Name']=="Points"][0]
    min_rad = list(np.fromstring(min_rad_elt.text, sep=' '))
    points = list(np.fromstring(points_elt.text, sep=' '))
    points_xyz = [[points[ii], points[ii+1], points[ii+2]] for ii in range(0,len(points), 3)]
    # points_xyz_reordered = [[p[0], -p[2], p[1]] for p in points_xyz]  # if went through paraview
    points_xyz_reordered = [[p[0], p[1], p[2]] for p in points_xyz]  # if used local vtp writer for mesh
    return(points_xyz_reordered, min_rad)


# Write data to file 
def write_data(lengths, minradii, areas, maxradii, vcounts, area_sums, full_filename, self):
    # directory = bpy.props.StringProperty(subtype="FILE_PATH")
    # filename = bpy.props.StringProperty(subtype="FILE_NAME")
    outfile = open(full_filename, 'w')

    outfile.write("distance along curve")
    if len(minradii) > 0:
        outfile.write(";minimum radius at vertex")
    if len(areas) > 0:
        outfile.write(";cross-sectional area at vertex")
    if len(maxradii) > 0:
        outfile.write(";maximum radius at vertex")
    if len(vcounts) > 0:
        outfile.write(";number of spheres (vesicles) closest to this vertex")
    if len(area_sums) > 0:
        outfile.write(";sum of surface areas projected to this vertex")
    outfile.write("\n\n")
    for v_ind in range(0, len(lengths)):
        outfile.write(str(lengths[v_ind]))
        if len(minradii) > 0:
            outfile.write(";" + str(minradii[v_ind]))
        if len(areas) > 0:
            outfile.write(";" + str(areas[v_ind]))
        if len(maxradii) > 0:
            outfile.write(";" + str(maxradii[v_ind]))
        if len(vcounts) > 0:
            outfile.write(";" + str(vcounts[v_ind]))
        if len(area_sums) > 0:
            outfile.write(";" + str(area_sums[v_ind]))
        outfile.write("\n")

    outfile.close()
    self.report({'INFO'}, "Finished exporting file.")



class WriteCtrlineData(bpy.types.Operator):
    """Write all calculated data of selected centerline"""
    bl_idname = "object.write_ctrline_data"
    bl_label = "Write data of selected centerline"

    directory = bpy.props.StringProperty(subtype="FILE_PATH")
    filename = bpy.props.StringProperty(subtype="FILE_NAME")

    def invoke(self, context, event):
        # Check if active object is a centerline with centerline data attached
        if (("centerline_min_radii" not in bpy.context.object) and 
            ("cross_sectional_areas" not in bpy.context.object)):
                self.report({'INFO'}, "Must select Centerline object for exporting.")
                return {'FINISHED'}

        # Define export file
        WindowManager = context.window_manager
        WindowManager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        full_filename = define_filename(self, ".csv")

        # Assumes active object is centerline object (checked in invoke())
        centerline = bpy.context.object
        convert_to_global_coords()

        lengths = get_length_along_crv(centerline)
        minradii = centerline["centerline_min_radii"]  # might be []
        areas = centerline["cross_sectional_areas"]  # might be []
        maxradii = centerline["centerline_max_radii"]  # might be []
        vcounts = centerline["vesicle_counts"]  # might be []
        area_sums = centerline["area_sums"]  # might be []

        write_data(lengths, minradii, areas, maxradii, vcounts, area_sums, full_filename, self)
        return {'FINISHED'}



def define_filename(self, filetype):
    directory = self.directory
    filename = self.filename
    full_filename = os.path.join(directory, filename)
    if full_filename[-4:] != filetype:
        full_filename += filetype
    return (full_filename)


def select_obj(ob):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = ob
    ob.select = True  # necessary


def get_dist(coord1, coord2):  # distance is monotonic, take square root at end for efficiency
    d = math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2 + (coord1[2] - coord2[2])**2)
    return d

# Sometimes this is necessary before changing modes
def activate_an_object(ob_0=[]):
    tmp = [ob_0 for ob_0 in bpy.data.objects if ob_0.type == 'MESH' and ob_0.hide == False][0]
    bpy.context.scene.objects.active = tmp  # required before setting object mode

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    if ob_0 == []:
        ob_0 = [ob_0 for ob_0 in bpy.data.objects if ob_0.type == 'MESH' and ob_0.hide == False][0]
    bpy.context.scene.objects.active = ob_0
    ob_0.select = True


if __name__ == "__main__":
    register()

def register():
    bpy.utils.register_module(__name__)

    bpy.types.Scene.npts_centerline = bpy.props.IntProperty \
    (
        name="Number of Centerline Points",
        description = "Number of points used to construct centerline (default: 200), do not change after centerline is defined", 
        default=200
    )

    bpy.types.Scene.search_radius = bpy.props.FloatProperty \
    (
        name="Search Radius around Centerline Point",
        description = "Size of planes and local mesh region to include when searching for axon-plane intersection", 
        default=1.0  # needed 1.67 once
    )

    bpy.types.Scene.bouton_distance_change = bpy.props.FloatProperty \
    (
        name="Distance for Area Change",
        description = "Distance along centerline in which the cross-sectional area must change by a certain ratio to detect a bouton\n(centerline vertices marked with green/red spheres)", 
        default=0.2
    )

    bpy.types.Scene.bouton_area_change = bpy.props.FloatProperty \
    (
        name="Area Change (ratio)",
        description = "Ratio change in cross-sectional area, along set distance, that detects a bouton\n(centerline vertices marked with green/red spheres)", 
        default=1.3
    )

    bpy.types.Scene.bouton_max_rad = bpy.props.FloatProperty \
    (
        name="Minimum Max Radius",
        description = "Maximum radius of cross section must be at least this large to detect a bouton\n(centerline vertices marked with blue spheres)", 
        default=0.2
    )


def unregister():

    del bpy.types.Scene.bouton_max_rad
    del bpy.types.Scene.bouton_area_change
    del bpy.types.Scene.bouton_distance_change
    del bpy.types.Scene.search_radius
    del bpy.types.Scene.npts_centerline

    bpy.utils.unregister_module(__name__)

