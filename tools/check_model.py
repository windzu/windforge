"""Verify imported provenance, print meshes and generic 3MF packages."""
from pathlib import Path
from xml.etree import ElementTree as ET
import hashlib
import json
import sys
import zipfile
import numpy as np
import trimesh

root = Path(__file__).resolve().parents[1]
model = root / 'models' / (sys.argv[1] if len(sys.argv) > 1 else 'apple-tv-brick-phone-case')
manifest = json.loads((model / 'import-manifest.json').read_text())
checks = {'checked_date': '2026-10-06', 'geometry_modified': False,
          'verified_import_files': 0, 'meshes': {}, 'generic_3mf': {}}
for item in manifest['files']:
    file = model / item['destination']
    assert file.stat().st_size == item['bytes'], f'Import size changed: {file}'
    assert hashlib.sha256(file.read_bytes()).hexdigest() == item['sha256'], f'Import hash changed: {file}'
    checks['verified_import_files'] += 1
for file in sorted((model / 'exports/v2').rglob('*.stl')):
    mesh = trimesh.load_mesh(file)
    components = len(mesh.split())
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, file
    assert components == 1 and abs(mesh.bounds[0][2]) < 0.001, file
    if file.parent.name != 'fit-tests':
        original = trimesh.load_mesh(model / 'src/v2/parts' / file.name.replace('_bed', ''))
        assert np.isclose(mesh.volume, original.volume, rtol=1e-6), file
    checks['meshes'][str(file.relative_to(model))] = {
        'watertight': bool(mesh.is_watertight), 'winding_consistent': bool(mesh.is_winding_consistent),
        'connected_components': components, 'triangles': len(mesh.faces),
        'volume_mm3': float(mesh.volume), 'bounds_mm': mesh.bounds.tolist()}
namespace = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
for file in sorted((model / 'exports/v2').rglob('*.3mf')):
    with zipfile.ZipFile(file) as package:
        assert package.testzip() is None, file
        assert not any('gcode' in name.lower() for name in package.namelist()), file
        document = ET.fromstring(package.read('3D/3dmodel.model'))
        assert document.attrib['unit'] == 'millimeter', file
        objects = document.findall('m:resources/m:object', namespace)
        object_ids = {obj.attrib['id'] for obj in objects}
        for obj in objects:
            mesh = obj.find('m:mesh', namespace)
            if mesh is not None:
                vertices = mesh.findall('m:vertices/m:vertex', namespace)
                for triangle in mesh.findall('m:triangles/m:triangle', namespace):
                    assert all(0 <= int(triangle.attrib[f'v{i}']) < len(vertices) for i in (1, 2, 3)), file
            for component in obj.findall('m:components/m:component', namespace):
                assert component.attrib['objectid'] in object_ids, file
        items = document.findall('m:build/m:item', namespace)
        assert all(item.attrib['objectid'] in object_ids for item in items), file
        expected = 2 if file.name == 'plate_white.3mf' else 3
        assert len(items) == expected, file
        checks['generic_3mf'][str(file.relative_to(model))] = {
            'unit': document.attrib['unit'], 'build_items': len(items), 'contains_gcode': False}
output = model / 'validation/import-checks.json'
output.write_text(json.dumps(checks, indent=2, ensure_ascii=False) + '\n')
print(f"Verified {checks['verified_import_files']} imported files, {len(checks['meshes'])} meshes and {len(checks['generic_3mf'])} generic 3MF packages.")
