"""Blender display export. Never changes or saves the manufacturing source.

Open the saved model in Blender background mode, run this script, then pass
the output GLB path after --. Keeps the visual remote reference but omits
the studio, cameras and lights. The GLB is a display asset, not a print file.
"""
import sys
from pathlib import Path
import bpy

output = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
output.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
included = []
for obj in bpy.context.scene.objects:
    if obj.type in {'MESH', 'CURVE'} and not obj.name.startswith('STUDIO'):
        obj.hide_set(False)
        obj.hide_render = False
        obj.select_set(True)
        included.append(obj.name)
assert included, 'No display objects selected'
bpy.ops.export_scene.gltf(filepath=str(output), export_format='GLB',
    use_selection=True, export_apply=True, export_cameras=False,
    export_lights=False, export_extras=True)
print(f'Display GLB exported: {output}; {len(included)} objects. Source was not saved.')
