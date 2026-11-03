import * as THREE from "three";
import {LookControls} from "./look-controls.js?v=5";
import {GLTFLoader} from "three/addons/loaders/GLTFLoader.js";
import {DRACOLoader} from "three/addons/loaders/DRACOLoader.js";
import {projects,ibm,notepad,credits} from "./content.js";
import {Ambience} from "./audio.js";

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
let TAPES=[];
const tapesP=fetch("tapes.json").then(r=>r.json()).then(t=>{TAPES=t.map(d=>({idx:d.idx,box:new THREE.Box3(new THREE.Vector3(...d.min),new THREE.Vector3(...d.max))}))});
const roomP=new Promise((res,rej)=>loader.load("sakina-room-std.glb",g=>{
  const maxAniso=renderer.capabilities.getMaxAnisotropy();
  g.scene.traverse(o=>{
    if(!o.isMesh)return;
    meshes[o.name]=o;
    const m=o.material;
    if(m.emissiveMap){m.emissiveMap.anisotropy=Math.min(8,maxAniso)}
    m.envMapIntensity=0;
  });
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

const box=name=>new THREE.Box3().setFromObject(meshes[name]);
const DESK_TOP=0.72;
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
    ibm:{target:ibmC.clone().add(new THREE.Vector3(0,-0.05,0)),pos:ibmC.clone().add(new THREE.Vector3(1.12,0.25,0.42))},
    notepad:{target:note.clone(),pos:note.clone().add(new THREE.Vector3(0.05,0.62,0.55))},
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

function go(name){
  if(name==="tapes"){flyTo("tapes");openPanel("tapes",panelState?.kind==="tapes"?panelState.idx:0)}
  else if(name==="ibm"){flyTo("ibm");openPanel("ibm")}
  else if(name==="notepad"){flyTo("notepad");openPanel("notepad")}
  else if(name==="desk"){flyTo("desk");closePanel()}
  else{flyTo("home");closePanel()}
}

document.querySelectorAll("[data-view]").forEach(b=>b.addEventListener("click",()=>go(b.dataset.view)));
$("panel-close").addEventListener("click",()=>go("home"));
$("btn-credits").addEventListener("click",()=>{panelState?.kind==="credits"?closePanel():openPanel("credits")});
addEventListener("keydown",e=>{
  if(e.metaKey||e.ctrlKey||e.altKey)return;
  const k=e.key.toLowerCase();
  if(k==="t")go("tapes");
  else if(k==="i")go("ibm");
  else if(k==="n")go("notepad");
  else if(k==="z")go("desk");
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

const ray=new THREE.Raycaster();
const ptr=new THREE.Vector2();
let hover=null;
function pick(ev){
  const r=canvas.getBoundingClientRect();
  ptr.set(((ev.clientX-r.left)/r.width)*2-1,-((ev.clientY-r.top)/r.height)*2+1);
  ray.setFromCamera(ptr,camera);
  const targets=["Room_Tapes","Room_Station","Room_Desk"].map(n=>meshes[n]).filter(Boolean);
  const hit=ray.intersectObjects(targets,false)[0];
  if(!hit)return null;
  const n=hit.object.name;
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
  if(hover){h.textContent=hover.kind==="tapes"?"TAPES":hover.kind==="ibm"?"IBM PC":"NOTEPAD";h.classList.add("show")}
  else h.classList.remove("show");
});
let down=null;
canvas.addEventListener("pointerdown",ev=>{down={x:ev.clientX,y:ev.clientY}});
canvas.addEventListener("pointerup",ev=>{
  if(!down||tween)return;
  const moved=Math.hypot(ev.clientX-down.x,ev.clientY-down.y);down=null;
  if(moved>6||controls.clickBlocked)return;     // a drag or pinch is never a click
  const hit=pick(ev);
  if(!hit)return;
  if(hit.kind==="tapes"){flyTo("tapes");openPanel("tapes",hit.idx)}
  else go(hit.kind);
});

function resize(){
  const w=innerWidth,h=innerHeight;
  renderer.setSize(w,h,false);
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
  crtGlass.uniforms.uTime.value=reduced?0:now/1000;
  renderer.render(scene,camera);
}

Promise.all([roomP,outP,viewP,tapesP]).then(()=>{
  buildViews();
  const l=$("loader");l.classList.add("done");
  setTimeout(()=>l.remove(),1000);
  requestAnimationFrame(frame);
}).catch(err=>{
  console.error(err);
  $("loader-text").textContent="FAILED TO LOAD SCENE";
});
