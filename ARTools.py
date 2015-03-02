# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


bl_info = {
    "name": "AR Tools",
    "author": "Maxim Seliverstoff",
    "version": (1, 0),
    "blender": (2, 69, 0),
    "location": "View3D > Tool Shelf > AR Tools",
    "description": "Edit MultiTarget XML data for Vuforia SDK",
    "warning": "",
    "wiki_url": "",
    "category": "Scene"}


import bpy, bmesh
from mathutils import *
from math import *
from xml.dom import minidom


Targets = []
Parts = []

class ImageTarget:
    def __init__(self, str_name, size_x, size_y):
        self.name = str_name
        self.x = size_x
        self.y = size_y
        
class Part:
    def __init__(self, name, translation, rotation):
        self.name = name
        self.translation = translation
        self.rotation = rotation
            
def openXML():
    asset_path = bpy.context.scene.conf_path
    data_name = bpy.context.scene.mt_data
    
    xmldoc = minidom.parse(asset_path+'StreamingAssets/QCAR/'+data_name+'.xml')
    itemlist = xmldoc.getElementsByTagName('ImageTarget')
    partlist = xmldoc.getElementsByTagName('Part')

    for s in itemlist:
        name = s.attributes['name'].value
        size = s.attributes['size'].value.split(" ")
        iT = ImageTarget(name, float(size[0]), float(size[1]))
        Targets.append(iT)
    
    for p in partlist:
        name = p.attributes['name'].value
        translation = p.attributes['translation'].value.split(" ")
        translation = (float(translation[0]), float(translation[1]), float(translation[2]))
    
        rotation = p.attributes['rotation'].value.split(" ")
        rotation = (float(rotation[1]), float(rotation[2]), float(rotation[3]), float(rotation[4]))
    
        Parts.append(Part(name, translation, rotation))


def CreateTargets():
    bpy.ops.group.create(name="ImageTarget")     
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    emp = bpy.context.object
    emp.empty_draw_size = 0.16   
    asset_path = bpy.context.scene.conf_path
    data_name = bpy.context.scene.mt_data

    for img in Targets:
        imagen_original=bpy.data.images.load(filepath=asset_path+'Editor/QCAR/ImageTargetTextures/'+data_name+'/'+img.name+'_scaled.jpg')  
        nombre_textura = "TX_" + img.name
        nombre_material = "MA_" + img.name
        textura_creada = bpy.data.textures.new(nombre_textura, type = 'IMAGE')
        bpy.data.textures[nombre_textura].image = imagen_original
        mat = bpy.data.materials.new(nombre_material)
    
        textura_en_material = bpy.data.materials[nombre_material].texture_slots.add()
        textura_en_material.texture_coords = 'UV'
        textura_en_material.texture = textura_creada

        plane = bpy.ops.mesh.primitive_plane_add(view_align=False, enter_editmode=False, location=(0, 0, 0))
        bpy.context.object.parent = emp
        bpy.context.scene.objects.active.select = True
        bpy.context.object.data.name = "ME_"+img.name
    
        bpy.context.object.data.materials.append(mat)
        #bpy.context.object.name = "OB_"+img.name
        bpy.context.object.name = img.name
        bpy.context.object.scale = (img.x/2000, img.y/2000, 1.0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bpy.context.object.lock_scale = (True, True, True)

        bpy.ops.object.mode_set(mode='EDIT')
        me = bpy.context.object.data
        bm = bmesh.from_edit_mesh(me)
    
        bpy.ops.uv.reset()

        bmesh.update_edit_mesh(me)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.object.data.uv_textures[0].data[0].image = imagen_original
    
        bpy.ops.object.group_link(group="ImageTarget")  
        
def SaveTargets():
    asset_path = bpy.context.scene.conf_path
    data_name = bpy.context.scene.mt_data
    if 'ImageTarget' in bpy.data.groups:
        gr = bpy.data.groups['ImageTarget']
        if len(gr.objects) < 1:
            print('ERROR: Multitarget objects not found')
        else:
            line = '<?xml version="1.0"?>\n'
            line += '<QCARConfig xsi:noNamespaceSchemaLocation="qcar_config.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
            line += '  <Tracking>\n'
            for ob in gr.objects:
                line += '    <ImageTarget name="%s" size="%f %f"/>\n' % (ob.name, ob.dimensions.x*1000, ob.dimensions.y*1000)
            line += '      <MultiTarget name="'+ data_name +'">\n'
            for ob in gr.objects:
                line += '        <Part name="'+ob.name+'" '
                line += 'translation="%f %f %f" ' % (ob.location.x*1000, ob.location.y*1000, ob.location.z*1000)
                r = ob.rotation_axis_angle
                line += 'rotation="AD: %f %f %f %f"/>\n' % (r[1], r[2], r[3]*-1, 180*r[0]/pi)
            line += '      </MultiTarget>\n'
            line += '    </Tracking>\n'
            line += '</QCARConfig>\n'
            print(line)
            f = open(asset_path + '/StreamingAssets/QCAR/'+ data_name +'.xml', 'w')
            f.write(line)
            f.close()
    else:
        print('ERROR: Group "ImageTarget" not found')        

def TransformTargets():
    for p in Parts:
        #obj = bpy.data.objects["OB_"+p.name]
        obj = bpy.data.objects[p.name]
        obj.location = Vector((p.translation))/1000
        obj.rotation_mode ='AXIS_ANGLE'
        obj.rotation_axis_angle[0] = pi*p.rotation[3]/180
        obj.rotation_axis_angle[1] = p.rotation[0]
        obj.rotation_axis_angle[2] = p.rotation[1]
        obj.rotation_axis_angle[3] = p.rotation[2]*-1                

class ARToolsMakerPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_category = "AR Tools"
    bl_label = "Multi Targets Editor"
 
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.scene, 'conf_path')
        col = layout.column()
        col.prop(context.scene, 'mt_data')        
        col = layout.column()
        col = self.layout.column(align=True)
        col.operator("object.create_mt_scene", text="Create Multi Targets")
        col = self.layout.column(align=True)
        col.operator("object.save_mt_scene", text="Save Multi Targets")        
 
class CreateMultiTargetScene(bpy.types.Operator):
    bl_idname = "object.create_mt_scene"
    bl_label = "Create Multi Targets"
    bl_options = {"UNDO"}
 
    def invoke(self, context, event):
        openXML()
        CreateTargets()
        TransformTargets()
        return {"FINISHED"}
       
class SaveMultiTargetScene(bpy.types.Operator):
    bl_idname = "object.save_mt_scene"
    bl_label = "Same Multi Targets"
    bl_options = {"UNDO"}
 
    def invoke(self, context, event):
        SaveTargets()
        return {"FINISHED"}

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.conf_path = bpy.props.StringProperty \
      (
      name = "Asset path",
      default = "",
      description = "Path to the directory Assets project Unity3d",
      subtype = 'DIR_PATH'
      )
    bpy.types.Scene.mt_data = bpy.props.StringProperty \
      (
      name = "Data Name",
      default = "",
      description = "Name of the database target"
      )

def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.conf_path
 
if __name__ == "__main__":
    register()
 


