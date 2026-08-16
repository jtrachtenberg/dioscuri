"""List every object in the two source GLBs: name, dims, verts, parent."""
import bpy
import os

SRC = r"C:\Users\jtrac\dev\cp2077-mods\dioscuri\mesh-work\source"
FILES = {
    "ASHURA": os.path.join(SRC, r"base\weapons\firearms\rifle_sniper\tsunami_ashura\entities\meshes\w_rifle_sniper__tsunami_ashura__base1_01.glb"),
    "MALORIAN": os.path.join(SRC, r"base\weapons\firearms\handgun\malorian_silverhand\entities\meshes\w_handgun__malorian_silverhand__base1_01.glb"),
}

for label, path in FILES.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    print(f"=== {label} ===")
    for o in bpy.data.objects:
        if o.type == 'MESH':
            d = o.dimensions
            print(f"  MESH {o.name:45s} dims=({d.x:6.3f},{d.y:6.3f},{d.z:6.3f}) verts={len(o.data.vertices):6d} parent={o.parent.name if o.parent else '-'}")
        else:
            print(f"  {o.type:8s} {o.name:45s} parent={o.parent.name if o.parent else '-'}")
print("INSPECT DONE")
