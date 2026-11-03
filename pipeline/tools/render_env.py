import bpy, math, os
D=bpy.data; sc=bpy.context.scene
for o in D.objects:
    if o.type=='LIGHT': o.hide_render=True
    if o.name.startswith(("Rain","Steam","Haze")): o.hide_render=True
    if o.type=='CAMERA' and o.name=="EnvCam": D.objects.remove(o)
cam=D.cameras.new("EnvCam"); cam.type='PANO'
try: cam.panorama_type='EQUIRECTANGULAR'
except Exception: cam.cycles.panorama_type='EQUIRECTANGULAR'
co=D.objects.new("EnvCam",cam); sc.collection.objects.link(co)
co.location=(0.0,1.2,1.15)            # blender coords; three: (0, 1.15, -1.2)
co.rotation_euler=(math.radians(90),0,math.radians(-90))
sc.camera=co
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=24; sc.cycles.use_denoising=False
sc.render.resolution_x=2048; sc.render.resolution_y=1024; sc.render.resolution_percentage=100
sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'
sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGB'
sc.render.filepath=os.environ["OUT"]
bpy.ops.render.render(write_still=True); print("ENV done",flush=True)
