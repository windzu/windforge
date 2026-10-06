from pathlib import Path
import cadquery as cq
import trimesh,numpy as np,json
R=Path(__file__).resolve().parents[1];P=R/'parts';T=R/'fit_tests';T.mkdir(exist_ok=True)
def box(x0,x1,y0,y1,z0,z1):return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))
rear=cq.importers.importStep(str(P/'rear_white.step')).val()
# Actual housing stop faces; a thin connector below the remote joins the ends.
gauge=rear.intersect(box(-13,13,12.0,17.15,5.5,147.25))
gauge=gauge.fuse(box(-12,12,12.0,13.5,5.5,147.25)).clean()
items={'length_gauge_136.5mm':gauge}
white=cq.importers.importStep(str(P/'front_white.step')).val();black=cq.importers.importStep(str(P/'front_black.step')).val()
# Lower locating pin including curved support surface and adhesive seating face.
region=box(6,16,20,38,38,49)
items['panel_socket_coupon']=white.intersect(region)
items['panel_pin_coupon']=black.intersect(region)
checks={}
for name,s in items.items():
 assert s.isValid() and len(s.Solids())==1,(name,len(s.Solids()))
 cq.exporters.export(s,str(T/f'{name}.step'));s.exportStl(str(T/f'{name}.stl'),tolerance=.03,angularTolerance=.1)
 m=trimesh.load_mesh(T/f'{name}.stl');m.vertices=np.column_stack([m.vertices[:,0],-m.vertices[:,2],m.vertices[:,1]])
 m.vertices-=m.bounds[0];m.export(T/f'{name}_bed.stl')
 checks[name]={'valid':True,'volume_mm3':s.Volume()}
(T/'checks.json').write_text(json.dumps(checks,indent=2))
