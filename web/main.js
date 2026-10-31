import * as THREE from "three";
import {OrbitControls} from "three/addons/controls/OrbitControls.js";
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
renderer.useLegacyLights=false;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.0;
renderer.setClearColor(0x07050a);

const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(46,1,0.05,120);
const HOME={pos:new THREE.Vector3(0.12,0.86,-0.3),target:new THREE.Vector3(0.1,0.98,-1.8)};
camera.position.copy(HOME.pos);

const controls=new OrbitControls(camera,canvas);
controls.enablePan=true;
controls.panSpeed=0.6;
controls.enableDamping=true;
controls.dampingFactor=0.05;
controls.rotateSpeed=0.7;
controls.zoomSpeed=0.8;
controls.target.copy(HOME.target);

function limitAround(){
  // Free orbit — no angle restrictions
  controls.minAzimuthAngle=-Infinity;
  controls.maxAzimuthAngle=Infinity;
  controls.minPolarAngle=0.2;
  controls.maxPolarAngle=Math.PI*0.85;
  controls.minDistance=0.5;
  controls.maxDistance=12;
}
controls.update();limitAround();

const draco=new DRACOLoader();
draco.setDecoderPath("https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/libs/draco/gltf/");
const loader=new GLTFLoader();
loader.setDRACOLoader(draco);
const meshes={};
const objs={};   // all named Object3D (groups + meshes)
let progressRoom=0,progressOut=0;
function setProgress(){
  const p=Math.round((progressRoom*0.9+progressOut*0.1)*100);
  $("loader-fill").style.width=p+"%";$("loader-text").textContent="LOADING "+p+"%";
}
const roomP=new Promise((res,rej)=>loader.load("sakina-room-v3.glb",g=>{
  const maxAniso=renderer.capabilities.getMaxAnisotropy();
  g.scene.traverse(o=>{
    if(o.name)objs[o.name]=o;
    // Blender volumetric haze: glTF has no volume shaders, so it arrives as an opaque white box around the camera.
    if(o.name==="Room_Volume"){o.visible=false;return;}
    // Blender exports lights in candela (W*683/4pi) while emissive strengths stay radiometric; convert back to W/sr.
    if(o.isLight){o.intensity/=683;return;}
    if(!o.isMesh)return;
    meshes[o.name]=o;
    const m=o.material;
    if(m.emissiveMap){m.emissiveMap.anisotropy=Math.min(8,maxAniso)}
    m.envMapIntensity=0;
  });
  scene.add(g.scene);res();
},e=>{if(e.lengthComputable){progressRoom=e.loaded/e.total;setProgress()}},rej));
const outP=new Promise((res,rej)=>loader.load("sakina-outside.glb",g=>{scene.add(g.scene);res()},
  e=>{if(e.lengthComputable){progressOut=e.loaded/e.total;setProgress()}},rej));

const box=name=>new THREE.Box3().setFromObject(objs[name]);
const DESK_TOP=0.72;
function deskTapeBox(){
  const b=new THREE.Box3();
  for(let i=1;i<=7;i++){
    const g=objs['PTape_'+i];
    if(g)b.expandByObject(g);
  }
  return b;
}
let tapeBox;
function tapeIndex(p){
  const gap=(tapeBox.min.x+tapeBox.max.x)/2;
  return p.x<gap?{stack:0,n:6}:{stack:1,n:7};
}
let VIEWS;
function buildViews(){
  tapeBox=deskTapeBox();
  const tapes=tapeBox.getCenter(new THREE.Vector3());
  const ibmC=box("Station_Root").getCenter(new THREE.Vector3());
  ibmC.y+=0.3;
  const deskBox=box("Desk_Top");
  const deskC=deskBox.getCenter(new THREE.Vector3());
  const note=new THREE.Vector3(-0.45,0.76,-1.36);
  VIEWS={
    home:{target:HOME.target.clone(),pos:HOME.pos.clone()},
    tapes:{target:tapes.clone(),pos:tapes.clone().add(new THREE.Vector3(0,0.35,0.95))},
    ibm:{target:ibmC.clone().add(new THREE.Vector3(0,-0.05,0)),pos:ibmC.clone().add(new THREE.Vector3(1.15,0.12,0.25))},
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
    tween=null;controls.enabled=true;controls.update();limitAround();
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
const mouse={x:0,y:0,sx:0,sy:0};
let hover=null;
function pick(ev){
  const r=canvas.getBoundingClientRect();
  ptr.set(((ev.clientX-r.left)/r.width)*2-1,-((ev.clientY-r.top)/r.height)*2+1);
  ray.setFromCamera(ptr,camera);
  // collect tape child meshes (PTape_1..7 are groups; their children are meshes)
  const tapeMeshes=[];
  for(let i=1;i<=7;i++){
    const g=objs['PTape_'+i];
    if(g)g.traverse(o=>{if(o.isMesh)tapeMeshes.push(o)});
  }
  const ibmMesh=meshes['PC_Unit'];
  const deskMesh=meshes['Desk_Top'];
  const targets=[...tapeMeshes,ibmMesh,deskMesh].filter(Boolean);
  const hit=ray.intersectObjects(targets,false)[0];
  if(!hit)return null;
  const n=hit.object.name;
  // tape hit: any PTape_N or PTape_N_* child
  if(/^PTape_\d/.test(n)){
    const {stack,n:slots}=tapeIndex(hit.point);
    const h=tapeBox.max.y-DESK_TOP;
    const row=Math.min(slots-1,Math.max(0,Math.floor(((tapeBox.max.y-hit.point.y)/h)*slots)));
    return {kind:"tapes",idx:stack===0?row:6+row};
  }
  if(n==='PC_Unit')return {kind:"ibm"};
  if(Math.hypot(hit.point.x+0.45,hit.point.z+1.36)<0.3&&hit.point.y<0.95)return {kind:"notepad"};
  return null;
}
canvas.addEventListener("pointermove",ev=>{
  mouse.x=(ev.clientX/innerWidth)*2-1;mouse.y=(ev.clientY/innerHeight)*2-1;
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
  if(moved>6)return;
  const hit=pick(ev);
  if(!hit)return;
  if(hit.kind==="tapes"){flyTo("tapes");openPanel("tapes",hit.idx)}
  else go(hit.kind);
});

function resize(){
  const w=innerWidth,h=innerHeight;
  renderer.setSize(w,h,false);
  camera.aspect=w/h;
  camera.fov=w/h<1?64:46;
  camera.updateProjectionMatrix();
}
addEventListener("resize",resize);resize();

function frame(now){
  requestAnimationFrame(frame);
  stepTween(now);
  if(controls.enabled)controls.update();
  if(!reduced){
    mouse.sx+=(mouse.x-mouse.sx)*0.05;mouse.sy+=(mouse.y-mouse.sy)*0.05;
    const w=innerWidth,h=innerHeight;
    camera.setViewOffset(w,h,mouse.sx*w*0.012,mouse.sy*h*0.012,w,h);
  }
  renderer.render(scene,camera);
}

Promise.all([roomP,outP]).then(()=>{
  buildViews();
  const l=$("loader");l.classList.add("done");
  setTimeout(()=>l.remove(),1000);
  requestAnimationFrame(frame);
}).catch(err=>{
  console.error(err);
  $("loader-text").textContent="FAILED TO LOAD SCENE";
});
