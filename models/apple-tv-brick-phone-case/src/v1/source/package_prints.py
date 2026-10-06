"""Validate exported meshes, create standard material-aware 3MF packages.
3MF is a geometry package, not a printer-specific sliced project or G-code.
"""
from pathlib import Path
import json, zipfile
import numpy as np
import trimesh
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
PARTS=ROOT/'parts'
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',NS)
def tag(n):return f'{{{NS}}}{n}'
names=['rear_white','front_white','front_black','antenna_black','side_button_black']
meshes={n:trimesh.load_mesh(PARTS/f'{n}.stl') for n in names}
checks={}
for n,m in meshes.items():
    # OCC's revolved pole may contain a zero-area triangle. Remove only
    # degenerate facets, then validate; never remesh or change the silhouette.
    removed=len(m.faces)-int(m.nondegenerate_faces().sum())
    if removed:
        m.update_faces(m.nondegenerate_faces())
        m.remove_unreferenced_vertices(); m.merge_vertices()
        m.export(PARTS/f'{n}.stl')
    checks[n]=dict(watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),
        removed_degenerate_triangles=removed,
        connected_components=len(m.split()),vertices=len(m.vertices),triangles=len(m.faces),
        volume_mm3=float(m.volume),bounds_mm=m.bounds.tolist())
    assert m.is_watertight and m.is_winding_consistent and m.volume>0,n
    assert len(m.split())==1,n
(ROOT/'mesh_checks.json').write_text(json.dumps(checks,indent=2))

def write_3mf(path,objects,groups):
    model=ET.Element(tag('model'),{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
    ET.SubElement(model,tag('metadata'),{'name':'Title'}).text='Reference-driven retro Apple TV remote shell'
    ET.SubElement(model,tag('metadata'),{'name':'Description'}).text='White and charcoal bodies; mm. Unsliced geometry; select your own printer, material and supports.'
    res=ET.SubElement(model,tag('resources'))
    bases=ET.SubElement(res,tag('basematerials'),{'id':'1'})
    ET.SubElement(bases,tag('base'),{'name':'Shell light grey','displaycolor':'#C9CDCAFF'})
    ET.SubElement(bases,tag('base'),{'name':'Charcoal','displaycolor':'#242929FF'})
    ids={}
    for idx,(name,m,colour) in enumerate(objects,2):
        ids[name]=idx
        ob=ET.SubElement(res,tag('object'),{'id':str(idx),'type':'model','name':name,'pid':'1','pindex':str(colour)})
        mesh=ET.SubElement(ob,tag('mesh')); verts=ET.SubElement(mesh,tag('vertices'))
        for v in m.vertices: ET.SubElement(verts,tag('vertex'),{a:f'{v[i]:.6f}' for i,a in enumerate('xyz')})
        tris=ET.SubElement(mesh,tag('triangles'))
        for f in m.faces: ET.SubElement(tris,tag('triangle'),{f'v{i+1}':str(f[i]) for i in range(3)})
    build=ET.SubElement(model,tag('build'))
    for k,(label,children) in enumerate(groups,len(objects)+2):
        ob=ET.SubElement(res,tag('object'),{'id':str(k),'type':'model','name':label})
        comp=ET.SubElement(ob,tag('components'))
        for n in children: ET.SubElement(comp,tag('component'),{'objectid':str(ids[n])})
        ET.SubElement(build,tag('item'),{'objectid':str(k)})
    content='<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    rels='<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',content);z.writestr('_rels/.rels',rels)
        z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
    # Read back XML to check ids and triangle indexing.
    with zipfile.ZipFile(path) as z:
        doc=ET.fromstring(z.read('3D/3dmodel.model'))
        for mesh in doc.findall(f'.//{tag("mesh")}'):
            count=len(mesh.find(tag('vertices')))
            for t in mesh.find(tag('triangles')): assert all(0<=int(t.attrib[f'v{i}'])<count for i in (1,2,3))

objects=[(n,m,0 if n.endswith('white') else 1) for n,m in meshes.items()]
write_3mf(ROOT/'assembly_multicolor.3mf',objects,[('ASSEMBLY — inspection, rearrange before printing',names)])

# Front is joint face down; rear outer back is face up so support scars stay
# inside its cavity rather than in the visible decorative back recesses. Front is
# retained as ONE multipart build item so white and charcoal remain registered.
plate=[]
for n,m in meshes.items():
    q=m.copy()
    if n.startswith('front'):
        q.vertices=np.column_stack([m.vertices[:,0]+30,168-m.vertices[:,2],m.vertices[:,1]-17.7])
    elif n=='rear_white':
        q.vertices=np.column_stack([-m.vertices[:,0]+87,168-m.vertices[:,2],19.7-m.vertices[:,1]])
    elif n=='antenna_black':
        q.vertices=m.vertices-m.bounds[0]+np.array([122,15,0])
    else:
        # Button cap down: +X points upward after export mirroring.
        q.vertices=np.column_stack([m.vertices[:,1],m.vertices[:,2],m.vertices[:,0]])
        q.vertices-=q.bounds[0];q.vertices+=np.array([122,45,0])
    plate.append((n,q,0 if n.endswith('white') else 1))
write_3mf(ROOT/'print_layout_multicolor.3mf',plate,[('Front — WHITE + BLACK together',['front_white','front_black']),
    ('Rear',['rear_white']),('Antenna',['antenna_black']),('Side button',['side_button_black'])])

# Dedicated front file avoids slicers interpreting the complete assembly as one
# multicolour object. Both material meshes share the same transformed origin.
write_3mf(ROOT/'front_multicolor.3mf',[x for x in plate if x[0].startswith('front')],
          [('Front — keep both colour volumes aligned',['front_white','front_black'])])

for name in ['rail_coupon_rear','rail_coupon_front']:
    m=trimesh.load_mesh(PARTS/f'{name}.stl')
    q=m.copy();q.vertices=np.column_stack([m.vertices[:,0],-m.vertices[:,2],m.vertices[:,1]])
    q.vertices-=q.bounds[0]
    q.export(PARTS/f'{name}_bed.stl')

print(json.dumps(checks,indent=2))
print('Standard 3MF files created and XML validated.')
