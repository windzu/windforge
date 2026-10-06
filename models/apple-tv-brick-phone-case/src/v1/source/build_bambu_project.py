"""Build a Bambu-specific TWO-filament preparation project from installed presets.
Uses saved local printer family P1S / 0.4 as an explicit provisional assumption.
Does not connect to a printer, send a job, or modify the user's application config.
"""
from pathlib import Path
import json, copy, subprocess, zipfile, shutil
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parents[1]/'work'/'bambu'; WORK.mkdir(parents=True,exist_ok=True)
LIB=Path('/Applications/BambuStudio.app/Contents/Resources/profiles/BBL')
APP='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'
paths={p.stem:p for p in LIB.rglob('*.json')}
def flattened(name,seen=()):
    assert name not in seen,name
    data=json.loads(paths[name].read_text())
    result={}
    parent=data.get('inherits','')
    if parent:
        for p in ([parent] if isinstance(parent,str) else parent): result.update(flattened(p,seen+(name,)))
    result.update(data)
    result.pop('inherits',None)
    return result

machine=flattened('Bambu Lab P1S 0.4 nozzle')
# Newer installed presets store machine-specific G-code in separate template
# files. Flattening inheritance alone would retain generic fallback startup.
for template_path in (LIB/'machine').glob('Bambu Lab P1S 0.4 nozzle template *.json'):
    template=json.loads(template_path.read_text())
    for key,value in template.items():
        if key.endswith('_gcode'): machine[key]=value
process=flattened('0.16mm Optimal @BBL X1C')
process.update(curr_bed_type='Textured PEI Plate',layer_height='0.16',wall_loops='3',sparse_infill_density='15%',
    sparse_infill_pattern='gyroid',enable_support='1',support_type='normal(auto)',
    support_style='snug',support_on_build_plate_only='0',support_top_z_distance='0.2',
    enable_prime_tower='1',name='Retro replica — P1S 0.4 / 0.16 / supports')
filament=flattened('Bambu PLA Basic @BBL P1S 0.4 nozzle')
files=[]
for name,data in [('machine',machine),('process',process),('white',filament),('black',filament)]:
    data=copy.deepcopy(data)
    if name in ('white','black'):
        data['filament_colour']=['#D1D4D1' if name=='white' else '#202525']
    p=WORK/f'{name}.json';p.write_text(json.dumps(data,indent=2));files.append(p)

cmd=[APP,'--load-settings',';'.join(map(str,files[:2])),
     '--load-filaments',';'.join(map(str,files[2:])),
     '--outputdir',str(WORK),'--export-3mf','base.3mf',str(ROOT/'print_layout_multicolor.3mf')]
with (WORK/'export.log').open('w') as log: subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
with zipfile.ZipFile(WORK/'base.3mf') as z: content={n:z.read(n) for n in z.namelist()}
model=ET.fromstring(content['Metadata/model_settings.config'])
assignments=[]
def setmeta(node,key,val):
    el=next((e for e in node.findall('metadata') if e.get('key')==key),None)
    if el is None:el=ET.SubElement(node,'metadata',{'key':key})
    el.set('value',str(val))
for ob in model.findall('object'):
    label=next(e.get('value','') for e in ob.findall('metadata') if e.get('key')=='name')
    parts=ob.findall('part')
    colours=[1,2] if label.startswith('Front') else [2 if label in ('Antenna','Side button') else 1]
    assert len(parts)==len(colours),(label,len(parts))
    setmeta(ob,'extruder',colours[0])
    for i,(part,colour) in enumerate(zip(parts,colours)):
        partname=('front_white','front_black')[i] if label.startswith('Front') else label
        setmeta(part,'name',partname);setmeta(part,'extruder',colour)
        assignments.append(dict(object=label,part=partname,filament=colour))
content['Metadata/model_settings.config']=ET.tostring(model,encoding='utf-8',xml_declaration=True)
settings=json.loads(content['Metadata/project_settings.config'])
settings['filament_colour']=['#D1D4D1','#202525']
settings['filament_colors']=['#D1D4D1','#202525']
settings['filament_map']=['1','1'] # one physical nozzle, two selectable filaments
settings['flush_volumes_matrix']=['0','250','550','0']
settings['flush_volumes_vector']=['140','140','140','140']
settings['layer_height']='0.16'
settings['printer_settings_id']='Bambu Lab P1S 0.4 nozzle'
content['Metadata/project_settings.config']=json.dumps(settings,indent=2).encode()
target=ROOT/'Bambu_P1S_0.4_双色_试打准备.3mf'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for n,b in content.items():z.writestr(n,b)
# Round-trip through the slicer to refresh thumbnails and preserve actual part
# assignments, rather than shipping a stale all-white cached preview.
with (WORK/'roundtrip.log').open('w') as log:
    subprocess.run([APP,'--arrange','1','--orient','0','--outputdir',str(WORK),
        '--export-3mf','prepared_checked.3mf',str(target)],stdout=log,stderr=subprocess.STDOUT,check=True)
with zipfile.ZipFile(WORK/'prepared_checked.3mf') as z:
    roundtrip=ET.fromstring(z.read('Metadata/model_settings.config'))
    seen=[]
    for obj in roundtrip.findall('object'):
        default=next((m.get('value') for m in obj.findall('metadata') if m.get('key')=='extruder'),'1')
        for part in obj.findall('part'):
            seen.append(next((m.get('value') for m in part.findall('metadata') if m.get('key')=='extruder'),default))
    assert seen.count('1')==2 and seen.count('2')==3,seen
    assert not any(n.endswith('.gcode') for n in z.namelist())
shutil.copyfile(WORK/'prepared_checked.3mf',target)
(ROOT/'bambu_project_checks.json').write_text(json.dumps(dict(
    printer_assumption='Bambu Lab P1S 0.4 nozzle — based on locally saved preset, confirm before printing',
    layer_height=settings['layer_height'],colour_assignments=assignments,
    filament_colours=settings['filament_colour'],support=settings.get('enable_support'),
    physical_print_sent=False),indent=2,ensure_ascii=False))
print(target,flush=True)
print(assignments,flush=True)
