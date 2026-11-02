import bpy, json, os
D=bpy.data; OUT=os.environ["OUT"]
res=[]
for o in D.objects:
    if o.type!='MESH' or not o.name.endswith("_Logo"): continue
    mat=o.material_slots[0].material if o.material_slots else None
    if not mat or not mat.use_nodes: print("LG skip",o.name,mat); continue
    nt=mat.node_tree
    tex=next((n for n in nt.nodes if n.type=='TEX_IMAGE'),None)
    if not tex or not tex.image: print("LG noimg",o.name); continue
    pr=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    bc=pr.inputs["Base Color"]; mode="img" if bc.is_linked else None
    mr=next((n for n in nt.nodes if n.type=='MAP_RANGE'),None)
    if mode is None: mode="bw" if mr else "alpha"
    info=dict(name=o.name,image=tex.image.name,mode=mode,base=list(bc.default_value)[:3])
    if mr: info["map"]=[mr.inputs[i].default_value for i in (1,2,3,4)]
    me=o.data; uv=me.uv_layers.active.data
    verts=[];uvs=[]
    me.calc_loop_triangles()
    for t in me.loop_triangles:
        for li in t.loops:
            v=o.matrix_world@me.vertices[me.loops[li].vertex_index].co
            verts.append([round(v.x,5),round(v.z,5),round(-v.y,5)]); uvs.append([round(uv[li].uv[0],5),round(uv[li].uv[1],5)])
    info["pos"]=verts;info["uv"]=uvs
    img=tex.image
    print("LG",o.name,img.name,img.size[:],mode,info.get("map"),img.has_data,img.alpha_mode,len(verts))
    fn=f"{OUT}/{img.name}.png"
    if not os.path.exists(fn):
        sc=bpy.context.scene; sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGBA'; sc.render.image_settings.color_depth='8'
        img.save_render(fn,scene=sc)
    res.append(info)
json.dump(res,open(OUT+"/logos.json","w"))
