from pathlib import Path
import subprocess
R=Path(__file__).resolve().parents[1];P=R/'source/presets'
cmd=['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--load-settings',str(P/'machine.json')+';'+str(P/'process.json'),'--load-filaments',str(P/'white.json'),'--arrange','1','--orient','0','--slice','1','--outputdir',str(R/'fit_tests'),'--export-3mf','V2_Fit_Tests.gcode.3mf',str(R/'fit_tests/plate_fit_tests.3mf')]
subprocess.run(cmd,check=True)
