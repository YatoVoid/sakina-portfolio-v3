import bpy, os, sys, glob, time, ctypes
sys.path.insert(0, os.environ["TOOLS"])
import oidn
LIB="/app/blender/lib/libOpenImageDenoise.so"
oidn.glob.glob=lambda *a,**k:[LIB]
oidn.bpy=bpy
import types
# bpy.__file__ may not exist in the binary; _load only needs dirname(dirname(bpy.__file__))
if not hasattr(bpy,"__file__"): bpy.__file__="/app/blender/x/y"
sc=bpy.context.scene
names=os.environ["GROUPS"].split(",")
MODE=os.environ.get("MODE","denoise")
OUT=os.environ["OUT"]
print("DN view",sc.view_settings.view_transform,sc.view_settings.look)
for n in names:
    t=time.time()
    img=bpy.data.images.load(f"{os.environ['LM']}/lm_{n}.exr"); img.colorspace_settings.name='Linear Rec.709'
    if MODE=="denoise":
        oidn.denoise_image(img)
    sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_depth='8'; sc.render.image_settings.color_mode='RGB'
    img.save_render(f"{OUT}/lm_{n}.png",scene=sc)
    print("DN done",n,MODE,round(time.time()-t),"s",flush=True)
