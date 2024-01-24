import bpy
import bmesh
import math
from datetime import datetime
import csv
import numpy as np
from PIL import Image, ImageMath

# Addon Info
bl_info = {
    "name": "Rendering Settings Optimizer",
    "blender": (4, 0, 0),
    "category": "Render",
}

# Register Buttons
class RenderProperties(bpy.types.PropertyGroup):
    mockFloat : bpy.props.FloatProperty(name="Mock Float", description="Quality vs. Optimization, In Percentage", min=0, max=100, default=50)
    mockBool : bpy.props.BoolProperty(name="Mock Boolean", description="Enable Setting", default=True)

    meshQuality : bpy.props.FloatProperty(name="Mesh", description="Mesh Quality vs. Optimization, In Percentage", min=0, max=100, default=50)

    modifierQuality : bpy.props.FloatProperty(name="Modifiers", description="Modifiers Quality vs. Optimization, In Percentage", min=0, max=100, default=50)
    subdivMod : bpy.props.BoolProperty(name="Subdivision Surface/Multiresolution Modifier Optimizations", description="Enable Optimizations On Subdivision Surface and Multiresolution Modifiers (Lowers Quality)", default=True)
    bevelMod : bpy.props.BoolProperty(name="Bevel Modifier Optimizations", description="Enable Optimizations On Bevel Modifiers (Lowers Quality)", default=True)
    remeshMod : bpy.props.BoolProperty(name="Remesh Modifier Optimizations", description="Enable Optimizations On Remesh Modifiers (Lowers Quality)", default=True)

    lightingQuality : bpy.props.FloatProperty(name="Lighting", description="Lighting Quality vs. Optimization, In Percentage", min=0, max=100, default=50)

    renderQuality : bpy.props.FloatProperty(name="Rendering", description="Render Quality vs. Optimization, In Percentage", min=0, max=100, default=50)
    noiseThreshold : bpy.props.BoolProperty(name="Noise Threshold Optimizations", description="Enable Optimizations For Rendered Noise (Lowers Quality)", default=True)
    samples : bpy.props.BoolProperty(name="Render Samples Optimizations", description="Enable Optimizations For Render Samples (Lowers Quality)", default=True)
    
    autoOptimizations : bpy.props.BoolProperty(name="Default Optimizations", description="Enable Settings For Universal Optimizations", default=True)
    
    finalRender : bpy.props.BoolProperty(name="Final Render Mode", description="Enable Finalized Rendering Mode (Highest Fidelity)", default=False)

# Default Panel
class RSO_PT_head_panel(bpy.types.Panel):
    bl_label = "Rendering Settings Optimizer"
    bl_idname = "RSO_PT_head_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RSO"
    bl_order = 0
 
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        renderingTools = scene.renderingTools
        
        layout.prop(renderingTools, "autoOptimizations")
        layout.prop(renderingTools, "finalRender")
        layout.operator("rso.run")
        
        
# Main Panel
class RSO_PT_advanced_panel_mesh(bpy.types.Panel):
    bl_label = "Mesh Quality Settings"
    bl_idname = "RSO_PT_advanced_panel_mesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RSO"
    bl_parent_id = "RSO_PT_head_panel"
    bl_options = {'DEFAULT_CLOSED'}
 
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        renderingTools = scene.renderingTools
        
        layout.prop(renderingTools, "meshQuality", slider=True)

# Subsettings
class RSO_PT_advanced_panel_mod(bpy.types.Panel):
    bl_label = "Modifier Quality Settings"
    bl_idname = "RSO_PT_advanced_panel_mod"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RSO"
    bl_parent_id = "RSO_PT_head_panel"
    bl_options = {'DEFAULT_CLOSED'}
 
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        renderingTools = scene.renderingTools
        
        layout.prop(renderingTools, "modifierQuality", slider=True)
        layout.prop(renderingTools, "subdivMod")
        layout.prop(renderingTools, "bevelMod")
        layout.prop(renderingTools, "remeshMod")
        layout.prop(renderingTools, "smoothMod")

# Lighting Settings
class RSO_PT_advanced_panel_light(bpy.types.Panel):
    bl_label = "Lighting Quality Settings"
    bl_idname = "RSO_PT_advanced_panel_light"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RSO"
    bl_parent_id = "RSO_PT_head_panel"
    bl_options = {'DEFAULT_CLOSED'}
 
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        renderingTools = scene.renderingTools
        
        layout.prop(renderingTools, "lightingQuality", slider=True)

# Camera Settings Options
class RSO_PT_advanced_panel_render(bpy.types.Panel):
    bl_label = "Camera Settings"
    bl_idname = "RSO_PT_advanced_panel_render"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RSO"
    bl_parent_id = "RSO_PT_head_panel"
    bl_options = {'DEFAULT_CLOSED'}
 
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        renderingTools = scene.renderingTools
        
        layout.prop(renderingTools, "renderQuality", slider=True)
        layout.prop(renderingTools, "noiseThreshold")
        layout.prop(renderingTools, "samples")
        
# Apply Settings
class RSO_OT_run(bpy.types.Operator):
    bl_idname = "rso.run"
    bl_label = "Apply Settings"
    
    def execute(self, context):
        for coll in bpy.data.collections:
            coll.hide_render = True
            if coll.name != "RSOCollection":
                copy = [obj for obj in coll.all_objects]
                for obj in copy:
                    obj.hide_render = True
                    
            if coll.name == "RSOCollection":
                for object in coll.objects:
                    bpy.context.view_layer.objects.active = object
                    bpy.ops.object.delete()
                bpy.data.collections.remove(coll)

        collection = bpy.data.collections.new(name="RSOCollection")
        bpy.context.scene.collection.children.link(collection)                
        
        
        for object in context.scene.objects:
            if object.users_collection[0].name == "RSOCollection":
                object.hide_render = False
                
            if object.type == 'MESH' and object.users_collection[0].name != "RSOCollection":
                
            # PREPARE
            
                editObject = object.copy()
                collection.objects.link(editObject)
                editObject.data = editObject.data.copy()
                bpy.context.view_layer.objects.active = editObject
                
                object.hide_render = True
                
                renderingTools = context.scene.renderingTools
            
            # MESH
                
                decimate = editObject.modifiers.new(name="Decimate", type='DECIMATE')
                decimate.decimate_type = "COLLAPSE"
                decimate.ratio = renderingTools.meshQuality/100
                bpy.ops.object.modifier_apply(modifier=decimate.name)
                    
            # MODIFIERS
                
                for sub in bpy.data.objects[editObject.name].modifiers:
                    if(sub.type == "SUBSURF" and renderingTools.subdivMod == True):
                        
                        sub.levels = round(sub.levels * renderingTools.modifierQuality/100)
                        sub.render_levels = round(sub.render_levels * renderingTools.modifierQuality/100)
                
                    if(sub.type == "MULTIRES" and renderingTools.subdivMod == True):
                        
                        sub.levels = round(sub.levels * renderingTools.modifierQuality/100)
                        sub.sculpt_levels = round(sub.sculpt_levels * renderingTools.modifierQuality/100)
                        sub.render_levels = round(sub.render_levels * renderingTools.modifierQuality/100)
                        
                    if(sub.type == "BEVEL" and renderingTools.bevelMod == True):
                        
                        sub.segments = round(sub.segments * renderingTools.modifierQuality/100)
                        
                    if(sub.type == "REMESH" and renderingTools.remeshMod == True):
                        
                        sub.octree_depth = round(sub.octree_depth * renderingTools.modifierQuality/100)
                        sub.voxel_size = sub.voxel_size * sub.voxel_size * renderingTools.modifierQuality
                               
            # RENDER
            
        if renderingTools.samples == True:
            bpy.context.scene.cycles.samples = int(bpy.context.scene.cycles.samples * renderingTools.renderQuality/100)
            
        if renderingTools.samples == True:            
            bpy.context.scene.cycles.use_adaptive_sampling = True
            bpy.context.scene.cycles.adaptive_threshold = int(bpy.context.scene.cycles.adaptive_threshold * (1+renderingTools.renderQuality/100))
           
                   
            # LIGHTING
                
        samples = bpy.context.scene.cycles.samples
        bpy.context.scene.cycles.samples = 1
        bpy.context.scene.update_tag()
        
        bounces = bpy.context.scene.cycles.max_bounces
        diff = bpy.context.scene.cycles.diffuse_bounces
        gloss = bpy.context.scene.cycles.glossy_bounces
        transm = bpy.context.scene.cycles.transmission_bounces
        vol = bpy.context.scene.cycles.volume_bounces
        transp = bpy.context.scene.cycles.transparent_max_bounces

        file = 'D:/Blender Files/Blender Renders/Polygence/data.csv'

        with open(file, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Name', 'Render', 'Bounces', 'Diffuse', 'Transmission', 'Volume', 'Transparent', 'Quality', 'Difference'])
     
        vals = [bounces, diff, gloss, transm, vol, transp]
        refs = ["bpy.context.scene.cycles.max_bounces", "bpy.context.scene.cycles.diffuse_bounces", "bpy.context.scene.cycles.glossy_bounces", "bpy.context.scene.cycles.transmission_bounces", "bpy.context.scene.cycles.volume_bounces", "bpy.context.scene.cycles.transparent_max_bounces"]
        percents = [0, 50]

        renderData("Default", vals[0], refs[0])
        testData(vals, refs, percents)
        resetBounces(bounces, diff, gloss, transm, vol, transp)
        bpy.context.scene.cycles.samples = samples
        
        print("DONE")
        
        fileContent = []
        normalizedVals = []
        with open(file, newline='') as csvfile:
            csvreader = csv.reader(csvfile)
            header = next(csvreader)
            for row in csvreader:
                fileContent.append(row)
        maxVal = 0
        maxTime = 0
        
        for row in fileContent:
            
            if row[0] == "Default":
                defaultTime = float(row[1].replace(":",""))
            
            if maxVal < float(row[8]):
                maxVal = float(row[8])
                
        
        for row in fileContent:
            time = float(row[1].replace(":",""))
            time = time / defaultTime
            val = float(row[8])
            val = val / maxVal
            
            normalized = 0.5*(time)+0.5*(val)
            print(normalized)
            normalizedVals.append("FINAL VALUE: " + str(normalized) + " | NAME: " + str(row[0]))
        
        file = 'D:/Blender Files/Blender Renders/Polygence/finalData.csv'
        with open(file, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(normalizedVals)
         
            # AUTO
        '''
          
        for coll in bpy.data.collections:
            coll.hide_render = False
            if coll.name != "RSOCollection":
                for obj in coll.all_objects:
                    obj.hide_render = False
                    
            if coll.name == "RSOCollection":
                bpy.data.collections.remove(coll)
'''
        return {"FINISHED"}
    
classes = [RenderProperties, RSO_OT_run, RSO_PT_head_panel, RSO_PT_advanced_panel_mesh, RSO_PT_advanced_panel_mod, RSO_PT_advanced_panel_light, RSO_PT_advanced_panel_render]

# Testing Data
def testData(vals, refs, percents):
    for ref in refs:
        for percent in percents:
            val = vals[refs.index(ref)]
            name = "".join([str(ref), str(f"{percent : 04d}")])
            renderData(name, (percent*val/100), ref)
            exec(f"{ref} = {val}")

# Rendering Data
def renderData(name, edit, editName):
    for coll in bpy.data.collections:
        if coll.name == "RSOCollection":
            coll.hide_render = False
            '''
            for c in coll.all_objects:
                print("BREAKAD")
                c.hide_render = False
                print("BREAKAE")
        '''
    edit = int(edit)
    exec(f"{editName} = {edit}")
    filepath = 'D:/Blender Files/Blender Renders/Polygence/TestSample' + name + '.png'
    bpy.context.scene.render.filepath = filepath
    start = datetime.now()
    bpy.ops.render.render(write_still = True)
    end = datetime.now() - start
    
    file = 'D:/Blender Files/Blender Renders/Polygence/data.csv'
    err = compareImage("Default", name)
    with open(file, 'a', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow([name, end, bpy.context.scene.cycles.max_bounces, bpy.context.scene.cycles.diffuse_bounces, bpy.context.scene.cycles.glossy_bounces, bpy.context.scene.cycles.transmission_bounces, bpy.context.scene.cycles.volume_bounces, bpy.context.scene.cycles.transparent_max_bounces, err])

# Reset Bounce Values
def resetBounces(bounces, diff, gloss, transm, vol, transp):
    bpy.context.scene.cycles.max_bounces = bounces
    bpy.context.scene.cycles.diffuse_bounces = diff
    bpy.context.scene.cycles.glossy_bounces = gloss
    bpy.context.scene.cycles.transmission_bounces = transm
    bpy.context.scene.cycles.volume_bounces = vol
    bpy.context.scene.cycles.transparent_max_bounces = transp

# Compare Two Images
def compareImage(imageA, imageB):
    filepathA = 'D:/Blender Files/Blender Renders/Polygence/TestSample' + imageA + '.png'
    filepathB = 'D:/Blender Files/Blender Renders/Polygence/TestSample' + imageB + '.png'
    imageA = Image.open(filepathA)
    imageB = Image.open(filepathB)
    imA = np.sum(np.asarray(imageA).astype(np.float64))
    imB = np.sum(np.asarray(imageB).astype(np.float64))
    err = np.sum((imA - imB) ** 2)
    err /= float(bpy.context.scene.render.resolution_x * bpy.context.scene.render.resolution_y)
    return err

# Register/Unregister Addons
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        bpy.types.Scene.renderingTools = bpy.props.PointerProperty(type=RenderProperties)
 
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
 
 
 
if __name__ == "__main__":
    register()
