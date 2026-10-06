"""Reference-driven Apple TV retro handset shell. Units: mm.
Run with CadQuery 2.8. Geometry estimates and fit assumptions are recorded in
parameters.json and README. No original manufacturer's CAD is available.
"""
from pathlib import Path
import json, math, time
import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / 'parts'
PARTS.mkdir(parents=True, exist_ok=True)
P = dict(width=48.0, body_height=162.0, max_depth=40.0,
         seam_back=17.5, seam_front=17.7, remote_back=14.7,
         remote_front=23.95, remote_bottom=8.0, remote_top=144.0, remote_axial_gap=0.5, panel_side_gap=0.15,
         magnet_diameter=4.2, magnet_depth=2.15, magnet_nominal='4 x 2 mm',
         rail_side_clearance=0.25, rail_vertical_clearance=0.25,
         rail_slide=5.0, antenna_height=71.0, antenna_x=-11.0,
         antenna_y=10.0, window_width=34.4, window_height=89.5)
LOG = []

def note(s):
    print(s, flush=True)
    LOG.append(s)

def box(x0,x1,y0,y1,z0,z1):
    return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))

def rr(w,h,r,y0,y1,cx=0,cz=81):
    a = cq.Workplane('XZ').center(cx,cz).rect(w,h).extrude(-(y1-y0))
    if r:
        a = a.edges('|Y').fillet(r)
    return a.val().translate((0,y0,0))

def wire_rr(w,h,r,y,cz):
    return cq.Workplane(obj=rr(w,h,r,y,y+.1,cz=cz)).faces('<Y').val().outerWire()

def cyl_y(r,y0,y1,x,z):
    return cq.Solid.makeCylinder(r,y1-y0,cq.Vector(x,y0,z),cq.Vector(0,1,0))

def outline(y0,y1):
    # Top R5, separate small bottom chamfers, no all-corner rounded rectangle.
    return (cq.Workplane('XZ').moveTo(-22.5,0).lineTo(22.5,0)
        .lineTo(24,1.5).lineTo(24,157)
        .threePointArc((22.5355339,160.5355339),(19,162))
        .lineTo(-19,162)
        .threePointArc((-22.5355339,160.5355339),(-24,157))
        .lineTo(-24,1.5).close().extrude(-(y1-y0)).val().translate((0,y0,0)))

def valid(name,s,one=True):
    s=s.clean()
    assert s.isValid(), f'Invalid CAD shape: {name}'
    n=len(s.Solids())
    assert n == 1 if one else n>0, f'{name}: {n} disconnected solids'
    assert s.Volume()>0, name
    bb=s.BoundingBox()
    note(f'{name}: {n} solid(s), {s.Volume():.2f} mm3, '
         f'{bb.xlen:.2f} x {bb.ylen:.2f} x {bb.zlen:.2f} mm')
    return s

def safe_fillet(s,selector,r,name):
    # Never silently omit an intended feature.
    try:
        v=cq.Workplane(obj=s).edges(selector).fillet(r).val()
        assert v.isValid()
        note(f'{name}: fillet {r} mm applied')
        return v
    except Exception as e:
        raise RuntimeError(f'{name}: failed intended fillet {r}: {e}')

note('Building rear shell')
rear=outline(0,P['seam_back'])
rear=cq.Workplane(obj=rear).faces('<Y').edges().fillet(.65).val()
rear=rear.cut(rr(36.6,156,4.0,3.0,18.0,cz=81))

# Back decorations are real recessed geometry; depths are explicit estimates.
for w,h,r,cz,depth in [(20,6,.65,150,1.0),(30,74,2.0,76,1.15),
                        (8,8,.35,32,1.1),(30,18,1.6,16,1.15)]:
    rear=rear.cut(rr(w,h,r,-.5,depth,cz=cz))
for x in (-12,12):
    rear=rear.cut(cyl_y(3,-.5,1.15,x,33))

# Internal support shoes locate the remote against the face opening.
# These attach to the back floor. No full solid infill behind the remote.
for z0,z1 in [(15,24),(64,73),(120,129)]:
    for x0,x1 in [(-14,-9),(9,14)]:
        rear=rear.fuse(box(x0,x1,2.7,14.45,z0,z1))
# Bottom location ledge, with the charging opening cut afterwards.
rear=rear.fuse(box(-15.5,15.5,2.7,17.5,5.5,7.75))

# Positive axial location, maintaining the existing remote position z=8..144.
# Bottom stop is z=7.75; top stop z=144.25 => 136.50 mm effective length.
# Side pads avoid the central IR opening and remain below the sliding seam.
for x0,x1 in [(-12,-7),(7,12)]:
    rear=rear.fuse(box(x0,x1,2.7,17.15,144.25,147.25))
note('Axial stops: 7.75..144.25 mm = 136.50 mm; nominal remote 136 mm')

note('Building asymmetric front envelope')
def shoulder_mid(a,z0,b,z1):
    dx=abs(b-a)/2; dz=(z1-z0)/2
    r=(dx*dx+dz*dz)/(2*dx)
    theta=math.asin(dz/r)/2
    move=r*(1-math.cos(theta)); rise=r*math.sin(theta)
    sign=1 if b>a else -1
    return (a+sign*move,z0+rise),(b-sign*move,z1-rise)
bm1,bm2=shoulder_mid(40,19,26.8,49)
tm1,tm2=shoulder_mid(26.8,120,34.6,138)
theta=math.atan(.52)
radius_sum=(30*math.sin(theta)-13.2*math.cos(theta))/(1-math.cos(theta))
lower_r=3.0; upper_r=radius_sum-lower_r
lower_mid=(40-lower_r*(1-math.cos(theta/2)),19+lower_r*math.sin(theta/2))
lower_end=(40-lower_r*(1-math.cos(theta)),19+lower_r*math.sin(theta))
upper_start=(26.8+upper_r*(1-math.cos(theta)),49-upper_r*math.sin(theta))
upper_mid=(26.8+upper_r*(1-math.cos(theta/2)),49-upper_r*math.sin(theta/2))
profile=(cq.Workplane('YZ',origin=(-30,0,0)).moveTo(17.7,0)
 .lineTo(38.8,0).lineTo(40,1.2).lineTo(40,19)
 .threePointArc(lower_mid,lower_end).lineTo(*upper_start)
 .threePointArc(upper_mid,(26.8,49))
 .lineTo(26.8,120)
 .threePointArc(tm1,(30.7,129)).threePointArc(tm2,(34.6,138))
 .lineTo(34.6,159)
 .threePointArc((33.72132,161.12132),(31.6,162))
 .lineTo(17.7,162).close().extrude(60).val())
# Explicit lofted edge rounds avoid fragile fillets at tangent shoulder joins.
# Sections follow a 0.55 mm quarter circle; this preserves the front profile
# through the entire upper/lower transition instead of rounding only the waist.
profile_wire=cq.Workplane(obj=profile).faces('<X').val().outerWire()
core=profile.intersect(box(-23.45,23.45,17.0,43,-1,163))
for side in (-1,1):
    wires=[]
    for i in range(13):
        a=math.pi/2*i/12
        x=side*(23.45+.55*math.sin(a))
        delta=.55*(1-math.cos(a))
        wires.append(profile_wire.translate((x+30,-delta,0)))
    cap=cq.Solid.makeLoft(wires,ruled=False)
    assert cap.isValid(), 'Rounded side loft must be valid'
    core=core.fuse(cap)
front_raw=outline(17.7,42).intersect(core).clean()
assert front_raw.isValid(), 'Rounded front envelope must be valid'
note('front contour: explicit 0.55 mm rounded side lofts and tangent shoulder arcs')

footprint=rr(40.5,135,3.8,16,45,cz=90.5)
skin_inner=front_raw.translate((0,-2.0,0))
skin_outer=front_raw.translate((0,-.35,0))
panel_pocket=front_raw.cut(skin_inner).intersect(footprint)
black=skin_outer.cut(skin_inner).intersect(footprint).intersect(front_raw)
white=front_raw.cut(panel_pocket)

# The visible window has a very mild flare, a black well, and rounded corners.
aperture=cq.Solid.makeLoft([
    wire_rr(33.8,89.0,4.3,23.0,99.75),
    wire_rr(34.4,89.5,4.6,27.0,99.75),
    wire_rr(35.0,90.4,4.9,35.5,99.75),
    wire_rr(35.0,90.4,4.9,46.0,99.75)],ruled=True)
well=rr(37.6,93.0,5.5,24.4,45,cz=99.75).intersect(front_raw).cut(aperture)
black=black.fuse(well)
white=white.cut(well)

# Remote accommodation reaches under the lower black decorative region.
cavity=rr(36.6,156,3.2,17.2,24.45,cz=81)
for name in ['white','black']:
    s=locals()[name].cut(cavity).cut(aperture)
    locals()[name]=s

# Small front pads limit rocking without changing the visible face or blocking
# longitudinal assembly. Nominal clearance to remote face is 0.05 mm.
for z0,z1 in [(20,25),(43,47)]:
    for x0,x1 in [(-16,-13),(13,16)]:
        white=white.fuse(box(x0,x1,23.95,24.65,z0,z1))

# Recessed two-row, ten-column grille. Panel skin is locally backed so the
# decorative holes do not open into unplanned white geometry.
grille_back=rr(34.6,8.8,1.25,29.5,34.0,cz=151.0).intersect(front_raw)
black=black.fuse(grille_back)
white=white.cut(grille_back)
grille_tool=rr(33.5,7.5,1.0,32.7,40,cz=151.0)
black=black.cut(grille_tool)
holes=[]
for z in (149.55,152.45):
    for i in range(10):
        holes.append(cyl_y(.82,29.8,40,(i-4.5)*3.05,z))
for h in holes:
    black=black.cut(h)
    white=white.cut(h)

# Bottom mouthpiece: inset center, deeper border channel, lower narrow slot.
# Cutter depths follow the sloped front by subtracting translated envelopes.
lower_outer=rr(34,9.7,1.25,16,45,cz=35.7)
lower_inner=rr(31.8,7.5,.6,16,45,cz=35.7)
border=lower_outer.cut(lower_inner)
border_tool=front_raw.cut(front_raw.translate((0,-1.75,0))).intersect(border)
center_tool=front_raw.cut(front_raw.translate((0,-.85,0))).intersect(lower_inner)
slot=rr(16.5,1.35,.6,16,45,cz=27.6)
slot_tool=front_raw.cut(front_raw.translate((0,-1.55,0))).intersect(slot)
for tool in [border_tool,center_tool,slot_tool]:
    black=black.cut(tool)
    white=white.cut(tool)

note('Adding bidirectional segmented sliding rails')
# Head teeth enter periodic reliefs at either +/-5 mm, then slide to the
# central retained position. Long stems and undercut slots supply guidance.
# End relief plus remote clearance is tested at every sliding position.
rail_centers=[30,40,50,80,90,100,140]
for side in (-1,1):
    cx=side*20.75
    for z0,z1 in [(25,55),(75,102),(135,145)]:
        rear=rear.fuse(box(cx-.5,cx+.5,17.3,18.8,z0,z1))
        white=white.cut(box(cx-.75,cx+.75,17.4,18.6,z0-5.4,z1+5.4))
        white=white.cut(box(cx-1.25,cx+1.25,18.55,20.0,z0-5.4,z1+5.4))
        # Loading reliefs between narrow retention bridges.
        for cz in range(z0,z1+6,10):
            white=white.cut(box(cx-1.25,cx+1.25,17.4,20.0,cz-3.25,cz+3.25))
    for z in rail_centers:
        rear=rear.fuse(box(cx-1.0,cx+1.0,18.8,19.7,z-1.5,z+1.5))

# Four pairs of cylindrical pockets, axis normal to the joint.
magnet_positions=[]
for x in (-20.65,20.65):
    for z in (4.6,157.0):
        rear=rear.cut(cyl_y(P['magnet_diameter']/2,15.35,17.8,x,z))
        white=white.cut(cyl_y(P['magnet_diameter']/2,17.4,19.85,x,z))
        magnet_positions.append((x,z))

note('Cutting functional openings and making side plunger')
# Top slot bridges the joint; bottom notch accommodates plug overmould.
top_slot=(cq.Workplane('XY').center(0,18.55).rect(26,6.5)
          .extrude(8.8).edges('|Z').fillet(.7).val().translate((0,0,155.2)))
bottom_xy=(cq.Workplane('XY').center(0,19.85).rect(14,11.7)
           .extrude(12).edges('|Z').fillet(1.6).val().translate((0,0,-1)))
bottom_slot=rr(14.0,20.0,2.0,14.0,25.7,cz=0).intersect(bottom_xy)
for name in ['rear','white','black']:
    locals()[name]=locals()[name].cut(top_slot).cut(bottom_slot)

# Separate side button and captured flange. Movement is along X.
def side_rr(w,h,r,x0,x1,cy,cz):
    a=cq.Workplane('YZ').center(cy,cz).rect(w,h).extrude(x1-x0)
    if r: a=a.edges('|X').fillet(r)
    return a.val().translate((x0,0,0))

button=side_rr(3.8,15.0,1.55,22.0,24.8,20.10,117.0)
button=button.fuse(side_rr(4.9,17.0,1.25,20.8,22.0,20.10,117.0))
button=button.fuse(side_rr(2.5,8.0,.7,17.85,20.8,20.10,117.0))
button_hole=side_rr(4.3,15.6,1.7,21.9,26,20.10,117.0)
button_pocket=side_rr(5.5,17.6,1.45,18.0,22.25,20.10,117.0)
button_shaft=side_rr(3.0,8.6,.9,17.0,22.3,20.10,117.0)
for t in (button_hole,button_pocket,button_shaft):
    white=white.cut(t)
    rear=rear.cut(t)

note('Building stepped offset antenna with keyed mounting peg')
# Revolved profile includes shoulders and a rounded tip; exposed Z=162..233.
antenna=(cq.Workplane('XZ').moveTo(0,162).lineTo(5.5,162)
 .lineTo(5.5,171.0).lineTo(4.0,173.3).lineTo(4.0,202.0)
 .lineTo(2.65,204.3).lineTo(2.65,230.35)
 .threePointArc((1.87383,232.22383),(0,233.0))
 .close().revolve(360,(0,0),(0,1)).val().translate((-11,10,0)))
# Keyed peg and socket, hidden below shell top.
peg=cq.Solid.makeCylinder(3.5,7,cq.Vector(-11,10,155),cq.Vector(0,0,1))
peg=peg.cut(box(-7.9,-6,5,15,154,163))
antenna=antenna.fuse(peg)
socket=cq.Solid.makeCylinder(3.7,7.5,cq.Vector(-11,10,154.7),cq.Vector(0,0,1))
socket=socket.cut(box(-7.7,-5,5,15,154,164))
# Socket boss is attached to top wall; do not leave a floating ring in cavity.
boss=cq.Solid.makeCylinder(5.0,7,cq.Vector(-11,10,155),cq.Vector(0,0,1))
rear=rear.fuse(boss).cut(socket)

# V2 removable panel: clearance along the insertion direction (+Y withdrawal).
# Keep the original back seating surface; expand only the side boundaries.
# A translated sweep removes hidden undercuts so the insert can enter from front.
original_black=black
clearance=black
for dx,dz in [(-.15,0),(.15,0),(0,-.15),(0,.15)]:
    clearance=clearance.fuse(original_black.translate((dx,0,dz)))
for dy in (0.5,1,2,4,8,16,24):
    clearance=clearance.fuse(original_black.translate((0,dy,0)))
white=white.cut(clearance).clean()
# Two hidden locating pins; adhesive provides retention, pins provide alignment.
# Fit is deliberately not a fragile snap fit in the thin decorative panel.
panel_pins=[]
for x,z in [(-11,43),(18,151)]:
    section=original_black.intersect(box(x-.2,x+.2,0,45,z-.2,z+.2))
    y=section.BoundingBox().ymin+.15
    peg=cyl_y(1.2,y-1.8,y+.45,x,z)
    socket=cyl_y(1.4,y-2.05,y+.5,x,z)
    black=black.fuse(peg)
    white=white.cut(socket).cut(peg)
    note(f'Pin {x},{z}, y={y}: overlap after cut={black.intersect(white).Volume()}')
    panel_pins.append(dict(x=x,z=z,seat_y=y,pin_diameter=2.4,socket_diameter=2.8))
P['panel_pins']=panel_pins
P['panel_retention']='Two locating pins, original seating surfaces and small adhesive spots; no snap lock.'
note(f'Panel original overlap={original_black.intersect(white).Volume()}, black overlap={black.intersect(white).Volume()}, white valid={white.isValid()}, black valid={black.isValid()}')
# Verify front-on assembly path, separately from housing sliding motion.
panel_checks=[]
for dy in (0,.25,.5,1,2,3,5,10,20,30):
    volume=black.translate((0,dy,0)).intersect(white).Volume()
    panel_checks.append(dict(withdrawal_y=dy,overlap_mm3=volume))
    assert volume<.001, ('panel insertion collision',dy,volume)
(ROOT/'panel_insertion_checks.json').write_text(json.dumps(panel_checks,indent=2))

# Construction uses image-right X. Export uses a right-handed Z-up frame:
# front looks from +Y, so image-left is world +X.
rear=rear.mirror('YZ')
white=white.mirror('YZ')
black=black.mirror('YZ')
antenna=antenna.mirror('YZ')
button=button.mirror('YZ')
P['export_coordinate_note']='Z up; front viewed from +Y; image-left is world +X. Construction X is mirrored at export.'

rear=valid('rear_white',rear)
white=valid('front_white',white)
black=valid('front_black',black)
antenna=valid('antenna_black',antenna)
button=valid('side_button_black',button)
front=white.fuse(black) # Separate manufactured parts; do not require one fused solid.
remote=rr(35.0,136.0,5.0,14.7,23.95,cz=76.0)

shapes={'rear_white':rear,'front_white':white,'front_black':black,
        'antenna_black':antenna,'side_button_black':button}
colours={'rear_white':(.77,.78,.76),'front_white':(.77,.78,.76),
         'front_black':(.055,.06,.06),'antenna_black':(.035,.04,.04),
         'side_button_black':(.045,.05,.05)}
assembly=cq.Assembly(name='Retro_Remote_Replica')
for name,s in shapes.items():
    cq.exporters.export(s,str(PARTS/f'{name}.step'))
    s.exportStl(str(PARTS/f'{name}.stl'),tolerance=.035,angularTolerance=.10)
    assembly.add(s,name=name,color=cq.Color(*colours[name]))
assembly.export(str(ROOT/'retro_remote_assembly.step'))
remote.exportStl(str(PARTS/'REFERENCE_remote_DO_NOT_PRINT.stl'),tolerance=.04,angularTolerance=.12)

note('Checking assembly interference')
checks=[]
names=list(shapes)
for i,a in enumerate(names):
    for b in names[i+1:]:
        vol=shapes[a].intersect(shapes[b]).Volume()
        checks.append(dict(a=a,b=b,overlap_mm3=vol))
        note(f'Overlap {a} / {b}: {vol:.6f} mm3')
for n,s in shapes.items():
    vol=s.intersect(remote).Volume()
    checks.append(dict(a=n,b='remote',overlap_mm3=vol))
    note(f'Overlap {n} / remote: {vol:.6f} mm3')

# Sliding checks use fully installed remote and stationary rear. The plunger
# travels with the front and is checked separately; a 0.2 mm mating gap remains.
for shift in (-5,-4,-3,-2,-1,0,1,2,3,4,5):
    moving=front.translate((0,0,shift))
    vr=moving.intersect(rear).Volume()
    vm=moving.intersect(remote).Volume()
    vb=moving.intersect(button.translate((0,0,shift))).Volume()
    vbr=button.translate((0,0,shift)).intersect(rear).Volume()
    checks.append(dict(slide_z=shift,rear_overlap_mm3=vr,remote_overlap_mm3=vm,button_overlap_mm3=vb,button_rear_overlap_mm3=vbr))
    note(f'Slide {shift:+} mm: rear={vr:.6f}, remote={vm:.6f}, button={vb:.6f}, button/rear={vbr:.6f}')

for shift in (-5,5):
    for gap in (0,.5,1,1.5,2,3,4):
        moving=front.fuse(button).translate((0,gap,shift))
        vr=moving.intersect(rear).Volume()
        vm=moving.intersect(remote).Volume()
        checks.append(dict(loading_z=shift,loading_y=gap,rear_overlap_mm3=vr,remote_overlap_mm3=vm))
        note(f'Load Z={shift:+} Y={gap}: rear={vr:.6f}, remote={vm:.6f}')

for check in checks:
    for key,value in check.items():
        if 'overlap' in key:
            assert value<.001, f'Assembly collision: {check}'

# Small mating-rail coupon uses the same undercut and loading reliefs.
coupon_rear=rear.intersect(box(18.4,23.2,14.0,20.0,24,56))
coupon_front=white.intersect(box(18.4,23.2,17.7,23.0,24,56))
for name,s in [('rail_coupon_rear',coupon_rear),('rail_coupon_front',coupon_front)]:
    valid(name,s)
    s.exportStl(str(PARTS/f'{name}.stl'),tolerance=.035,angularTolerance=.10)

(ROOT/'parameters.json').write_text(json.dumps(P,indent=2,ensure_ascii=False))
(ROOT/'geometry_checks.json').write_text(json.dumps(checks,indent=2))
(ROOT/'build_log.txt').write_text('\n'.join(LOG))
note('Finished CAD exports')
