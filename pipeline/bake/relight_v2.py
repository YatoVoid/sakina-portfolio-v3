"""Night-study lighting for the final bake (exec before bake_lightmaps.py setup, or run inside Blender on v3-integrated.blend).
Cool moon and city glow through the window, a small warm sodium glow, a dim cool world fill, warmer less saturated lamps, deeper bounces."""
import bpy
D=bpy.data; sc=bpy.context.scene; w=sc.world.node_tree; L=D.objects
    L=D.objects
def setl(n,col,e): L[n].data.color=col; L[n].data.energy=e
setl("L1_DeskLamp_Key",(1.0,0.68,0.34),60)
setl("L2_DeskLamp_Spill",(1.0,0.68,0.34),4)
setl("L3_FloorLamp",(1.0,0.64,0.30),45)
setl("L7_DeskPool",(1.0,0.70,0.32),18)
setl("L6_TV_Screen",(0.62,0.76,1.0),14)
setl("L4_Window_Night",(0.38,0.52,1.0),200)
glow=L["L4_Window_Night"].copy(); glow.data=L["L4_Window_Night"].data.copy(); glow.name="L8_CityGlow"
glow.location=(0.05,3.0,1.2); glow.data.size=1.4; glow.data.color=(1.0,0.55,0.25); glow.data.energy=70
sc.collection.objects.link(glow)
bg=next(n for n in w.nodes if n.type=='BACKGROUND'); bg.inputs["Color"].default_value=(0.06,0.09,0.17,1); bg.inputs["Strength"].default_value=0.9
out=next(n for n in w.nodes if n.type=='OUTPUT_WORLD')
if not any(l.to_socket.name=="Surface" for l in w.links): w.links.new(bg.outputs["Background"],out.inputs["Surface"])
sc.cycles.max_bounces=14; sc.cycles.diffuse_bounces=8; sc.cycles.glossy_bounces=4; sc.cycles.sample_clamp_indirect=8
