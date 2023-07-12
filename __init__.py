# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "Mesh Arranger",
    "author": "Aspecky",
    "description": "Allows you to position your objects in an organized manner.",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "N-Panel > Arrange",
    "category": "Object",
}

import bpy
from mathutils import Vector


def get_root_parents():
    table = {}
    for obj in bpy.context.selected_objects:
        while obj.parent is not None:
            obj = obj.parent
        table[obj] = True

    return list(table.keys())


def get_bounding_box(objs: list):
    min_point = Vector((float("inf"), float("inf"), float("inf")))
    max_point = Vector((float("-inf"), float("-inf"), float("-inf")))
    for obj in objs:
        for vertex in obj.data.vertices:
            world_pos = obj.matrix_world @ vertex.co
            min_point.x = min(min_point.x, world_pos.x)
            min_point.y = min(min_point.y, world_pos.y)
            min_point.z = min(min_point.z, world_pos.z)
            max_point.x = max(max_point.x, world_pos.x)
            max_point.y = max(max_point.y, world_pos.y)
            max_point.z = max(max_point.z, world_pos.z)

    return min_point, max_point


class PropertyGroup(bpy.types.PropertyGroup):
    conglomerate: bpy.props.BoolProperty(
        name="Conglomerate",
        default=False,
        description="Treat the selected objects as one",
    )


class OBJECT_OT_center(bpy.types.Operator):
    bl_idname = "mesh_arranger.center"
    bl_label = "Center"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) != 0

    def execute(self, context):
        props = context.scene.mesh_arranger
        if props.conglomerate:
            roots = get_root_parents()
            objs = [
                obj
                for root in roots
                for obj in [root] + root.children_recursive
                if obj.type == "MESH"
            ]

            min_point, max_point = get_bounding_box(objs)
            center, size = (min_point + max_point) / 2, max_point - min_point
            for obj in roots:
                offset = obj.location - center
                obj.location = Vector((0, 0, size.z / 2)) + offset

        else:
            for obj in get_root_parents():
                objs = [
                    obj for obj in [obj] + obj.children_recursive if obj.type == "MESH"
                ]
                min_point, max_point = get_bounding_box(objs)
                center, size = (min_point + max_point) / 2, max_point - min_point
                offset = obj.location - center
                obj.location = (0, 0, size.z / 2 + offset.z)

        return {"FINISHED"}


class OBJECT_OT_snap_to_plane(bpy.types.Operator):
    bl_idname = "mesh_arranger.snap_to_plane"
    bl_label = "Snap to Plane"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) != 0

    def execute(self, context):
        props = context.scene.mesh_arranger
        if props.conglomerate:
            roots = get_root_parents()
            objs = [
                obj
                for root in roots
                for obj in [root] + root.children_recursive
                if obj.type == "MESH"
            ]

            min_point, max_point = get_bounding_box(objs)
            center, size = (min_point + max_point) / 2, max_point - min_point
            for obj in roots:
                offset = obj.location - center
                obj.location.z = size.z / 2 + offset.z
        else:
            for obj in get_root_parents():
                objs = [
                    obj for obj in [obj] + obj.children_recursive if obj.type == "MESH"
                ]
                min_point, max_point = get_bounding_box(objs)
                center, size = (min_point + max_point) / 2, max_point - min_point
                offset = obj.location - center
                obj.location.z = size.z / 2 + offset.z

        return {"FINISHED"}


class Panel(bpy.types.Panel):
    bl_label = "Mesh Arranger"
    bl_idname = "VIEW3D_PT_mesh_arranger_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Arrange"

    @classmethod
    def poll(cls, context):
        return (
            context.object is None or context.object and context.object.mode == "OBJECT"
        )

    def draw(self, context):
        layout = self.layout
        props = context.scene.mesh_arranger

        box = layout.box()
        box.operator("mesh_arranger.center")
        box.operator("mesh_arranger.snap_to_plane")
        box.prop(props, "conglomerate")


register_classes, unregister_classes = bpy.utils.register_classes_factory(
    [PropertyGroup, OBJECT_OT_center, OBJECT_OT_snap_to_plane, Panel]
)


def register():
    register_classes()
    bpy.types.Scene.mesh_arranger = bpy.props.PointerProperty(type=PropertyGroup)


def unregister():
    unregister_classes()
    del bpy.types.Scene.mesh_arranger


if __name__ == "__main__":
    register()
