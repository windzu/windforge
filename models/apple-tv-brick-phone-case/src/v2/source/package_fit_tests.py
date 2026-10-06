from pathlib import Path
import runpy,trimesh,numpy as np
R=Path(__file__).resolve().parents[1]
write=runpy.run_path(str(R/'source/package_prints.py'))['write_3mf']
objects=[]
for name,xy in [('length_gauge_136.5mm',(30,30)),('panel_socket_coupon',(70,60)),('panel_pin_coupon',(90,60))]:
 m=trimesh.load_mesh(R/'fit_tests'/f'{name}_bed.stl');m.vertices+=np.array([*xy,0]);objects.append((name,m,0))
write(R/'fit_tests/plate_fit_tests.3mf',objects,[(n,[n]) for n,_,_ in objects])
