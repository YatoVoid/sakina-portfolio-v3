import bpy, os
D=bpy.data
for im in list(D.images):
    if im.name.startswith("lm_") and im.name.endswith(".png"):
        g=im.name[3:-4]; new=os.path.join(os.environ["DN"],im.name)
        if os.path.exists(new):
            im.unpack(method='REMOVE') if im.packed_file else None
            im.filepath=new; im.reload(); im.colorspace_settings.name='sRGB'; im.pack()
            print("SWAP",im.name,im.size[:],flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.environ["OUTBLEND"],compress=True)
