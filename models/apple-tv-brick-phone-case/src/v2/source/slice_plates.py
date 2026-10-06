from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parents[1];P=R/'source/presets';A='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'
results={}
for colour in ('white','black'):
 out=R/'print_jobs'/colour;out.mkdir(parents=True,exist_ok=True)
 cmd=[A,'--load-settings',str(P/'machine.json')+';'+str(P/'process.json'),'--load-filaments',str(P/f'{colour}.json'),'--arrange','1','--orient','0','--slice','1','--outputdir',str(out),'--export-3mf',f'V2_{colour}.gcode.3mf',str(R/f'plate_{colour}.3mf')]
 with (out/'slice.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 d=json.loads((out/'result.json').read_text())['sliced_plates'][0]
 assert d['filament_change_times']==0
 results[colour]={'seconds':d['total_predication'],'grams':sum(f['total_used_g'] for f in d['filaments']),'objects':[o['name'] for o in d['objects']],'filament_changes':d['filament_change_times'],'warnings':d.get('warning_message')}
 assert all('REFERENCE' not in n for n in results[colour]['objects'])
(R/'slicing_summary.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
