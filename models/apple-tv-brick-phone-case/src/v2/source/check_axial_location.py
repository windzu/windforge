from pathlib import Path
import cadquery as cq,json
R=Path(__file__).resolve().parents[1]
rear=cq.importers.importStep(str(R/'parts/rear_white.step')).val()
remote=(cq.Workplane('XZ').center(0,76).rect(35,136).extrude(-9.25).edges('|Y').fillet(5).val().translate((0,14.7,0)))
checks=[]
for shift in [-.5,-.3,-.25,-.2,0,.2,.25,.3,.5]:
 v=rear.intersect(remote.translate((0,0,shift))).Volume()
 if abs(shift)<=.25:assert v<.001,(shift,v)
 else:assert v>.001,(shift,v)
 checks.append({'remote_shift_mm':shift,'overlap_mm3':v,'expected':'clear' if abs(shift)<=.25 else 'blocked by end stop'})
(R/'axial_location_checks.json').write_text(json.dumps(checks,indent=2))
print('Verified +/-0.25 mm free travel and positive stops beyond that.')
