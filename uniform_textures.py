bl_info = {
    "name": "Uniform_textures",
    "author": "eelh",
    "version": (0, 1),
    "blender": (2, 93, 1),
    "category": "Object",
    "location": "3D Viewport -> UI",
    "description": "Uniform textures",
}


import bmesh
import bpy
import math
import random


class UniformTexturesPanel(bpy.types.Panel):
    """Creates a Panel in 3D viewport properties"""
    bl_idname = "VIEW_3D_PT_uniform_textures"
    bl_label = "Uniform textures"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Uniform textures"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Uniform UVs scale")

        col = layout.column(align=True)
        col.operator("uniform_textures.make_uniform_all", text="For visible faces")

        col = layout.column(align=True)
        col.operator("uniform_textures.make_uniform_sel", text="For selected faces")


class MakeUniformAll(bpy.types.Operator):
    bl_idname = "uniform_textures.make_uniform_all"
    bl_label = "Make uniform"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Make textures uniform for visible islands."

    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        return active_object is not None \
               and active_object.type == 'MESH' \
               and active_object.select_get() \
               and context.mode == 'EDIT_MESH'

    def execute(self, context):
        obj = bpy.context.object
        mesh = obj.data
        paths = {v.index: set() for v in mesh.vertices}
        for e in mesh.edges:
            paths[e.vertices[0]].add(e.vertices[1])
            paths[e.vertices[1]].add(e.vertices[0])
        lparts = []
        while True:
            try:
                i = next(iter(paths.keys()))
            except StopIteration:
                break
            lpart = {i}
            cur = {i}
            while True:
                eligible = {sc for sc in cur if sc in paths}
                if not eligible:
                    break
                cur = {ve for sc in eligible for ve in paths[sc]}
                lpart.update(cur)
                for key in eligible: paths.pop(key)
            lparts.append(lpart)

        bm = bmesh.from_edit_mesh(obj.data)

        for island in lparts:
            # Find a face for an island
            bpy.ops.mesh.select_all(action='DESELECT')
            ind = island.pop()
            if not bm.verts[ind].hide:
                bpy.ops.mesh.select_mode(type='VERT')
                bm.verts[ind].select = True
                bpy.ops.mesh.select_linked()
                # bpy.ops.mesh.select_more()
                bpy.ops.mesh.select_mode(type='FACE')
                face = None
                for f in bm.faces:
                    if f.select:
                        bpy.ops.mesh.select_all(action='DESELECT')
                        f.select = True
                        bm.faces.active = f
                        face = f
                        break
                if len(face.verts) == 4:
                    bpy.ops.uv.reset()
                    bpy.ops.mesh.select_linked()
                    bpy.ops.uv.follow_active_quads(mode='LENGTH_AVERAGE')

                    sel_vert = face.edges[0].verts[0]
                    edges = []
                    for edge in face.edges:
                        for vert in edge.verts:
                            if vert == sel_vert:
                                edges.append(edge)

                    uv_layer = bm.loops.layers.uv.verify()

                    # scale UVs
                    for f in bm.faces:
                        if f.select:
                            for l in f.loops:
                                l[uv_layer].uv.x *= edges[0].calc_length() * 100
                                l[uv_layer].uv.y *= edges[1].calc_length() * 100

                else:
                    bpy.ops.mesh.select_linked()
                    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
                    bpy.ops.mesh.select_mode(type='EDGE')
                    bpy.ops.mesh.region_to_loop()
                    edge_len = 0
                    for edge in bm.edges:
                        if edge.select:
                            edge_len = edge.calc_length()*100
                            break
                    edge_count = bpy.context.active_object.data.total_edge_sel
                    chord = math.sin(math.radians(180/edge_count))
                    scale = edge_len/chord
                    uv_layer = bm.loops.layers.uv.verify()
                    bpy.ops.mesh.select_linked()
                    for f in bm.faces:
                        if f.select:
                            for l in f.loops:
                                    l[uv_layer].uv *= scale

        return {'FINISHED'}


class MakeUniform(bpy.types.Operator):
    bl_idname = "uniform_textures.make_uniform_sel"
    bl_label = "Make uniform"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Make textures uniform for selected faces."

    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        return active_object is not None \
               and active_object.type == 'MESH' \
               and active_object.select_get() \
               and context.mode == 'EDIT_MESH'

    def execute(self, context):

        obj = bpy.context.object
        bm = bmesh.from_edit_mesh(obj.data)

        bpy.ops.mesh.select_mode(type='FACE')
        selfaces = [f for f in bm.faces if f.select]
        for face in selfaces:
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_mode(type='VERT')
            face.select = True
            bm.faces.active = face
            bpy.ops.mesh.select_mode(type='FACE')
            if len(face.verts) == 4:
                bpy.ops.uv.reset()
                bpy.ops.mesh.select_linked()
                bpy.ops.uv.follow_active_quads(mode='LENGTH_AVERAGE')

                sel_vert = face.edges[0].verts[0]
                edges = []
                for edge in face.edges:
                    for vert in edge.verts:
                        if vert == sel_vert:
                            edges.append(edge)

                uv_layer = bm.loops.layers.uv.verify()

                # scale UVs
                for f in bm.faces:
                    if f.select:
                        for l in f.loops:
                            l[uv_layer].uv.x *= edges[0].calc_length() * 100
                            l[uv_layer].uv.y *= edges[1].calc_length() * 100

            else:
                bpy.ops.mesh.select_linked()
                bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
                bpy.ops.mesh.select_mode(type='EDGE')
                bpy.ops.mesh.region_to_loop()
                edge_len = 0
                for edge in bm.edges:
                    if edge.select:
                        edge_len = edge.calc_length() * 100
                        break
                edge_count = bpy.context.active_object.data.total_edge_sel
                chord = math.sin(math.radians(180 / edge_count))
                scale = edge_len / chord
                uv_layer = bm.loops.layers.uv.verify()
                bpy.ops.mesh.select_linked()
                for f in bm.faces:
                    if f.select:
                        for l in f.loops:
                            l[uv_layer].uv *= scale

        return {'FINISHED'}


blender_classes = [
    UniformTexturesPanel,
    MakeUniform,
    MakeUniformAll,
]


def register():

    for blender_class in blender_classes:
        bpy.utils.register_class(blender_class)
        print("Registered {}".format(bl_info['name']))


def unregister():

    for blender_class in blender_classes:
        bpy.utils.unregister_class(blender_class)
        print("Unregistered {}".format(bl_info['name']))
