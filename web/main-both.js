import * as THREE from "three";
import {LookControls} from "./look-controls.js?v=7";
import {GLTFLoader} from "three/addons/loaders/GLTFLoader.js";
import {DRACOLoader} from "three/addons/loaders/DRACOLoader.js";
import {projects,ibm,notepad,credits} from "./content.js";
import {Ambience} from "./audio.js";
import {pad} from "./pad-content.js";
import {makeIbmTerminal} from "./ibm-terminal.js?v=5";
import {addIbmLights} from "./ibm-lights.js";
import {makePadTexture,PAD,UNDER} from "./pad-texture.js";
import {EffectComposer} from "three/addons/postprocessing/EffectComposer.js";
import {RenderPass} from "three/addons/postprocessing/RenderPass.js";
import {UnrealBloomPass} from "three/addons/postprocessing/UnrealBloomPass.js";
import {OutputPass} from "three/addons/postprocessing/OutputPass.js";

const $=id=>document.getElementById(id);
const canvas=$("scene");
const reduced=matchMedia("(prefers-reduced-motion: reduce)").matches;

let renderer;
try{
  renderer=new THREE.WebGLRenderer({canvas,antialias:true,powerPreference:"high-performance"});
}catch{
  $("nogl").hidden=false;$("loader").remove();
  throw new Error("WebGL unavailable");
}
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.NoToneMapping;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.setClearColor(0x07050a);

const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(46,1,0.05,7000);
// Opening hero shot (round 2): eye at screen height, 1.4 m from the CRT, looking slightly down at the desk.
const HOME={pos:new THREE.Vector3(-0.02,1.12,-0.73),target:new THREE.Vector3(-0.02,0.92,-2.13)};   // desk moved 0.48 m to the wall (round 5): same 1.4 m from the CRT
camera.position.copy(HOME.pos);

// Limited orbit around the current view target (round 2): no cursor parallax, zoom and position kept inside the room.
const controls=new LookControls(camera,canvas);
controls.target.copy(HOME.target);
camera.lookAt(controls.target);
controls.setFromCamera(true);

const draco=new DRACOLoader();
draco.setDecoderPath("https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/libs/draco/gltf/");
const loader=new GLTFLoader();
loader.setDRACOLoader(draco);
const meshes={};
let progressRoom=0,progressOut=0;
function setProgress(){
  const p=Math.round((progressRoom*0.9+progressOut*0.1)*100);
  $("loader-fill").style.width=p+"%";$("loader-text").textContent="LOADING "+p+"%";
}
// Per-tape click boxes generated from the Blender scene (pipeline/tools/tape_layout.py).
const TAPE_PAL=[0xc9a227,0x1f8f73,0xa8281f,0x2a4a9a,0xd9631c,0x2f7d3a,0x1f2f63,0x3a8a4a,0x7a3b8c,0xd0541d,0xa02a3c,0x1c6f8a,0x8a7a2a];
let TAPES=[];
const tapeBoxU={min:{value:Array.from({length:16},()=>new THREE.Vector3(1e9,1e9,1e9))},max:{value:Array.from({length:16},()=>new THREE.Vector3(-1e9,-1e9,-1e9))},n:{value:0},col:{value:Array.from({length:16},()=>new THREE.Color(0x333333))}};
const tapesP=fetch("tapes.json").then(r=>r.json()).then(t=>{TAPES=t.map(d=>({idx:d.idx,box:new THREE.Box3(new THREE.Vector3(...d.min),new THREE.Vector3(...d.max))}));TAPES.slice(0,16).forEach((t,i)=>{tapeBoxU.min.value[i].copy(t.box.min);tapeBoxU.max.value[i].copy(t.box.max)});tapeBoxU.n.value=Math.min(16,TAPES.length);TAPES.slice(0,16).forEach((t,i)=>tapeBoxU.col.value[i].set(TAPE_PAL[t.idx%TAPE_PAL.length]))});
// Reflections: a 360 degree capture of the baked room (rendered in Blender at desk height) filters into the environment map.
// The baked materials are emission-only, so the environment only adds specular on top: [roughness, strength, metalness] per bake group.
const REFL=new URLSearchParams(location.search).get("refl")!==null?parseFloat(new URLSearchParams(location.search).get("refl")):1.5;
const SPEC={
  Room_Floor:[.42,.4],Room_Desk:[.4,.75],Room_Monitor:[.28,1.1],Room_Lamp:[.32,1.0],Room_Tapes:[.32,.9],Room_Station:[.45,.45],
  Room_Window:[.5,.4],Room_Plant:[.5,.25],Room_Keepsakes:[.28,1.0,.25],Room_Right_Nook:[.48,.6],Room_Wall_Decor:[.55,.35],Room_Shell:[.8,.12]
};
const envReady=new Promise(res=>{
  const t=new THREE.TextureLoader().load("room_env.jpg",tex=>{
    tex.mapping=THREE.EquirectangularReflectionMapping;tex.colorSpace=THREE.SRGBColorSpace;
    const pm=new THREE.PMREMGenerator(renderer);res(pm.fromEquirectangular(tex).texture);tex.dispose();pm.dispose();
  });
});
// Local lift around the IBM corner (the bake leaves it nearly black). Emissive is scaled and a small warm floor is added
// inside a soft ellipsoid centred on the dresser; nothing outside it changes.
const IBMQ=new URLSearchParams(location.search).get("ibm");const IBM_K=IBMQ!==null?parseFloat(IBMQ):2.8;
const IBM_LIFT_NAMES=["Room_Station","Room_Shell","Room_Floor","Room_Wall_Decor"];
function ibmLift(m){
  m.onBeforeCompile=sh=>{
    sh.uniforms.uIbmC={value:new THREE.Vector3(-2.72,0.95,-1.05)};sh.uniforms.uIbmK={value:IBM_K};
    sh.vertexShader=sh.vertexShader.replace("#include <common>","#include <common>\nvarying vec3 vWP2;")
      .replace("#include <begin_vertex>","#include <begin_vertex>\nvWP2=(modelMatrix*vec4(transformed,1.0)).xyz;");
    sh.fragmentShader=sh.fragmentShader.replace("#include <common>","#include <common>\nvarying vec3 vWP2;uniform vec3 uIbmC;uniform float uIbmK;")
      .replace("#include <emissivemap_fragment>",`#include <emissivemap_fragment>
        vec3 d=(vWP2-uIbmC)/vec3(1.7,1.5,1.9);float f=1.0-smoothstep(0.2,1.0,length(d));
        totalEmissiveRadiance=totalEmissiveRadiance*(1.0+uIbmK*f)+vec3(.010,.006,.003)*f*uIbmK;`)};
  m.needsUpdate=true;
}

const HEALREF=parseFloat(new URLSearchParams(location.search).get("pref")||"0.17");
function heal(m){
  m.onBeforeCompile=sh=>{
    sh.uniforms.uHealRef={value:HEALREF};
    sh.vertexShader=sh.vertexShader.replace("#include <common>","#include <common>\nvarying vec3 vWP3;")
      .replace("#include <begin_vertex>","#include <begin_vertex>\nvWP3=(modelMatrix*vec4(transformed,1.0)).xyz;");
    sh.fragmentShader=sh.fragmentShader.replace("#include <common>","#include <common>\nvarying vec3 vWP3;uniform float uHealRef;")
      .replace("#include <emissivemap_fragment>",`#include <emissivemap_fragment>
        vec3 hd=(vWP3-vec3(-0.80,0.80,-1.95))/vec3(0.22,0.19,0.22);float hw=1.0-smoothstep(0.7,1.0,length(hd));
        if(hw>0.0){
          float hx=smoothstep(0.045,0.075,length(vWP3.xz-vec2(-0.70,-1.94)));hw*=hx;
          vec2 ts=1.0/vec2(textureSize(emissiveMap,0));vec3 qs[24];float ls[24];float mean=0.;
          for(int r=0;r<3;r++)for(int k=0;k<8;k++){float a=float(k)*0.7854+float(r)*0.3;vec2 o=vec2(cos(a),sin(a))*(18.0+float(r)*14.0)*ts;
            vec3 q=texture2D(emissiveMap,vEmissiveMapUv+o).rgb;float ql=dot(q,vec3(.2126,.7152,.0722));qs[r*8+k]=q;ls[r*8+k]=ql;mean+=ql;}
          mean/=24.;vec3 acc=vec3(0.);float cnt=0.;
          for(int i=0;i<24;i++){if(ls[i]>=mean*1.15){acc+=qs[i];cnt+=1.;}}
          vec3 best=cnt>0.?acc/cnt:totalEmissiveRadiance;
          totalEmissiveRadiance=mix(totalEmissiveRadiance,max(totalEmissiveRadiance,best),hw);
          float tl2=dot(totalEmissiveRadiance,vec3(.2126,.7152,.0722));
          float gain=clamp(uHealRef/(tl2+0.002),1.0,24.0);
          totalEmissiveRadiance*=mix(1.0,gain,hw);
        }`)};
  m.needsUpdate=true;
}

const roomP=new Promise((res,rej)=>loader.load("sakina-room-agx-both.glb",g=>{
  const maxAniso=renderer.capabilities.getMaxAnisotropy();
  g.scene.traverse(o=>{
    if(!o.isMesh)return;
    meshes[o.name]=o;
    const m=o.material;
    if(m.emissiveMap){m.emissiveMap.anisotropy=Math.min(8,maxAniso)}
    if(o.name==="Room_Tapes"){
      // Tape cases: the baked black plastic is recoloured per tape (palette below) inside the 13 tape boxes, lit by a lamp falloff.
      // Cream labels, colour stripes and printed text keep their baked values. The same mesh also holds the phone, papers and recorder, which stay untouched.
      m.onBeforeCompile=sh=>{
        sh.uniforms.uBmin=tapeBoxU.min;sh.uniforms.uBmax=tapeBoxU.max;sh.uniforms.uBn=tapeBoxU.n;sh.uniforms.uBcol=tapeBoxU.col;
        sh.vertexShader=sh.vertexShader.replace("#include <common>","#include <common>\nvarying vec3 vWP;")
          .replace("#include <begin_vertex>","#include <begin_vertex>\nvWP=(modelMatrix*vec4(transformed,1.0)).xyz;");
        sh.fragmentShader=sh.fragmentShader.replace("#include <common>","#include <common>\nvarying vec3 vWP;uniform vec3 uBmin[16];uniform vec3 uBmax[16];uniform vec3 uBcol[16];uniform int uBn;")
          .replace("#include <emissivemap_fragment>",`#include <emissivemap_fragment>
           float inTape=0.;vec3 tcol=vec3(0.);
           for(int i=0;i<16;i++){if(i<uBn&&all(greaterThan(vWP,uBmin[i]-vec3(.004)))&&all(lessThan(vWP,uBmax[i]+vec3(.004)))){inTape=1.;tcol=uBcol[i];}}
           float tl=dot(totalEmissiveRadiance,vec3(.2126,.7152,.0722));
           float darkW=(1.0-smoothstep(.05,.30,tl))*inTape;
           float dl=length(vWP-vec3(-0.4,1.06,-2.17));
           float lampL=0.20+0.95/(1.0+2.0*dl*dl);
           vec3 plastic=mix(vec3(dot(tcol,vec3(.3,.59,.11))),tcol,0.82)*lampL*(0.62+3.6*tl);
           totalEmissiveRadiance=mix(totalEmissiveRadiance,plastic,darkW);`)};
      m.needsUpdate=true;
    }
    if(IBM_LIFT_NAMES.includes(o.name))ibmLift(m);
    if(o.name==="Room_Desk"||o.name==="Room_Plant")heal(m);
    const sp=SPEC[o.name];
    if(sp){m.roughness=sp[0];m.metalness=sp[2]||0;if("specularIntensity" in m){m.specularIntensity=1;m.specularColor.setRGB(1,1,1);m.ior=1.5}m.envMapIntensity=sp[1]*REFL;envReady.then(t=>{m.envMap=t;m.needsUpdate=true})}
    else m.envMapIntensity=0;
  });
  // Live shadows on the walls and floor: tiny-intensity point lights at the lamps (they only drive shadow maps; the baked
  // materials are emission-only), and ShadowMaterial copies of the shell and floor that darken only where a caster blocks the lamp.
  const SH=new URLSearchParams(location.search).get("shadow");const shOpacity=SH!==null?parseFloat(SH):0.32;
  for(const [n,m] of Object.entries(meshes)){m.castShadow=!["Room_Shell","Room_Floor","Room_Lamp"].includes(n)}
  const mkLight=(x,y,z,far)=>{const l=new THREE.PointLight(0xffffff,0.0001,far,1);l.position.set(x,y,z);l.castShadow=true;
    l.shadow.mapSize.set(1536,1536);l.shadow.radius=7;l.shadow.bias=-0.0006;l.shadow.normalBias=0.02;l.shadow.camera.near=0.05;scene.add(l);return l};
  mkLight(-0.4,1.06,-2.17,9);          // desk lamp (Blender L1 -0.4, 2.17, 1.06)
  mkLight(2.21,1.6,-0.96,9);           // floor lamp (Blender L3 2.21, 0.96, 1.6)
  const shadowMat=new THREE.ShadowMaterial({color:0x14080a,opacity:shOpacity,transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-1,polygonOffsetUnits:-1});
  for(const n of ["Room_Shell","Room_Floor"]){
    const src=meshes[n];if(!src)continue;
    const r=new THREE.Mesh(src.geometry,shadowMat);r.position.copy(src.position);r.quaternion.copy(src.quaternion);r.scale.copy(src.scale);
    r.receiveShadow=true;r.renderOrder=1;r.name=n+"_shadow";src.parent.add(r);
  }
  {
    const N=1024,cv=document.createElement("canvas");cv.width=cv.height=N;const x=cv.getContext("2d");
    let seed=11;const rnd=()=>((seed=Math.imul(seed^seed>>>15,seed|1)+0x6D2B79F5|0,((seed^seed>>>7)>>>0)/4294967296));
    x.filter="blur(4px)";x.fillStyle="#000";
    const leaf=(cx,cy,len,wid,rot)=>{x.save();x.translate(cx,cy);x.rotate(rot);x.beginPath();x.moveTo(0,0);
      x.bezierCurveTo(wid*.9,-len*.25,wid,-len*.7,0,-len);x.bezierCurveTo(-wid,-len*.7,-wid*.9,-len*.25,0,0);x.fill();
      x.fillRect(-3,0,6,len*.28);x.restore()};
    for(let i=0;i<16;i++){const u=1-Math.pow(rnd(),1.7)*.8,v=.15+rnd()*.7;
      leaf(u*N,v*N+N*.12,N*(.16+rnd()*.14),N*(.05+rnd()*.04),(rnd()-.5)*3.6)}
    const t=new THREE.CanvasTexture(cv);t.colorSpace=THREE.SRGBColorSpace;
    const m=new THREE.MeshBasicMaterial({map:t,color:0x0a0405,transparent:true,opacity:0.62,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-4,polygonOffsetUnits:-4});
    const p=new THREE.Mesh(new THREE.PlaneGeometry(2.0,2.0),m);p.rotation.y=Math.PI/2;p.position.set(-2.99,1.7,-1.5);p.renderOrder=1;p.name="LeafShadows";scene.add(p);
  }
  {
    const t=new THREE.TextureLoader().load("sakina-photo.jpg");t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;
    const p=new THREE.Mesh(new THREE.PlaneGeometry(0.074,0.080),new THREE.MeshBasicMaterial({map:t,color:0xcfc2b0}));
    p.rotation.y=Math.PI/2;p.position.set(-2.6475,0.878,-1.354);p.renderOrder=2;p.name="PolaroidPhoto";scene.add(p);
  }
  scene.add(g.scene);res();
},e=>{if(e.lengthComputable){progressRoom=e.loaded/e.total;setProgress()}},rej));
// Night sky behind the city: dark zenith fading to a warm light-pollution haze at the horizon (round 2).
{
  const g=new THREE.SphereGeometry(3000,48,24),pos=g.attributes.position,c=new THREE.Color(),col=[];
  const zen=new THREE.Color(0x05060c),mid=new THREE.Color(0x111528),hor=new THREE.Color(0x5a3620);
  for(let i=0;i<pos.count;i++){
    const y=pos.getY(i)/3000;
    if(y<0)c.copy(hor);else if(y<0.10)c.copy(hor).lerp(mid,y/0.10);else c.copy(mid).lerp(zen,Math.min(1,(y-0.10)/0.5));
    col.push(c.r,c.g,c.b);
  }
  g.setAttribute("color",new THREE.Float32BufferAttribute(col,3));
  const sky=new THREE.Mesh(g,new THREE.MeshBasicMaterial({vertexColors:true,side:THREE.BackSide,depthWrite:false}));
  sky.renderOrder=-1;scene.add(sky);
}
// City lowered 10 m so its lit skyline fills the window behind the monitor (round 2).
const outP=new Promise((res,rej)=>loader.load("sakina-outside-r4lo.glb",g=>{g.scene.position.y=-10;scene.add(g.scene);res()},
  e=>{if(e.lengthComputable){progressOut=e.loaded/e.total;setProgress()}},rej));

// Berlin rail-yard night photo behind the window (round 4, approved): two unlit emissive pictures ~80 m away (photo patch + panorama).
const viewP=new Promise(res=>loader.load("sakina-view-r4lo.glb",g=>{
  g.scene.traverse(o=>{if(o.isMesh){o.material.side=THREE.DoubleSide;o.material.envMapIntensity=0;o.renderOrder=-1}});
  scene.add(g.scene);res();
},undefined,e=>{console.warn("window view failed",e);res()}));

// Live CRT glass over the baked picture (round 3): scanlines, curved-glass vignette, a soft warm lamp reflection
// that drifts with the viewing angle, and a slow roll bar. Darkens/adds only a little, so the screen never gets neon.
// Picture rect from the Blender scene (e05): x -0.16..0.12, height 0.905..1.115, picture surface 1.617 m deep.
const CRT={cx:-0.02,cy:1.01,w:0.28,h:0.21,z:-2.0935};   // round 5: +0.48 m deeper
const crtGlass=(()=>{
  const g=new THREE.PlaneGeometry(CRT.w,CRT.h,24,18),p=g.attributes.position;
  for(let i=0;i<p.count;i++){const u=p.getX(i)/(CRT.w/2),v=p.getY(i)/(CRT.h/2);p.setZ(i,0.0022*(1-u*u)*(1-v*v))}
  g.computeVertexNormals();
  const m=new THREE.ShaderMaterial({
    uniforms:{uTime:{value:0}},
    transparent:true,depthWrite:false,
    blending:THREE.CustomBlending,blendSrc:THREE.OneFactor,blendDst:THREE.OneMinusSrcAlphaFactor,
    vertexShader:`varying vec2 vUv;varying vec3 vN;varying vec3 vV;
      void main(){vUv=uv;vec4 wp=modelMatrix*vec4(position,1.0);vN=normalize(mat3(modelMatrix)*normal);
      vV=normalize(cameraPosition-wp.xyz);gl_Position=projectionMatrix*viewMatrix*wp;}`,
    fragmentShader:`uniform float uTime;varying vec2 vUv;varying vec3 vN;varying vec3 vV;
      void main(){
        float L=vUv.y*170.0;float fw=fwidth(L);
        float lines=(0.5-0.5*cos(L*6.2831853))*(1.0-smoothstep(0.35,0.9,fw));
        vec2 c=(vUv-0.5)*vec2(1.0,1.18);float r=dot(c,c);
        float vig=smoothstep(0.07,0.30,r)*0.55;
        float roll=fract(vUv.y*0.6-uTime*0.035);roll=smoothstep(0.0,0.06,roll)*(1.0-smoothstep(0.06,0.14,roll));
        vec2 hp=vec2(0.30,0.80)+vV.xy*vec2(-0.35,-0.25);
        vec2 d=(vUv-hp)*vec2(2.3,3.6);float hl=exp(-dot(d,d)*2.2)*0.06;
        float fres=pow(1.0-clamp(dot(normalize(vN),normalize(vV)),0.0,1.0),3.0)*0.10;
        vec3 add=vec3(1.0,0.84,0.64)*(hl+fres)+vec3(0.75,0.82,1.0)*roll*0.018;
        float a=clamp(lines*0.17+vig,0.0,0.8)+0.006*sin(uTime*47.0);
        gl_FragColor=vec4(add,a);
      }`
  });
  const mesh=new THREE.Mesh(g,m);mesh.position.set(CRT.cx,CRT.cy,CRT.z);mesh.renderOrder=2;scene.add(mesh);
  return m;
})();

// Bright CRT phosphor (additive over the baked text so the text stays readable) plus light spill on the desk.
const DESK_TOP=0.72;
const PAPER_TINT=0xc2b296;
const padMesh=(()=>{
  const m=new THREE.MeshBasicMaterial({map:makePadTexture(pad),color:PAPER_TINT});
  const mesh=new THREE.Mesh(new THREE.PlaneGeometry(PAD.w,PAD.h),m);
  mesh.rotation.order="YXZ";mesh.rotation.set(-Math.PI/2,PAD.rotY,0);
  mesh.position.set(PAD.x,0.7258,PAD.z);
  mesh.name="Pad";mesh.renderOrder=1;scene.add(mesh);
  return mesh;
})();
const crtScreen=(()=>{
  const W=1024,H=768,K=W/960,cv=document.createElement("canvas");cv.width=W;cv.height=H;
  const g=cv.getContext("2d");
  const rng=seed=>()=>((seed=Math.imul(seed^seed>>>15,seed|1)+0x6D2B79F5|0,((seed^seed>>>7)>>>0)/4294967296));
  const still=document.createElement("canvas");still.width=W;still.height=H;
  const tex=new THREE.CanvasTexture(cv);tex.colorSpace=THREE.SRGBColorSpace;tex.anisotropy=4;
  const INK="#f4f5ff",BIG=["SAKINA","SAIFUDDIN"],SUB="PORTFOLIO  ·  CH 00";
  const paintBg=c=>{const r=c.createRadialGradient(960*.48,720*.42,0,960*.48,720*.42,960*.62);r.addColorStop(0,"#5471d0");r.addColorStop(.45,"#4c6ac9");r.addColorStop(1,"#4560bd");c.fillStyle=r;c.fillRect(0,0,960,720)};
  let mode="loading",lastAct=0,modeT=0;
  const setMode=(m,t)=>{mode=m;modeT=t};
  const poke=()=>{if(document.getElementById("crt-gate"))return;lastAct=performance.now();if(mode!=="name")setMode("name",lastAct)};
  const paintStill=()=>{
    const s=still.getContext("2d");s.setTransform(1,0,0,1,0,0);s.scale(K,K);const r=rng(7);
    paintBg(s);s.fillStyle=INK;
    for(let i=0;i<26000;i++){
      const x=r()*960,y=r()*720,dx=(x-560)/300,dy=(y-420)/300,d=Math.hypot(dx,dy),edge=Math.max(0,y/720-.55)*1.6;
      const p=d<1?(1-d)*.55*(.4+.6*Math.max(0,-(dx+dy)*.7+.3)):.05+edge*.5;
      if(r()<p){const z=r()<.08?1.8:1.1;s.fillRect(x,y,z,z)}
    }
    s.strokeStyle=INK;s.lineWidth=2;s.globalAlpha=.25;s.beginPath();s.arc(560,420,300,0,7);s.stroke();s.globalAlpha=1;
    s.fillStyle=INK;s.font="900 150px Archivo";try{s.fontStretch="condensed"}catch{}
    BIG.forEach((w,i)=>s.fillText(w,58,220+i*150*.9));
    s.font="32px VT323";s.globalAlpha=.85;s.fillText(SUB,62,262+(BIG.length-1)*150*.9);s.globalAlpha=1;
  };
  const osd=(text,x,y,align="left",size=text.length>14?34:44)=>{g.font=size+"px VT323";g.textAlign=align;g.fillStyle="#f2f2f2";g.shadowColor="rgba(0,0,0,.65)";g.shadowOffsetX=3;g.shadowOffsetY=3;g.fillText(text,x,y);g.shadowColor="transparent";g.textAlign="left"};
  const orbits=t=>{
    g.save();g.strokeStyle=INK;g.lineCap="round";
    [[560,420,430,120,-.32,5],[560,420,380,150,.42,3],[560,400,470,70,.08,2]].forEach(([x,y,a,b,rot,w],i)=>{
      g.lineWidth=w;g.setLineDash([.1,14+i*6]);g.lineDashOffset=-(t*.02*(i%2?1:-1));g.beginPath();g.ellipse(x,y,a,b,rot,0,7);g.stroke()});
    g.restore();
    g.save();g.translate(820+Math.sin(t*.0004)*20,110);g.rotate(t*.0003);g.fillStyle=INK;g.beginPath();
    for(let k=0;k<8;k++){const R=k%2?5:42+Math.sin(t*.003)*6,a=k*Math.PI/4;g.lineTo(Math.cos(a)*R,Math.sin(a)*R)}g.fill();g.restore();
  };
  const draw=t=>{
    g.setTransform(1,0,0,1,0,0);g.setTransform(K,0,0,K,0,0);
    if(mode==="loading"&&!document.getElementById("crt-gate")){lastAct=performance.now();setMode("name",lastAct)}
    if(mode==="name"&&performance.now()-lastAct>6000)setMode("tape",performance.now());
    if(mode==="loading"){
      paintBg(g);osd("▶▶ LOADING",60,82);osd("CH 00",900,82,"right");
      g.font="44px VT323";g.textAlign="left";g.fillStyle="#f4f5ff";
      const line="▮".repeat(20)+"  100%";g.textAlign="center";g.fillText(line,480,392);g.textAlign="left";
    }else if(mode==="tape"){
      paintBg(g);osd("■ STOP",60,82);osd("VIDEO",900,82,"right");
      if(Math.floor(t/700)%2===0)osd("INSERT TAPE",480,372,"center",84);
      osd("PICK A TAPE FROM THE DESK",480,450,"center",44);
    }else{
      g.setTransform(1,0,0,1,0,0);g.drawImage(still,0,0);g.setTransform(K,0,0,K,0,0);
      orbits(t);
      if(Math.floor(t/600)%2===0&&performance.now()-lastAct<1500)osd("▶ PLAY",60,82);
      osd("CH 00",900,82,"right");
    }
    tex.needsUpdate=true;
  };
  const u={uTime:{value:0},uMap:{value:tex}};
  const m=new THREE.ShaderMaterial({uniforms:u,transparent:true,depthWrite:false,
    vertexShader:`varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
    fragmentShader:`uniform float uTime;uniform sampler2D uMap;varying vec2 vUv;
      float h(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
      void main(){
        vec2 c=vUv-0.5;float d=pow(abs(c.x)*2.0,9.0)+pow(abs(c.y)*2.0,9.0);
        float edge=(1.0-smoothstep(0.80,1.0,d))*(0.8+0.2*(1.0-dot(c,c)*3.0));
        vec2 uv=(vUv-0.5)*1.1+0.5;uv+=vec2(0.0015*sin(uTime*31.0+vUv.y*40.0),0.0);
        vec3 pic=texture2D(uMap,uv).rgb;
        float n=h(floor(vUv*vec2(240.0,180.0))+floor(uTime*24.0));
        float lines=0.86+0.14*sin(vUv.y*170.0*6.2831853);
        float flick=0.96+0.04*sin(uTime*53.0)+0.02*sin(uTime*7.0);
        float bar=smoothstep(0.0,0.05,fract(vUv.y*0.7-uTime*0.04))*(1.0-smoothstep(0.05,0.16,fract(vUv.y*0.7-uTime*0.04)));
        vec3 col=pic*(0.9+0.2*n)*lines*flick+vec3(0.5,0.65,1.0)*bar*0.04;
        gl_FragColor=vec4(col*CRT_GAIN,edge);
      }`.replace("CRT_GAIN",(+(new URLSearchParams(location.search).get("crtgain")||1.25)).toFixed(3))});
  const mesh=new THREE.Mesh(new THREE.PlaneGeometry(CRT.w*1.10,CRT.h*1.12),m);
  mesh.position.set(CRT.cx,CRT.cy,CRT.z+0.0012);mesh.renderOrder=1;scene.add(mesh);
  const start=()=>{paintStill();draw(0)};
  const fonts=["900 150px Archivo","32px VT323","44px VT323"];
  Promise.all(fonts.map(f=>document.fonts.load(f))).then(start,start);
  start();
  addEventListener("keydown",poke);
  canvas.addEventListener("pointerdown",poke);
  return {u,draw};
})();
const crtLive=crtScreen.u;
const spill=(()=>{
  const cv=document.createElement("canvas");cv.width=cv.height=256;const x=cv.getContext("2d");
  const g=x.createRadialGradient(128,128,0,128,128,128);g.addColorStop(0,"rgba(120,160,255,0.55)");g.addColorStop(0.45,"rgba(70,110,230,0.20)");g.addColorStop(1,"rgba(40,70,200,0)");
  x.fillStyle=g;x.fillRect(0,0,256,256);
  const t=new THREE.CanvasTexture(cv);t.colorSpace=THREE.SRGBColorSpace;
  const m=new THREE.MeshBasicMaterial({map:t,transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,polygonOffset:true,polygonOffsetFactor:-2,polygonOffsetUnits:-2});
  const mesh=new THREE.Mesh(new THREE.PlaneGeometry(0.85,0.34),m);
  mesh.rotation.x=-Math.PI/2;mesh.position.set(CRT.cx,DESK_TOP+0.006,CRT.z+0.17);mesh.renderOrder=1;scene.add(mesh);
  return mesh;
})();

// Rain on the window glass: static drops, running drops with trails, and faint falling streaks beyond the glass.
// The pane is not in the GLB (the exporter drops it), geometry from the Blender scene: x -0.7..0.8, y 0.95..2.25, z -2.64.
const rainU={uTime:{value:0}};
{
  const m=new THREE.ShaderMaterial({uniforms:rainU,transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,
    vertexShader:`varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
    fragmentShader:`uniform float uTime;varying vec2 vUv;
      float N(float t){return fract(sin(t*12345.564)*7658.76);}
      float N21(vec2 p){p=fract(p*vec2(123.34,345.45));p+=dot(p,p+34.345);return fract(p.x*p.y);}
      vec3 N13(float p){vec3 p3=fract(vec3(p)*vec3(.1031,.11369,.13787));p3+=dot(p3,p3.yzx+19.19);return fract(vec3((p3.x+p3.y)*p3.z,(p3.x+p3.z)*p3.y,(p3.y+p3.z)*p3.x));}
      float Saw(float b,float t){return smoothstep(0.,b,t)*smoothstep(1.,b,t);}
      vec2 DropLayer(vec2 uv,float t){
        vec2 UV=uv;uv.y+=t*.75;vec2 a=vec2(6.,1.);vec2 grid=a*2.;vec2 id=floor(uv*grid);
        float cs=N21(vec2(id.x,3.7));uv.y+=cs;id=floor(uv*grid);vec3 n=N13(id.x*35.2+id.y*2376.1);vec2 st=fract(uv*grid)-vec2(.5,0.);
        float x=n.x-.5;float y=UV.y*20.;float w=sin(y+sin(y));x+=w*(.5-abs(x))*(n.z-.5);x*=.7;
        float ti=fract(t+n.z);y=(Saw(.85,ti)-.5)*.9+.5;vec2 p=vec2(x,y);
        float d=length((st-p)*a.yx);float md=smoothstep(.4,.0,d);
        float r=sqrt(smoothstep(1.,y,st.y));float cd=abs(st.x-x);float tr=smoothstep(.23*r,.15*r*r,cd);float tf=smoothstep(-.02,.02,st.y-y);tr*=tf*r*r;
        y=UV.y;float t2=smoothstep(.2*r,.0,cd);float dr=max(0.,(sin(y*(1.-y)*120.-st.y))*t2*tf*n.z);y=fract(y*10.)+(st.y-.5);float dd=length(st-vec2(x,y));dr=smoothstep(.3,0.,dd);
        return vec2(md+dr*r*tf,tr);}
      float Static(vec2 uv,float t){uv*=38.;vec2 id=floor(uv);uv=fract(uv)-.5;vec3 n=N13(id.x*107.45+id.y*3543.654);vec2 p=(n.xy-.5)*.7;float d=length(uv-p);float f=Saw(.025,fract(t+n.z));return smoothstep(.3,0.,d)*fract(n.z*10.)*f;}
      void main(){
        float t=uTime*.2;vec2 uv=(vUv-.5)*vec2(1.5,1.3)*1.7;
        float st=Static(uv*1.5,t);vec2 dr=DropLayer(uv*1.2,t)*.8+DropLayer(uv*2.1+7.2,t)*.6;
        float m=clamp(st+dr.x,0.,1.);m=smoothstep(.5,.88,m)*.5;
        vec2 g=vec2(dFdx(m),dFdy(m));float hl=clamp(dot(normalize(g+1e-6),normalize(vec2(-.6,.8)))*length(g)*40.,0.,1.);
        float body=m*.045;
        float streak=0.;
        for(int k=0;k<3;k++){
          float fk=float(k);float cols=48.+fk*29.;float sp=1.15+fk*.5;
          vec2 q=vec2(uv.x+uv.y*.1+sin(uv.y*3.+fk*2.)*.01,uv.y);
          float col=floor(q.x*cols);float rr=N(col+1.+fk*17.);float xx=fract(q.x*cols+(N(col+7.)-.5)*.5)-.5;
          float len=.18+N(col+3.+fk)*.3;
          float yy=fract(q.y*(.3+fk*.08)+uTime*(sp+rr*.7)+rr*9.);
          streak+=smoothstep(.07-fk*.01,.0,abs(xx))*smoothstep(0.,.06,yy)*smoothstep(len,.02,yy)*step(.58,rr)*(.3-fk*.05);
        }
        vec3 c=vec3(.55,.66,.9)*(body+streak)+vec3(1.,.93,.82)*hl*.3*m;
        gl_FragColor=vec4(c,1.);
      }`});
  const mesh=new THREE.Mesh(new THREE.PlaneGeometry(1.5,1.3),m);
  mesh.position.set(0.05,1.6,-2.636);mesh.renderOrder=3;scene.add(mesh);
}

// Steam over the coffee. Mug_Coffee surface: three.js x -0.236, y 0.809, z -1.883. The Blender steam curves are not exported.
const steamU={uTime:{value:0},uPx:{value:700}};
{
  const N=36,pos=new Float32Array(N*3),seed=new Float32Array(N*4);
  for(let i=0;i<N;i++){seed[i*4]=Math.random();seed[i*4+1]=Math.random();seed[i*4+2]=Math.random();seed[i*4+3]=Math.random()}
  const g=new THREE.BufferGeometry();
  g.setAttribute("position",new THREE.BufferAttribute(pos,3));
  g.setAttribute("seed",new THREE.BufferAttribute(seed,4));
  const m=new THREE.ShaderMaterial({uniforms:steamU,transparent:true,depthWrite:false,
    vertexShader:`uniform float uTime,uPx;attribute vec4 seed;varying float vA;
      void main(){
        float life=3.4+seed.x*1.6;float ph=fract(uTime/life+seed.y);
        float h=ph*0.2;
        float sway=sin(ph*6.2831*1.3+seed.z*6.2831)*(0.006+ph*0.022);
        float sway2=cos(ph*6.2831*0.9+seed.w*6.2831)*(0.004+ph*0.018);
        vec3 p=vec3(-0.236+(seed.z-.5)*0.03+sway+ph*0.012,0.812+h,-1.883+(seed.w-.5)*0.03+sway2);
        vec4 mv=viewMatrix*vec4(p,1.0);
        gl_Position=projectionMatrix*mv;
        gl_PointSize=uPx*(0.02+ph*0.06+seed.x*0.012)/-mv.z;
        vA=smoothstep(0.,.14,ph)*(1.-smoothstep(.45,1.,ph))*(.5+seed.x*.5);
      }`,
    fragmentShader:`varying float vA;
      void main(){float d=length(gl_PointCoord-.5)*2.;float a=smoothstep(1.,0.,d);a*=a;gl_FragColor=vec4(vec3(.95,.92,.88),a*vA*.4);}`});
  const pts=new THREE.Points(g,m);pts.frustumCulled=false;pts.renderOrder=2;scene.add(pts);
}

// Tape logos: the baked lightmap cannot hold them (each logo quad got a ~140x10 px lightmap island), so they are drawn as
// textured quads over the baked label windows. Geometry and blend mode come from the Blender scene (pipeline/tools/export_logos.py).
const LOGO_LIGHT=0.62;
fetch("logos/logos.json").then(r=>r.json()).then(list=>{
  const tl=new THREE.TextureLoader();
  const sh=list.find(l=>l.name==="PTape_1_Logo"),dv=[0.0126,-0.0194,0.0436];
  if(sh)list.push({name:"PTape_2_House",image:null,mode:"alpha",base:[0.03,0.04,0.03],uv:sh.uv,pos:sh.pos.map(p=>[p[0]+dv[0],p[1]+dv[1],p[2]+dv[2]])});
  for(const L of list){
    let tex;
    if(L.image){tex=tl.load("logos/"+L.image+".png")}
    else{const c=document.createElement("canvas");c.width=c.height=128;const g=c.getContext("2d");g.fillStyle="#fff";g.beginPath();g.moveTo(64,10);g.lineTo(118,60);g.lineTo(100,60);g.lineTo(100,116);g.lineTo(76,116);g.lineTo(76,80);g.lineTo(52,80);g.lineTo(52,116);g.lineTo(28,116);g.lineTo(28,60);g.lineTo(10,60);g.closePath();g.fill();tex=new THREE.CanvasTexture(c)}
    tex.colorSpace=THREE.SRGBColorSpace;tex.anisotropy=8;
    const g=new THREE.BufferGeometry();
    g.setAttribute("position",new THREE.Float32BufferAttribute(L.pos.flat(),3));
    g.setAttribute("uv",new THREE.Float32BufferAttribute(L.uv.flat(),2));
    const base=new THREE.Color().setRGB(L.base[0],L.base[1],L.base[2],THREE.LinearSRGBColorSpace);
    const mode={img:0,alpha:1,bw:2}[L.mode],mp=L.map||[0,1,0,1];
    const m=new THREE.ShaderMaterial({
      uniforms:{map:{value:tex},uMode:{value:mode},uBase:{value:new THREE.Vector3(base.r,base.g,base.b)},uMap:{value:new THREE.Vector4(...mp)},uLight:{value:LOGO_LIGHT}},
      transparent:true,depthWrite:false,depthTest:L.image!==null,polygonOffset:true,polygonOffsetFactor:-4,polygonOffsetUnits:-4,side:THREE.DoubleSide,
      vertexShader:`varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
      fragmentShader:`uniform sampler2D map;uniform int uMode;uniform vec3 uBase;uniform vec4 uMap;uniform float uLight;varying vec2 vUv;
        void main(){
          vec4 t=texture2D(map,vUv);vec3 c;float a;
          if(uMode==0){c=t.rgb;a=t.a;}
          else if(uMode==1){c=uBase;a=t.a;}
          else{float l=dot(t.rgb,vec3(.2126,.7152,.0722));a=clamp((l-uMap.x)/(uMap.y-uMap.x),0.,1.)*(uMap.w-uMap.z)+uMap.z;c=uBase;}
          gl_FragColor=vec4(c*uLight,a);
        }`});
    const mesh=new THREE.Mesh(g,m);mesh.renderOrder=1;mesh.frustumCulled=false;mesh.name="Logo_"+L.name;scene.add(mesh);
  }
}).catch(e=>console.warn("logos failed",e));

const box=name=>new THREE.Box3().setFromObject(meshes[name]);
function deskTapeBox(){
  const b=new THREE.Box3(),v=new THREE.Vector3(),m=meshes.Room_Tapes;
  m.updateWorldMatrix(true,false);
  const pos=m.geometry.attributes.position;
  for(let i=0;i<pos.count;i++){
    v.fromBufferAttribute(pos,i).applyMatrix4(m.matrixWorld);
    if(v.y>DESK_TOP)b.expandByPoint(v);
  }
  return b;
}
let tapeBox;
// Which tape contains this point: the tape whose box holds it with the most vertical margin (stacked tapes share faces).
function tapeAt(p){
  let best=null,bestM=-Infinity;
  for(const t of TAPES){
    const b=t.box.clone().expandByScalar(0.004);
    if(!b.containsPoint(p))continue;
    const m=Math.min(p.y-t.box.min.y,t.box.max.y-p.y);
    if(m>bestM){bestM=m;best=t.idx}
  }
  return best;
}
const ibmLights=addIbmLights(scene);
const term=makeIbmTerminal({scene,position:[-2.7573,0.873,-1.1926],size:[0.283,0.208],rotationY:1.2896,onOpenLink:href=>{if(href.startsWith("mailto:"))location.href=href;else window.open(href,"_blank","noopener")}});
addEventListener("keydown",e=>{if(e.metaKey||e.ctrlKey||e.altKey||document.getElementById("crt-gate"))return;if(term.onKey(e)){e.preventDefault();e.stopImmediatePropagation()}},true);
let VIEWS;
function buildViews(){
  tapeBox=deskTapeBox();
  const tapes=tapeBox.getCenter(new THREE.Vector3());
  const ibmC=box("Room_Station").getCenter(new THREE.Vector3());
  ibmC.y+=0.36;                                   // round 3: dresser + computer, aim between keyboard and screen
  const deskBox=box("Room_Desk");
  const deskC=deskBox.getCenter(new THREE.Vector3());
  const note=new THREE.Vector3(-0.47,0.76,-1.84);
  VIEWS={
    home:{target:HOME.target.clone(),pos:HOME.pos.clone()},
    tapes:{target:tapes.clone(),pos:tapes.clone().add(new THREE.Vector3(0,0.35,0.95))},
    ibm:{target:new THREE.Vector3(-2.72,0.873,-1.195),pos:new THREE.Vector3(-2.2,0.9,-1.195)},
    notepad:{target:note.clone(),pos:note.clone().add(new THREE.Vector3(0.05,0.62,0.55))},
    work:{target:tapes.clone().add(new THREE.Vector3(0.24,-0.04,0)),pos:tapes.clone().add(new THREE.Vector3(0.22,0.3,1.12))},
    clocks:{target:new THREE.Vector3(-1.8,2.1,-2.55),pos:new THREE.Vector3(-1.0,1.5,-0.5)},
    desk:{target:deskC.clone().add(new THREE.Vector3(0,0.05,0)),pos:deskC.clone().add(new THREE.Vector3(0.1,0.65,1.25))}
  };
}

let tween=null;
function flyTo(name){
  const v=VIEWS[name];if(!v)return;
  const from={p:camera.position.clone(),t:controls.target.clone()};
  const dur=reduced?1:1300;
  controls.enabled=false;
  tween={start:performance.now(),dur,from,to:v,name};
}
function stepTween(now){
  if(!tween)return;
  let k=Math.min(1,(now-tween.start)/tween.dur);
  const e=k<.5?4*k*k*k:1-Math.pow(-2*k+2,3)/2;
  camera.position.lerpVectors(tween.from.p,tween.to.pos,e);
  controls.target.lerpVectors(tween.from.t,tween.to.target,e);
  camera.lookAt(controls.target);
  if(k>=1){
    const wasHome=tween.name==="home";tween=null;controls.enabled=true;controls.setFromCamera(wasHome);
  }
}

const panel=$("panel"),pBody=$("panel-body");
let panelState=null;
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n}
function openPanel(kind,idx=0){
  panelState={kind,idx};
  pBody.replaceChildren();
  if(kind==="tapes"){
    const p=projects[idx];
    $("panel-eyebrow").textContent=`TAPE ${String(idx+1).padStart(2,"0")} / ${String(projects.length).padStart(2,"0")}`+(p.year?`  ·  ${p.year}`:"");
    $("panel-title").textContent=p.title;
    pBody.append(el("p",p.summary));
    if(p.stack.length){const tags=el("div",undefined,"tags");p.stack.forEach(s=>tags.append(el("span",s)));pBody.append(tags)}
    if(p.link){const a=el("a","View project");a.href=p.link;a.target="_blank";a.rel="noopener noreferrer";const w=el("p");w.append(a);pBody.append(w)}
    const pager=el("div",undefined,"pager");
    const prev=el("button","< PREV"),next=el("button","NEXT >");
    prev.onclick=()=>openPanel("tapes",(idx+projects.length-1)%projects.length);
    next.onclick=()=>openPanel("tapes",(idx+1)%projects.length);
    pager.append(prev,next);pBody.append(pager);
  }else{
    const c={ibm,notepad,credits}[kind];
    $("panel-eyebrow").textContent=c.eyebrow;
    $("panel-title").textContent=c.title;
    (c.paragraphs||[]).forEach(t=>pBody.append(el("p",t)));
    if(c.skills){const tags=el("div",undefined,"tags");c.skills.forEach(s=>tags.append(el("span",s)));pBody.append(tags)}
    const list=c.items||[];
    if(list.length){const ul=el("ul");list.forEach(t=>ul.append(el("li",t)));pBody.append(ul)}
    if(c.links){
      const ul=el("ul");
      c.links.forEach(l=>{const li=el("li"),a=el("a",l.label);a.href=l.href;if(l.href.startsWith("http")){a.target="_blank";a.rel="noopener noreferrer"}li.append(a);ul.append(li)});
      pBody.append(ul);
    }
  }
  panel.hidden=false;
}
function closePanel(){panel.hidden=true;panelState=null}
// The pad lifts off the desk and hangs in front of the camera on the right. Its texture and material never change.
const padScrim=document.createElement("div");padScrim.id="pad-scrim";padScrim.hidden=true;
const padSr=document.createElement("div");padSr.className="pad-sr";padSr.hidden=true;padSr.setAttribute("role","dialog");padSr.setAttribute("aria-label",pad.title);
const padClose=document.createElement("button");padClose.type="button";padClose.id="pad-close";padClose.textContent="PUT DOWN · ESC";padClose.hidden=true;
document.body.append(padScrim,padSr,padClose);
const padRest={pos:padMesh.position.clone(),quat:padMesh.quaternion.clone()};
const padLift={k:0,dir:0,t0:0,from:0};
const _f=new THREE.Vector3(),_r=new THREE.Vector3(),_u=new THREE.Vector3(),_tp=new THREE.Vector3(),_tq=new THREE.Quaternion(),_tilt=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),-0.05);
function padOpen(){return padLift.dir===1}
function liftPad(){
  if(padOpen())return;
  padSr.replaceChildren(el("h2",pad.title));
  pad.sections.forEach(s=>{padSr.append(el("h3",s.head));const ul=el("ul");s.items.forEach(t=>ul.append(el("li",t)));padSr.append(ul)});
  padSr.hidden=false;padScrim.hidden=false;padClose.hidden=false;
  requestAnimationFrame(()=>{padScrim.classList.add("on");padClose.classList.add("on")});
  padMesh.renderOrder=999;
  Object.assign(padLift,{dir:1,t0:performance.now(),from:padLift.k});
  flyTo("work");
}
function dropPad(back=false){
  if(!padOpen())return;
  if(back)flyTo("home");
  padScrim.classList.remove("on");padClose.classList.remove("on");padSr.hidden=true;
  Object.assign(padLift,{dir:-1,t0:performance.now(),from:padLift.k});
}
function stepPad(now){
  if(!padLift.dir)return;
  const dur=reduced?1:1300;
  const p=Math.min(1,(now-padLift.t0)/dur);
  const target=padLift.dir>0?1:0;
  const s=padLift.from+(target-padLift.from)*p;
  padLift.k=s<.5?4*s*s*s:1-Math.pow(-2*s+2,3)/2;
  camera.updateMatrixWorld();
  camera.getWorldDirection(_f);_r.crossVectors(_f,camera.up).normalize();_u.crossVectors(_r,_f);
  _tp.copy(camera.position).addScaledVector(_f,0.5).addScaledVector(_r,0.2);
  _tq.copy(camera.quaternion).multiply(_tilt);
  padMesh.position.lerpVectors(padRest.pos,_tp,padLift.k);
  padMesh.position.y+=Math.sin(Math.PI*padLift.k)*0.06;
  padMesh.quaternion.slerpQuaternions(padRest.quat,_tq,padLift.k);
  padMesh.scale.setScalar(1+0.02*padLift.k);
  padMesh.material.color.set(PAPER_TINT).multiplyScalar(1+0.2*padLift.k);
  if(p>=1){
    if(padLift.dir<0){padMesh.position.copy(padRest.pos);padMesh.quaternion.copy(padRest.quat);padMesh.scale.setScalar(1);padMesh.renderOrder=1;padScrim.hidden=true;padClose.hidden=true}
    if(padLift.dir>0)padLift.t0=-Infinity;else padLift.dir=0;
  }
}
padScrim.addEventListener("click",()=>dropPad(true));
padClose.addEventListener("click",()=>dropPad(true));
addEventListener("keydown",e=>{
  if(e.metaKey||e.ctrlKey||e.altKey||document.getElementById("crt-gate"))return;
  if(e.key==="Escape"&&padOpen()){e.stopImmediatePropagation();dropPad(true)}
  else if(e.key.toLowerCase()==="c")padOpen()?dropPad(true):liftPad();
},true);

function go(name){
  if(name!=="pad")dropPad();
  if(name!=="ibm")term.setActive(false);
  if(name==="tapes"){flyTo("tapes");openPanel("tapes",panelState?.kind==="tapes"?panelState.idx:0)}
  else if(name==="ibm"){flyTo("ibm");closePanel();term.setActive(true)}
  else if(name==="notepad"){flyTo("notepad");openPanel("notepad")}
  else if(name==="pad")liftPad();
  else if(name==="power")toggleTv();
  else if(name==="desk"){flyTo("desk");closePanel()}
  else if(name==="clocks"){flyTo("clocks");closePanel()}
  else{flyTo("home");closePanel()}
}

document.querySelectorAll("[data-view]").forEach(b=>b.addEventListener("click",()=>{
  if(document.documentElement.classList.contains("crt-gating"))return;
  if(b.closest(".menu")&&b.dataset.view==="pad"&&padOpen()){dropPad(true);return}
  go(b.dataset.view);
}));
$("home-link").addEventListener("click",()=>{if(!document.documentElement.classList.contains("crt-gating"))go("home")});
const menuLinks=[...document.querySelectorAll(".menu [data-view]")];let menuCur="";
function syncMenu(){
  const cur=padOpen()?"pad":term.active?"ibm":"";
  if(cur===menuCur)return;menuCur=cur;
  menuLinks.forEach(b=>b.dataset.view===cur?b.setAttribute("aria-current","page"):b.removeAttribute("aria-current"));
}
$("panel-close").addEventListener("click",()=>go("home"));
$("btn-credits").addEventListener("click",()=>{panelState?.kind==="credits"?closePanel():openPanel("credits")});
addEventListener("keydown",e=>{
  if(e.metaKey||e.ctrlKey||e.altKey)return;
  const k=e.key.toLowerCase();
  if(k==="t")go("tapes");
  else if(k==="i")go("ibm");
  else if(k==="n")go("pad");
  else if(k==="z")go("desk");
  else if(k==="k")go("clocks");
  else if(k==="p")go("power");
  else if(k==="escape"){go("home")}
});

const audio=new Ambience();
const soundBtn=$("btn-sound"),lofiBtn=$("btn-lofi");
soundBtn.addEventListener("click",async()=>{
  const on=!audio.rainOn;
  await audio.setRain(on);
  soundBtn.textContent=on?"SOUND ON":"SOUND OFF";soundBtn.setAttribute("aria-pressed",String(on));
});
lofiBtn.addEventListener("click",async()=>{
  const on=!audio.lofiOn;
  await audio.setLofi(on);
  lofiBtn.setAttribute("aria-pressed",String(on));
});


function moveHint(h,ev){
  const flip=ev.clientX>innerWidth*0.55;
  h.style.setProperty("--tx",(flip?ev.clientX-12:ev.clientX+12)+"px");h.style.setProperty("--fx",flip?"-100%":"0%");
  h.style.setProperty("--ty",ev.clientY+14+"px");
}
// Every clickable thing says what a click does, in the hint that follows the cursor.
function tipFor3d(h){
  switch(h.kind){
    case"tapes":return "CLICK TO OPEN: "+projects[h.idx].title;
    case"ibm":return "CLICK TO USE THE IBM PC";
    case"pad":return "CLICK TO LIFT THE WORK NOTES";
    case"power":return tv.on?"CLICK TO TURN OFF THE TV":"CLICK TO TURN ON THE TV";
    default:return "CLICK TO OPEN THE NOTEPAD";
  }
}
const VIEW_TIPS={tapes:"CLICK TO LOOK AT THE TAPES · KEY T",ibm:"CLICK TO USE THE IBM PC · KEY I",pad:"CLICK TO LIFT THE WORK NOTES · KEY N",desk:"CLICK TO ZOOM IN ON THE DESK · KEY Z",
  clocks:"CLICK TO LOOK AT THE CLOCKS · KEY K",
  power:()=>(tv.on?"CLICK TO TURN OFF THE TV":"CLICK TO TURN ON THE TV")+" · KEY P"};
function tipFor(el){
  if(el.id==="pad-scrim")return "CLICK ANYWHERE TO PUT THE PAPER BACK DOWN";
  const b=el.closest("button,a");if(!b)return null;
  if(b.dataset.tip)return b.dataset.tip;
  if(b.dataset.view){const t=VIEW_TIPS[b.dataset.view];return typeof t==="function"?t():t||null}
  switch(b.id){
    case"pad-close":return "CLICK TO PUT THE PAPER BACK DOWN · ESC";
    case"panel-close":return "CLICK TO CLOSE AND GO BACK TO THE DESK · ESC";
    case"btn-credits":return "CLICK TO SEE THE CREDITS";
    case"btn-sound":return audio.rainOn?"CLICK TO TURN THE RAIN SOUND OFF":"CLICK TO TURN THE RAIN SOUND ON";
    case"btn-lofi":return audio.lofiOn?"CLICK TO STOP THE LO-FI MUSIC":"CLICK TO PLAY LO-FI MUSIC";
  }
  const t=b.textContent.trim();
  if(t.startsWith("<"))return "CLICK FOR THE PREVIOUS TAPE";
  if(t.startsWith("NEXT"))return "CLICK FOR THE NEXT TAPE";
  if(b.tagName==="A")return "CLICK TO OPEN THIS LINK IN A NEW TAB";
  return null;
}
document.addEventListener("pointermove",ev=>{
  if(ev.pointerType!=="mouse"||ev.target===canvas)return;
  const h=$("hint"),t=tipFor(ev.target);
  moveHint(h,ev);
  if(t){h.textContent=t;h.classList.add("show")}else h.classList.remove("show");
});
document.addEventListener("pointerleave",()=>$("hint").classList.remove("show"));

const ray=new THREE.Raycaster();
const ptr=new THREE.Vector2();
let hover=null;
function pick(ev){
  const r=canvas.getBoundingClientRect();
  ptr.set(((ev.clientX-r.left)/r.width)*2-1,-((ev.clientY-r.top)/r.height)*2+1);
  ray.setFromCamera(ptr,camera);
  const targets=["Room_Tapes","Room_Station","Room_Desk"].map(n=>meshes[n]).filter(Boolean);
  targets.push(padMesh,tvButton.hit);
  const hit=ray.intersectObjects(targets,false)[0];
  if(!hit)return null;
  const n=hit.object.name;
  if(n==="Pad")return {kind:"pad"};
  if(n==="TvPower")return {kind:"power"};
  if(n==="Room_Tapes"){
    const idx=tapeAt(hit.point);
    return idx===null?null:{kind:"tapes",idx};
  }
  if(n==="Room_Station")return {kind:"ibm"};
  if(Math.hypot(hit.point.x+0.47,hit.point.z+1.84)<0.3&&hit.point.y<0.95)return {kind:"notepad"};
  return null;
}
canvas.addEventListener("pointermove",ev=>{
  if(ev.pointerType!=="mouse"||tween||ev.buttons)return;
  hover=pick(ev);
  canvas.classList.toggle("hot",!!hover);
  const h=$("hint");
  moveHint(h,ev);
  if(hover){h.textContent=tipFor3d(hover);h.classList.add("show")}
  else h.classList.remove("show");
});
let down=null;
canvas.addEventListener("pointerdown",ev=>{down={x:ev.clientX,y:ev.clientY}});
canvas.addEventListener("pointerup",ev=>{
  if(!down||tween)return;
  const moved=Math.hypot(ev.clientX-down.x,ev.clientY-down.y);down=null;
  if(moved>6||controls.clickBlocked)return;     // a drag or pinch is never a click
  if(term.active){
    const r=canvas.getBoundingClientRect();
    ptr.set(((ev.clientX-r.left)/r.width)*2-1,-((ev.clientY-r.top)/r.height)*2+1);
    ray.setFromCamera(ptr,camera);
    const th=ray.intersectObject(term.mesh,false)[0];
    if(th){term.clickAt(th.uv);return}
  }
  const hit=pick(ev);
  if(!hit)return;
  if(hit.kind==="tapes"){flyTo("tapes");openPanel("tapes",hit.idx)}
  else go(hit.kind);
});

const composer=new EffectComposer(renderer,new THREE.WebGLRenderTarget(1,1,{type:THREE.HalfFloatType,samples:4}));
composer.addPass(new RenderPass(scene,camera));
const bloom=new UnrealBloomPass(new THREE.Vector2(1,1),0.7,0.6,0.88);
composer.addPass(bloom);
composer.addPass(new OutputPass());
function resize(){
  const w=innerWidth,h=innerHeight;
  renderer.setSize(w,h,false);composer.setSize(w,h);steamU.uPx.value=h*renderer.getPixelRatio()/(2*Math.tan(camera.fov*Math.PI/360));
  camera.aspect=w/h;
  // Portrait keeps 64 deg; landscape keeps the same desk width in frame on any screen shape
  // (38 deg at 2.2:1, ~46 deg at 16:9), clamped to 36-50 deg.
  camera.fov=w/h<1?64:Math.min(50,Math.max(36,2*Math.atan(0.761/(w/h))*180/Math.PI));
  camera.updateProjectionMatrix();
}
addEventListener("resize",resize);resize();

function frame(now){
  requestAnimationFrame(frame);
  stepTween(now);
  if(controls.enabled)controls.update();
  stepPad(now);
  crtGlass.uniforms.uTime.value=reduced?0:now/1000;
  crtLive.uTime.value=reduced?0:now/1000;if(now-(crtScreen.last||0)>50){crtScreen.last=now;crtScreen.draw(reduced?0:now)}term.step(now,reduced);ibmLights.step(now);rainU.uTime.value=reduced?0:now/1000;steamU.uTime.value=reduced?3:now/1000;windU.uTime.value=reduced?0:now/1000;stepTv(now);syncMenu();if(clock.tex)drawClock(reduced?0:Math.floor((now-clock.t0)/1000));
  composer.render();
}

// The old sheet is part of the room's geometry. Taking its triangles out leaves the desk top that was under it.
function hideSheet(){
  const c=Math.cos(UNDER.rotY),s=Math.sin(UNDER.rotY),v=new THREE.Vector3(),removed={};
  const inside=p=>{const dx=p.x-UNDER.x,dz=p.z-UNDER.z,u=dx*c-dz*s,w=dx*s+dz*c;return Math.abs(u)<0.17&&Math.abs(w)<0.12};
  for(const [name,m] of Object.entries(meshes)){
    const g=m.geometry,pos=g.attributes.position,idx=g.index;
    if(!idx)continue;
    m.updateWorldMatrix(true,false);
    const keep=[],n=idx.count;
    for(let i=0;i<n;i+=3){
      let all=true,hi=false;
      for(let j=0;j<3;j++){
        v.fromBufferAttribute(pos,idx.getX(i+j)).applyMatrix4(m.matrixWorld);
        if(!inside(v))all=false;
        if(v.y>0.7215&&v.y<0.74)hi=true;
      }
      if(all&&hi)removed[name]=(removed[name]||0)+1;
      else keep.push(idx.getX(i),idx.getX(i+1),idx.getX(i+2));
    }
    if(removed[name])g.setIndex(keep);
  }
  console.log("pad-sheet removed triangles",JSON.stringify(removed));
}

// Curtains sway in the wind. The baked light stays fixed; only the vertices move. Curtain_L/R sit at x -1.21..-0.83 and 0.92..1.31, z -2.47..-2.33.
const windU={uTime:{value:0}};
function setupWind(){
  const mesh=meshes.Room_Window,mat=mesh&&mesh.material;if(!mat)return;
  const g=mesh.geometry,pos=g.attributes.position,a=new Float32Array(pos.count*2);let n=0;
  for(let i=0;i<pos.count;i++){
    const x=pos.getX(i),y=pos.getY(i),z=pos.getZ(i);
    if(z<-2.49||z>-2.32)continue;
    const left=x>-1.23&&x<-0.82,right=x>0.91&&x<1.32;if(!left&&!right)continue;
    const h=Math.min(1,Math.max(0,(2.45-y)/(2.45-0.76)));
    const free=left?(x+1.2)/0.37:(1.3-x)/0.37;
    a[i*2]=Math.pow(h,1.6)*(0.4+0.6*Math.min(1,Math.max(0,free)));a[i*2+1]=left?0:2.1;n++;
  }
  g.setAttribute("aWind",new THREE.BufferAttribute(a,2));
  mat.onBeforeCompile=sh=>{
    sh.uniforms.uTime=windU.uTime;
    sh.vertexShader="uniform float uTime;attribute vec2 aWind;\n"+sh.vertexShader.replace("#include <begin_vertex>",`#include <begin_vertex>
      float wt=uTime;float gust=0.55+0.45*sin(wt*0.43+aWind.y)*sin(wt*0.29+1.3);
      float sw=sin(wt*1.15-aWind.x*2.6+aWind.y+position.x*2.2)+0.5*sin(wt*2.1-aWind.x*4.1+position.x*3.3);
      transformed.z+=aWind.x*0.2*(0.45+0.45*sw*gust);
      transformed.x+=aWind.x*0.12*sin(wt*0.95-aWind.x*2.2+aWind.y)*(0.5+0.5*gust);`);
  };
  mat.needsUpdate=true;
  console.log("curtain wind vertices",n);
}

// Plant: leaves and stems sway in the same wind as the curtains. The pot, soil and stones (below y 0.936) stay still.
function setupPlant(){
  const mesh=meshes.Room_Plant,mat=mesh&&mesh.material;if(!mat)return;
  const g=mesh.geometry,pos=g.attributes.position,a=new Float32Array(pos.count),v=new THREE.Vector3();let n=0;
  mesh.updateWorldMatrix(true,false);
  for(let i=0;i<pos.count;i++){
    v.fromBufferAttribute(pos,i).applyMatrix4(mesh.matrixWorld);
    const up=Math.min(1,Math.max(0,(v.y-0.93)/0.3)),out=Math.min(1,Math.hypot(v.x+0.9,v.z+2.04)/0.5);
    const w=up*up*(3-2*up)*(0.25+0.75*out);
    a[i]=w;if(w>0)n++;
  }
  g.setAttribute("aSway",new THREE.BufferAttribute(a,1));
  const prev=mat.onBeforeCompile;
  mat.onBeforeCompile=(sh,r)=>{
    if(prev)prev(sh,r);
    sh.uniforms.uTime=windU.uTime;
    sh.vertexShader="uniform float uTime;attribute float aSway;\n"+sh.vertexShader.replace("#include <begin_vertex>",`#include <begin_vertex>
      vec3 wp0=(modelMatrix*vec4(position,1.0)).xyz;float ph=wp0.x*4.1+wp0.z*3.3+wp0.y*1.7;
      float gu=0.55+0.45*sin(uTime*0.43)*sin(uTime*0.29+1.3);
      vec3 dw=vec3(sin(uTime*1.35+ph)*0.6+sin(uTime*2.7+ph*1.7)*0.25,sin(uTime*1.9+ph*1.3)*0.22,cos(uTime*1.15+ph*0.8)*0.5+0.18)*aSway*0.07*(0.5+0.8*gu);
      transformed+=transpose(mat3(modelMatrix))*dw;`);
  };
  mat.needsUpdate=true;
  console.log("plant sway vertices",n);
}

// TV power: the VCR's red key (VCR_Btn_5, x .1397..1525, y .7430..7520, z -2.047) is redrawn a little larger and switches the CRT off and on.
// The screen collapses to a line, then a dot, then goes dark; switching it back on runs the same thing in reverse.
const tv={off:0,dir:0,on:true,last:0};
const tvU={uOff:{value:0}};
const tvScreen=(()=>{
  const W=CRT.w*1.04,H=CRT.h*1.05;
  const m=new THREE.ShaderMaterial({uniforms:tvU,transparent:true,depthWrite:false,
    vertexShader:`varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
    fragmentShader:`uniform float uOff;varying vec2 vUv;
      float ease(float x){return x<.5?2.*x*x:1.-pow(-2.*x+2.,2.)/2.;}
      void main(){
        vec2 q=vUv-.5;vec2 p=q*vec2(${W.toFixed(4)},${H.toFixed(4)});
        float r=.016;float d=length(max(abs(p)-vec2(${W.toFixed(4)},${H.toFixed(4)})*.5+r,0.))-r;float mask=smoothstep(.0015,-.0015,d);
        float e1=ease(clamp(uOff/.55,0.,1.)),e2=ease(clamp((uOff-.55)/.25,0.,1.)),fade=clamp((uOff-.8)/.2,0.,1.);
        float hh=mix(.5,.004,e1),hw=mix(.5,.012,e2);
        float inside=smoothstep(hw+.012,hw-.004,abs(q.x))*smoothstep(hh+.004,hh-.002,abs(q.y));
        float glow=e1*e1*e1*(1.-fade);
        vec3 inC=mix(vec3(1.5,1.65,2.0),vec3(.01,.012,.018),fade);
        float inA=mix(glow*.92,1.,fade);
        vec3 col=mix(vec3(.01,.012,.018),inC,inside);
        float a=mix(.985,inA,inside)*mask;
        gl_FragColor=vec4(col,a);
      }`});
  const mesh=new THREE.Mesh(new THREE.PlaneGeometry(W,H),m);
  mesh.position.set(CRT.cx,CRT.cy,CRT.z+0.0035);mesh.renderOrder=1.5;mesh.visible=false;mesh.name="TvScreen";scene.add(mesh);
  return mesh;
})();
const tvButton=(()=>{
  const cv=document.createElement("canvas");cv.width=256;cv.height=176;const x=cv.getContext("2d");
  const rr=(px,py,w,h,r)=>{x.beginPath();x.roundRect(px,py,w,h,r)};
  rr(2,2,252,172,34);x.fillStyle="#2a0a08";x.fill();
  const g=x.createLinearGradient(0,10,0,166);g.addColorStop(0,"#ff4a36");g.addColorStop(.55,"#e02a1c");g.addColorStop(1,"#a81610");
  rr(10,10,236,156,28);x.fillStyle=g;x.fill();
  x.fillStyle="rgba(255,255,255,.28)";rr(24,18,208,30,15);x.fill();
  const t=new THREE.CanvasTexture(cv);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;
  const mesh=new THREE.Mesh(new THREE.PlaneGeometry(0.0188,0.0129),new THREE.MeshBasicMaterial({map:t}));
  mesh.position.set(0.1461,0.7475,-2.0461);mesh.renderOrder=2;mesh.name="TvPowerBtn";scene.add(mesh);
  const hit=new THREE.Mesh(new THREE.PlaneGeometry(0.034,0.024),new THREE.MeshBasicMaterial({transparent:true,opacity:0,depthWrite:false}));
  hit.position.set(0.1461,0.7475,-2.0455);hit.name="TvPower";scene.add(hit);
  return {mesh,hit};
})();
function setTv(on){
  tv.on=on;tv.dir=on?-1:1;tvScreen.visible=true;
}
function toggleTv(){setTv(!tv.on)}
function stepTv(now){
  const dt=Math.min(.1,(now-tv.last)/1000);tv.last=now;
  if(!tv.dir)return;
  const dur=reduced?0.01:(tv.dir>0?1.0:0.8);
  tv.off=Math.min(1,Math.max(0,tv.off+tv.dir*dt/dur));
  tvU.uOff.value=tv.off;
  const f=1-Math.min(1,Math.max(0,(tv.off-.05)/.5));
  spill.material.opacity=f;spill.visible=f>0.01;
  tvButton.mesh.material.color.setScalar(1-0.55*Math.min(1,tv.off*3));
  if(tv.off<=0){tv.dir=0;tvScreen.visible=false}
  else if(tv.off>=1)tv.dir=0;
}

// VCR display: the baked "23:05" is part of the lightmap, so a live readout is drawn over the plate (VCR_LCD, x .085...146, y .7615...7915, z -2.0475).
const clock={tex:null,ctx:null,key:"",t0:performance.now()};
function setupClock(){
  const cv=document.createElement("canvas");cv.width=640;cv.height=300;
  clock.ctx=cv.getContext("2d");
  clock.tex=new THREE.CanvasTexture(cv);clock.tex.colorSpace=THREE.SRGBColorSpace;clock.tex.anisotropy=8;
  const mesh=new THREE.Mesh(new THREE.PlaneGeometry(0.040,0.0187),new THREE.MeshBasicMaterial({map:clock.tex}));
  mesh.position.set(0.11555,0.77745-0.0044,-2.0465);mesh.renderOrder=2;mesh.name="VcrClock";scene.add(mesh);
  drawClock(0);
}
function drawClock(sec){
  const total=23*3600+5*60+sec,s=total%60,mi=Math.floor(total/60)%60,h=Math.floor(total/3600)%24;
  const key=h+":"+mi+":"+s;if(key===clock.key)return;clock.key=key;
  const c=clock.ctx,p=n=>String(n).padStart(2,"0");
  c.fillStyle="#020802";c.fillRect(0,0,640,300);
  c.fillStyle=CLOCK_INK;c.textBaseline="alphabetic";c.textAlign="left";
  c.font="190px 'DejaVu Sans Mono',Menlo,Consolas,monospace";
  const cw=c.measureText("0").width,x0=(640-cw*5)/2,base=205;
  c.fillText(p(h),x0,base);c.fillText(p(mi),x0+cw*3,base);
  if(s%2===0)c.fillText(":",x0+cw*2,base);
  c.font="62px 'DejaVu Sans Mono',Menlo,Consolas,monospace";c.textAlign="right";
  c.fillText(p(s),x0+cw*5,285);
  clock.tex.needsUpdate=true;
}
const CLOCK_INK="#cdeeee";

Promise.all([roomP,outP,viewP,tapesP]).then(()=>{
  hideSheet();
  try{setupWind()}catch(e){console.warn("wind failed",e)}
  try{setupPlant()}catch(e){console.warn("plant failed",e)}
  try{setupClock()}catch(e){console.warn("clock failed",e)}
  buildViews();
  const l=$("loader");l.classList.add("done");
  setTimeout(()=>l.remove(),1000);
  requestAnimationFrame(frame);
}).catch(err=>{
  console.error(err);
  $("loader-text").textContent="FAILED TO LOAD SCENE";
});
