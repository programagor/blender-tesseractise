import bpy
import bmesh
import numpy as np
from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty, CollectionProperty, PointerProperty

bl_info = {
    "name": "Tesseractise",
    "author": "Jiří Bednář (jbednar@isocta.com)",
    "version": (1, 1),
    "blender": (3, 5, 0),
    "location": "Object > Tesseractise",
    "description": "Projects the selected objects onto cells of a 4D tesseract, and then projects the result back into 3D space",
    "warning": "",
    "wiki_url": "",
    "category": "Object",
}

class TesseractiseRotation(bpy.types.PropertyGroup):
    angle: FloatProperty(name="Angle", description="Enter the rotation angle in degrees", default=np.radians(45.0), min=np.radians(-360.0), max=np.radians(360.0), subtype='ANGLE')
    
    plane_mapping = {
        "X": 0,
        "Y": 1,
        "Z": 2,
        "W": 3
    }

    # Enum for rotation plane
    plane_items = [
        ("X-Y", "X-Y", "Simple 3D rotation"),
        ("X-Z", "X-Z", "Simple 3D rotation"),
        ("X-W", "X-W", "Rotation around the 4D W axis"),
        ("Y-Z", "Y-Z", "Simple 3D rotation"),
        ("Y-W", "Y-W", "Rotation around the 4D W axis"),
        ("Z-W", "Z-W", "Rotation around the 4D W axis"),
    ]
    plane: bpy.props.EnumProperty(name="Plane", description="Choose the rotation plane", items=plane_items, default="X-W")



class TesseractiseRotationList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.prop(item, "angle")
        layout.prop(item, "plane")

class TesseractiseAddRotationOperator(bpy.types.Operator):
    bl_idname = "tesseractise.add_rotation"
    bl_label = "Add Rotation"
    bl_description = "Add a new 4D rotation"
    bl_icon = "ADD"

    def execute(self, context):
        context.scene.tesseractise_rotations.add()
        return {'FINISHED'}

class TesseractiseRemoveRotationOperator(bpy.types.Operator):
    bl_idname = "tesseractise.remove_rotation"
    bl_label = "Remove Rotation"
    bl_description = "Remove the selected 4D rotation"
    bl_icon = "REMOVE"

    def execute(self, context):
        rotations = context.scene.tesseractise_rotations
        index = context.scene.tesseractise_rotation_index

        rotations.remove(index)

        if index > 0:
            context.scene.tesseractise_rotation_index = index - 1

        return {'FINISHED'}




# Define the operator
class TesseractiseOperator(bpy.types.Operator):
    bl_idname = "object.tesseractise_operator"
    bl_label = "Tesseractise"
    bl_context = "objectmode"
    bl_description = "Projects the selected objects onto cells of a 4D tesseract, and then projects the result back into 3D space"

    # Define properties
    w_scale: bpy.props.FloatProperty(name="W scale", description="Scaling factor for all positions along the W axis", default=2.5, subtype='FACTOR', soft_min=0.0, soft_max=10.0)
    cam_distance: bpy.props.FloatProperty(name="Camera distance", description="Distance between the 4D camera and the origin", default=4.0, subtype='DISTANCE')
    
    W_minus: bpy.props.BoolProperty(name="W-", description="W- (inner 4D)", default=True)
    W_plus: bpy.props.BoolProperty(name="W+", description="W+ (outer 4D - This cell is inside out with default settings)", default=False)
    Z_minus: bpy.props.BoolProperty(name="Z-", description="Z-", default=True)
    Z_plus: bpy.props.BoolProperty(name="Z+", description="Z+", default=True)
    Y_minus: bpy.props.BoolProperty(name="Y-", description="Y-", default=True)
    Y_plus: bpy.props.BoolProperty(name="Y+", description="Y+", default=True)
    X_minus: bpy.props.BoolProperty(name="X-", description="X-", default=True)
    X_plus: bpy.props.BoolProperty(name="X+", description="X+", default=True)

    projection_options = [
        ("Perspective", "Perspective", "Simple perspective projection (maintains straight lines)"),
        ("Fish-eye", "Fish-eye", "Mirror ball fish-eye projection (introduces distortion)"),
        ("Orthographic", "Orthographic", "Orthographic projection (infinite viewing distance, not useful)"),
    ]
    projection: bpy.props.EnumProperty(name="Projection", description="Which projection to use when converting from 4D to 3D", items=projection_options, default="Fish-eye")

    # Your function definitions (rotation_matrix_4d, mirror_ball_fisheye_4D_to_3D, upconvert_3D_to_4D) go here
    def rotation_matrix_4d(self, theta, axis1, axis2):
        c, s = np.cos(theta), np.sin(theta)
        
        # Identity matrix
        rotation_matrix = np.eye(4)
        
        # Update the matrix elements
        rotation_matrix[axis1, axis1] = c
        rotation_matrix[axis1, axis2] = -s
        rotation_matrix[axis2, axis1] = s
        rotation_matrix[axis2, axis2] = c
        
        return rotation_matrix

    def mirror_ball_fisheye_4D_to_3D(self, points):
        # Normalize the 4D point
        norm_points = points / np.linalg.norm(points, axis=1, keepdims=True)
        
        # Get the 3D portion of the normalized point
        norm_points_3D = norm_points[:,:-1]
        
        # Calculate the cosine of the angle with the W axis
        cos_theta = norm_points[:,-1]   # as the point is normalized, the last component gives the cosine with W axis

        # Multiply the 3D portion by the cosine to get the projected point
        projected_points = cos_theta[:,np.newaxis] * norm_points_3D
        
        return projected_points
    
    def perspective_4D_to_3D(self, points):
        # Use the first 3 components of the 4D point as the 3D point,
        # and divide by the W component to get the perspective projection
        # (the W component is the distance of the point from the camera)
        projected_points = points[:,:-1] / points[:,-1,np.newaxis]

        return projected_points
    
    def orthographic_4D_to_3D(self, points):
        # Use the first 3 components of the 4D point as the 3D point
        projected_points = points[:,:-1]

        return projected_points


    # Function to apply to each vertex
    def upconvert_3D_to_4D(self, points, instance, w_scale, cam_distance):
        if instance == "W-":
            vertex4d = np.column_stack([points, np.full(len(points), -1)])
        elif instance == "W+":
            vertex4d = np.column_stack([points, np.full(len(points), 1)])
        elif instance == "Z-":
            vertex4d = np.column_stack([points[:, :2], np.full((len(points), 1), -1), points[:, 2]])
        elif instance == "Z+":
            vertex4d = np.column_stack([points[:, :2], np.full((len(points), 1), 1), points[:, 2]])
        elif instance == "Y-":
            vertex4d = np.column_stack([points[:, :1], np.full((len(points), 1), -1), points[:, 1:2], points[:, 2]])
        elif instance == "Y+":
            vertex4d = np.column_stack([points[:, :1], np.full((len(points), 1), 1), points[:, 1:2], points[:, 2]])
        elif instance == "X-":
            vertex4d = np.column_stack([np.full((len(points), 1), -1), points[:, :2], points[:, 2]])
        elif instance == "X+":
            vertex4d = np.column_stack([np.full((len(points), 1), 1), points[:, :2], points[:, 2]])

        rotations = bpy.context.scene.tesseractise_rotations

        for rotation in rotations:
            theta = rotation.angle
            axis1, axis2 = rotation.plane.split('-')
            axis1 = TesseractiseRotation.plane_mapping[axis1]
            axis2 = TesseractiseRotation.plane_mapping[axis2]
            rotation_matrix = self.rotation_matrix_4d(theta, axis1, axis2).T
            vertex4d = np.dot(vertex4d, rotation_matrix)

        # Exaggerate the W component
        vertex4d[:, 3] *= w_scale

        vertex4d[:, 3] -= cam_distance

        return vertex4d

    # Main function
    def tesseractise(self, axes, w_scale, cam_distance, projection):
        # Ensure we're in Object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        selected_objs = bpy.context.selected_objects
        for obj_index, obj in enumerate(selected_objs):
            # Make sure the object is a mesh
            if obj.type != 'MESH':
                print(f"Object {obj.name} is not a mesh, skipping.")
                continue

            for instance in axes:
                # Duplicate the object
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.duplicate()
                new_obj = bpy.context.selected_objects[0]
                new_obj.name = f"{obj.name}.{str(instance)}"  # Adds the suffix

                # Apply all modifiers
                bpy.ops.object.convert(target='MESH')

                # Get vertices and convert them to a numpy array
                bpy.ops.object.mode_set(mode='EDIT')
                bm = bmesh.from_edit_mesh(new_obj.data)
                points = np.array([vert.co[:] for vert in bm.verts])

                # Apply the function to all vertices
                new_points_4D = self.upconvert_3D_to_4D(points, instance, w_scale, cam_distance)
                if projection == "Fish-eye":
                    new_points_3D = self.mirror_ball_fisheye_4D_to_3D(new_points_4D)
                elif projection == "Perspective":
                    new_points_3D = self.perspective_4D_to_3D(new_points_4D)
                else:
                    new_points_3D = self.orthographic_4D_to_3D(new_points_4D)

                # Assign the new points back to the mesh
                for i, v in enumerate(bm.verts):
                    v.co = new_points_3D[i]

                bmesh.update_edit_mesh(new_obj.data)
                bpy.ops.object.mode_set(mode='OBJECT')

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        selected_axes = []
        if self.W_minus: selected_axes.append("W-")
        if self.W_plus: selected_axes.append("W+")
        if self.Z_minus: selected_axes.append("Z-")
        if self.Z_plus: selected_axes.append("Z+")
        if self.Y_minus: selected_axes.append("Y-")
        if self.Y_plus: selected_axes.append("Y+")
        if self.X_minus: selected_axes.append("X-")
        if self.X_plus: selected_axes.append("X+")

        self.tesseractise(selected_axes, self.w_scale, self.cam_distance, self.projection)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        # Draw the W scale slider
        layout.prop(self, "w_scale")

        # Draw the camera distance slider
        layout.prop(self, "cam_distance")

        # Draw the projection type
        layout.prop(self, "projection")

        # Draw the axis checkboxes
        layout.label(text="Tesseract cells to generate:", icon='MESH_CUBE')
        row = layout.row(align=True)
        row.prop(self, "X_minus")
        row.prop(self, "Y_minus")
        row.prop(self, "Z_minus")
        row.prop(self, "W_minus")
        row = layout.row(align=True)
        row.prop(self, "X_plus")
        row.prop(self, "Y_plus")
        row.prop(self, "Z_plus")
        row.prop(self, "W_plus")

        # Draw the rotation UI
        scene = context.scene
        layout.label(text="4D rotations:", icon='EMPTY_AXIS')
        layout.template_list("TesseractiseRotationList", "", scene, "tesseractise_rotations", scene, "tesseractise_rotation_index")
        
        # Add and remove rotation buttons
        row = layout.row(align=True)
        row.operator("tesseractise.add_rotation", icon='ADD')
        row.operator("tesseractise.remove_rotation", icon='REMOVE')


def menu_func(self, context):
    self.layout.operator(TesseractiseOperator.bl_idname, text="Tesseractise", icon='CUBE')

# Registration
def register():
    bpy.utils.register_class(TesseractiseRotation)
    bpy.utils.register_class(TesseractiseRotationList)
    bpy.utils.register_class(TesseractiseOperator)
    bpy.utils.register_class(TesseractiseAddRotationOperator)
    bpy.utils.register_class(TesseractiseRemoveRotationOperator)

    bpy.types.Scene.tesseractise_rotations = CollectionProperty(type=TesseractiseRotation)
    bpy.types.Scene.tesseractise_rotation_index = IntProperty()

    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.utils.unregister_class(TesseractiseOperator)
    bpy.utils.unregister_class(TesseractiseRotation)
    bpy.utils.unregister_class(TesseractiseRotationList)
    bpy.utils.unregister_class(TesseractiseAddRotationOperator)
    bpy.utils.unregister_class(TesseractiseRemoveRotationOperator)

    del bpy.types.Scene.tesseractise_rotations
    del bpy.types.Scene.tesseractise_rotation_index

if __name__ == "__main__":
    register()
