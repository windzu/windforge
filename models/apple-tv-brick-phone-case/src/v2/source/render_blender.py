"""Import millimetre CAD meshes into Blender, build nonprinting remote reference,
save an editable .blend and render orthographic / perspective verification views.
Run: Blender --background --python render_blender.py
"""
from pathlib import Path
import bpy, math, json, os
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
PRE=ROOT/'previews'; PRE.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.length_unit='MILLIMETERS'
scene.render.engine='CYCLES'
scene.cycles.samples=48
scene.cycles.use_denoising=True
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.world.color=(.25,.25,.25)
scene.world.use_nodes=True
scene.world.node_tree.nodes.clear()
bg=scene.world.node_tree.nodes.new('ShaderNodeBackground')
bg.inputs['Color'].default_value=(.65,.68,.67,1)
bg.inputs['Strength'].default_value=.35
wo=scene.world.node_tree.nodes.new('ShaderNodeOutputWorld')
scene.world.node_tree.links.new(bg.outputs['Background'],wo.inputs['Surface'])
scene.render.film_transparent=False

def material(name,colour,roughness=.4,metallic=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*colour,1); m.use_nodes=True
    m.node_tree.nodes.clear()
    p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    output=m.node_tree.nodes.new('ShaderNodeOutputMaterial')
    m.node_tree.links.new(p.outputs['BSDF'],output.inputs['Surface'])
    p.inputs['Base Color'].default_value=(*colour,1)
    p.inputs['Roughness'].default_value=roughness
    p.inputs['Metallic'].default_value=metallic
    p.inputs['Specular IOR Level'].default_value=.22
    return m
white=material('Shell — warm light grey',(.70,.72,.70),.38)
black=material('Face panel — charcoal',(.009,.012,.012),.48)
antmat=material('Antenna and side key',(.006,.008,.008),.46)
silver=material('REFERENCE remote aluminium',(.58,.61,.60),.29,.55)
buttonmat=material('REFERENCE remote buttons',(.004,.005,.006),.46)
iconmat=material('REFERENCE icon ink',(.7,.72,.72),.5)
floor_mat=material('Studio',(.72,.74,.73),.6)
parts={}
for name,mat in [('rear_white',white),('front_white',white),('front_black',black),
                 ('antenna_black',antmat),('side_button_black',antmat),
                 ('REFERENCE_remote_DO_NOT_PRINT',silver)]:
    bpy.ops.wm.stl_import(filepath=str(ROOT/'parts'/f'{name}.stl'))
    ob=bpy.context.object; ob.name=name
    for v in ob.data.vertices: v.co*=.001
    ob.data.materials.clear(); ob.data.materials.append(mat)
    # Preserve hard edges. Smooth only genuinely curved adjacency.
    for p in ob.data.polygons: p.use_smooth=True
    ob.data.set_sharp_from_angle(angle=math.radians(32))
    mod=ob.modifiers.new('Weighted CAD normals','WEIGHTED_NORMAL')
    mod.keep_sharp=True; mod.weight=25
    parts[name]=ob

reference=bpy.data.collections.new('REFERENCE — remote, NOT FOR PRINT')
scene.collection.children.link(reference)
remote=parts['REFERENCE_remote_DO_NOT_PRINT']
for c in list(remote.users_collection): c.objects.unlink(remote)
reference.objects.link(remote)

def ref(ob):
    for c in list(ob.users_collection): c.objects.unlink(ob)
    reference.objects.link(ob)
    return ob

def disk(name,x,z,r,y=24.35,depth=.7,mat=buttonmat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=r*.001,depth=depth*.001,
        location=(-x*.001,y*.001,z*.001),rotation=(math.pi/2,0,0))
    ob=bpy.context.object; ob.name=name; ob.data.materials.append(mat)
    bevel=ob.modifiers.new('soft edge','BEVEL'); bevel.width=.00018; bevel.segments=3
    ob.modifiers.new('normals','WEIGHTED_NORMAL')
    return ref(ob)

def stroke(name,points,r=.13,mat=iconmat,y=24.90):
    curve=bpy.data.curves.new(name,'CURVE'); curve.dimensions='3D'
    curve.bevel_depth=r*.001; curve.bevel_resolution=3
    spl=curve.splines.new('POLY'); spl.points.add(len(points)-1)
    for p,(x,z) in zip(spl.points,points): p.co=(-x*.001,y*.001,z*.001,1)
    ob=bpy.data.objects.new(name,curve); scene.collection.objects.link(ob)
    ob.data.materials.append(mat); return ref(ob)

def ring(name,x,z,r,y=24.91,width=.12,mat=iconmat,a0=0,a1=2*math.pi):
    return stroke(name,[(x+r*math.cos(a0+(a1-a0)*i/80),z+r*math.sin(a0+(a1-a0)*i/80))
                       for i in range(81)],width,mat,y)

disk('REFERENCE clickpad outer',0,116.3,15.1)
disk('REFERENCE clickpad inner',0,116.3,8.8,y=24.73,depth=.22)
ring('REFERENCE clickpad seam',0,116.3,8.85,y=24.88,width=.09,mat=black)
for x,z in [(0,129.7),(13.4,116.3),(0,102.9),(-13.4,116.3)]:
    disk('REFERENCE clickpad dot',x,z,.32,24.84,.06,iconmat)
for x,z in [(-7.4,93.7),(7.4,93.7),(-7.4,78.9),(-7.4,64.2)]:
    disk('REFERENCE round key',x,z,6.3)
# Volume pill as a shallow rounded cuboid.
bpy.ops.mesh.primitive_cube_add(size=1,location=(-.0074,.02435,.0717))
vol=bpy.context.object; vol.name='REFERENCE volume rocker'
vol.dimensions=(.0126,.0010,.0276)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
# Beveling only the face outline through a dedicated bevelled 2D polygon.
bpy.data.objects.remove(vol,do_unlink=True)
points=[]
for cx,cz,start in [(7.4,79.2,0),(7.4,64.2,math.pi)]:
    for i in range(49):
        a=start+math.pi*i/48
        points.append((cx+6.3*math.cos(a),cz+6.3*math.sin(a)))
verts=[(-x*.001,y,z*.001) for y in (.02385,.02485) for x,z in points]
n=len(points); faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
mesh=bpy.data.meshes.new('volume pill'); mesh.from_pydata(verts,[],faces); mesh.update()
ob=bpy.data.objects.new('REFERENCE volume rocker',mesh); scene.collection.objects.link(ob)
ob.data.materials.append(buttonmat); ref(ob)
stroke('REFERENCE back icon',[(-6.6,96.1),(-9.0,93.7),(-6.6,91.3)])
stroke('REFERENCE TV icon',[(4.6,95.5),(10.2,95.5),(10.2,92.1),(4.6,92.1),(4.6,95.5)])
stroke('REFERENCE TV stand',[(7.4,92.1),(7.4,91.2),(5.8,91.2),(9,91.2)])
stroke('REFERENCE play',[(-10,81),(-10,76.8),(-6.7,78.9),(-10,81)])
stroke('REFERENCE pause 1',[(-5.5,81),(-5.5,76.8)])
stroke('REFERENCE pause 2',[(-4.4,81),(-4.4,76.8)])
stroke('REFERENCE plus horizontal',[(4.8,79.2),(10,79.2)])
stroke('REFERENCE plus vertical',[(7.4,76.6),(7.4,81.8)])
stroke('REFERENCE minus',[(4.8,64.2),(10,64.2)])
stroke('REFERENCE mute speaker',[(-10,65.3),(-8.5,65.3),(-6.7,67),(-6.7,61.4),(-8.5,63.1),(-10,63.1),(-10,65.3)])
stroke('REFERENCE mute slash',[(-10.2,67),(-4.7,61.4)])
disk('REFERENCE power key',10.8,139.1,3.0,y=24.02,depth=.15,mat=silver)
ring('REFERENCE power symbol',10.8,139.1,1.3,y=24.15,width=.10,mat=black,a0=math.pi*.7,a1=math.pi*2.3)
stroke('REFERENCE power stroke',[(10.8,141),(10.8,139.2)],.1,black,24.15)
stroke('REFERENCE microphone',[(-.5,138.6),(.4,138.6)],.22,black,24.03)

for x in (-20.65,20.65):
    for z in (4.6,157):
        pass # Magnets are represented by empty pockets in assembly views.

bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,-.0006))
floor=bpy.context.object; floor.name='STUDIO floor'; floor.data.materials.append(floor_mat)

def area(name,loc,power,size,target=(0,.02,.1)):
    bpy.ops.object.light_add(type='AREA',location=loc)
    ob=bpy.context.object; ob.name=name; ob.data.energy=power; ob.data.shape='DISK'; ob.data.size=size
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
area('Key softbox',(-.25,.4,.48),6,.32)
area('Fill softbox',(.35,.15,.26),3,.25)
area('Back rim',(.05,-.3,.4),4,.25)
area('Back inspection fill',(-.25,-.3,.23),3,.20)
bpy.ops.object.camera_add()
camera=bpy.context.object; camera.name='Verification camera'; scene.camera=camera

def render(name,loc,target,scale=.27,size=(1100,1300),ortho=True):
    if os.environ.get('RENDER_ONLY') and name!=os.environ['RENDER_ONLY']: return
    camera.location=loc
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO' if ortho else 'PERSP'
    camera.data.ortho_scale=scale; camera.data.lens=70
    scene.render.resolution_x=size[0]; scene.render.resolution_y=size[1]
    scene.render.filepath=str(PRE/f'{name}.png')
    bpy.ops.render.render(write_still=True)

# Save complete editable assembly with reference in a clearly named collection.
camera.location=(-.32,.55,.33)
camera.rotation_euler=(Vector((0,.016,.112))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO'; camera.data.ortho_scale=.275
scene.render.resolution_x=1200; scene.render.resolution_y=1400
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            space=a.spaces.active
            space.region_3d.view_location=Vector((0,.016,.112))
            space.region_3d.view_distance=.36
            space.region_3d.view_rotation=camera.rotation_euler.to_quaternion()
            space.region_3d.view_perspective='CAMERA'
            space.overlay.show_overlays=False
            space.shading.type='SOLID'
            space.shading.color_type='MATERIAL'
            space.shading.show_cavity=True
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'retro_remote_replica.blend'))
render('01_front_orthographic',(0,.65,.1165),(0,0,.1165),.26)
render('02_back_orthographic',(0,-.65,.1165),(0,0,.1165),.26)
render('03_side_orthographic',(.65,.020,.1165),(0,.020,.1165),.26)
render('04_front_perspective',(-.32,.55,.33),(0,.016,.112),.275,size=(1200,1400))
render('05_back_perspective',(.34,-.55,.30),(0,.016,.112),.275,size=(1200,1400))
render('06_top_detail',(-.15,.18,.33),(0,.015,.158),.105,size=(1200,1000))
floor.hide_render=True
render('07_bottom_detail',(-.15,.24,-.17),(0,.020,.021),.115,size=(1200,1000))
floor.hide_render=False

# Exploded view is an alternate scene state only, not a printing arrangement.
reference.hide_render=True
for n in ('front_white','front_black','side_button_black'):
    parts[n].rotation_euler.z=math.pi
    parts[n].location=(-.038,.120,0)
for n in ('rear_white','antenna_black'): parts[n].location.x=.038
render('08_exploded',(-.26,.50,.36),(0,.045,.110),.30,size=(1400,1300))
for n in ('front_white','front_black','side_button_black'):
    parts[n].rotation_euler.z=0
    parts[n].location=(0,0,0)
for n in ('rear_white','antenna_black'): parts[n].location.x=0
reference.hide_render=False
print('Blender verification views complete',flush=True)

# V2 independent insert exploded view, reference hidden.
reference.hide_render=True
floor.hide_render=True
for n in ('rear_white','antenna_black'): parts[n].location.x=.075
parts['front_black'].location.x=-.065
parts['side_button_black'].location.x=-.022
render('09_v2_separate_parts',(-.38,.65,.42),(0,.016,.116),.34,size=(1500,1200))
