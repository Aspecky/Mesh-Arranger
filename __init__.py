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
    "name": "Object Arranger",
    "author": "Aspecky",
    "description": "Allows you to position your objects in an organized manner.",
    "blender": (2, 80, 0),
    "version": (1, 0, 0, 14072023),
    "location": "N-Panel > Arrange",
    "category": "Object",
    "doc_url": "https://github.com/Aspecky/Object-Arranger",
    "tracker_url": "https://github.com/Aspecky/Object-Arranger/issues",
}

import bpy
from mathutils import Vector


def filter_meshes(obj):
    return [obj for obj in [obj] + obj.children_recursive if obj.type == "MESH"]


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

    return (min_point + max_point) / 2, max_point - min_point


class PropertyGroup(bpy.types.PropertyGroup):
    conglomerate: bpy.props.BoolProperty(
        name="Conglomerate",
        default=False,
        description="Treat the selected objects as one",
    )
    margin: bpy.props.FloatProperty(
        name="Margin",
        default=0,
        description="The distance between the objects being arranged.",
    )
    order: bpy.props.EnumProperty(
        name="Order",
        items=[("True", "Descending", ""), ("False", "Ascending", "")],
    )


class OBJECT_ARRANGER_center(bpy.types.Operator):
    bl_idname = "object_arranger.center"
    bl_label = "Center"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) != 0

    def execute(self, context):
        props = context.scene.object_arranger
        if props.conglomerate:
            roots = get_root_parents()
            center, size = get_bounding_box(
                [
                    obj
                    for root in roots
                    for obj in [root] + root.children_recursive
                    if obj.type == "MESH"
                ]
            )
            for obj in roots:
                obj.location = Vector((0, 0, size.z / 2)) + (obj.location - center)

        else:
            for obj in get_root_parents():
                center, size = get_bounding_box(filter_meshes(obj))
                obj.location = Vector((0, 0, size.z / 2)) + (obj.location - center)

        return {"FINISHED"}


class OBJECT_ARRANGER_snap_to_plane(bpy.types.Operator):
    bl_idname = "object_arranger.snap_to_plane"
    bl_label = "Snap to Plane"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) != 0

    def execute(self, context):
        props = context.scene.object_arranger
        if props.conglomerate:
            roots = get_root_parents()
            center, size = get_bounding_box(
                [
                    obj
                    for root in roots
                    for obj in [root] + root.children_recursive
                    if obj.type == "MESH"
                ]
            )
            for obj in roots:
                obj.location.z = size.z / 2 + (obj.location - center).z
        else:
            for obj in get_root_parents():
                center, size = get_bounding_box(filter_meshes(obj))
                obj.location.z = size.z / 2 + (obj.location - center).z

        return {"FINISHED"}


class OBJECT_ARRANGER_arrange(bpy.types.Operator):
    bl_idname = "object_arranger.arrange"
    bl_label = "Arrange"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 1

    def execute(self, context):
        props = context.scene.object_arranger
        margin = props.margin
        order = props.order == "True"

        objs = []
        for obj in get_root_parents():
            center, size = get_bounding_box(
                [obj for obj in [obj] + obj.children_recursive if obj.type == "MESH"]
            )
            objs.append([obj, size.x * size.y * size.z, center, size])
        objs = sorted(objs, key=lambda x: x[1], reverse=order)

        v = objs[0]
        obj, center, size = v[0], v[2], v[3]
        offset = obj.location - center
        obj.location = Vector((0, 0, size.z / 2)) + offset
        last_loc, last_offset, last_size = obj.location, offset, size

        for v in objs[1:]:
            obj, center, size = v[0], v[2], v[3]
            offset = obj.location - center
            obj.location = last_loc + offset - last_offset
            obj.location.x += (last_size.x / 2) + (size.x / 2) + margin
            obj.location.z = size.z / 2 + offset.z
            last_loc, last_offset, last_size = obj.location, offset, size

        return {"FINISHED"}


class Panel(bpy.types.Panel):
    bl_label = "Object Arranger"
    bl_idname = "VIEW3D_PT_object_arranger_panel"
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
        props = context.scene.object_arranger

        box = layout.box()
        box.operator("object_arranger.center")
        box.operator("object_arranger.snap_to_plane")
        box.prop(props, "conglomerate")

        box = layout.box()
        box.operator("object_arranger.arrange")
        box.prop(props, "margin")
        box.prop(props, "order")


register_classes, unregister_classes = bpy.utils.register_classes_factory(
    [
        PropertyGroup,
        OBJECT_ARRANGER_arrange,
        OBJECT_ARRANGER_center,
        OBJECT_ARRANGER_snap_to_plane,
        Panel,
    ]
)


def register():
    register_classes()
    bpy.types.Scene.object_arranger = bpy.props.PointerProperty(type=PropertyGroup)


def unregister():
    unregister_classes()
    del bpy.types.Scene.object_arranger


if __name__ == "__main__":
    register()
