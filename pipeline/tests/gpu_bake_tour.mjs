import {chromium} from 'playwright';
const url=process.argv[2]||'http://localhost:8765/gpu-test.html';
const pre=process.argv[3]||'gpu';
const D='/home/wali/v3-local-test/shots/'+pre+'-';
const b=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=gl-egl','--ignore-gpu-blocklist','--enable-unsafe-swiftshader']});
const p=await b.newPage({viewport:{width:1440,height:810}});
const logs=[],fails=[],reqs=[];
p.on('console',m=>{if(['error','warning'].includes(m.type()))logs.push(m.type()+': '+m.text())});
p.on('pageerror',e=>logs.push('pageerror: '+e.message));
p.on('requestfailed',r=>fails.push(r.url()));
p.on('response',r=>{reqs.push(r.status()+' '+r.url().split('/').pop());if(r.status()>=400)fails.push(r.status()+' '+r.url())});
await p.goto(url);await p.waitForTimeout(12000);
const shot=async n=>{await p.waitForTimeout(1800);await p.screenshot({path:D+n+'.png'});console.log('shot',n)};
const panel=async()=>p.evaluate(()=>{const e=document.getElementById('panel');return e.hidden?'closed':document.getElementById('panel-title').textContent});
const drag=async(dx,dy)=>{await p.mouse.move(720,400);await p.mouse.down();await p.mouse.move(720+dx,400+dy,{steps:15});await p.mouse.up();await p.waitForTimeout(1500)};
await shot('01-home');
// tape click from home
await p.mouse.click(1000,470);await p.waitForTimeout(2500);console.log('tape click ->',await panel());await shot('02-tape-panel');
await p.keyboard.press('Escape');await p.waitForTimeout(2200);
for(const [k,n] of [['t','03-tapes'],['i','04-ibm'],['n','05-notepad'],['z','06-desk']]){
  await p.keyboard.press(k);await p.waitForTimeout(2400);console.log(k,'->',await panel());await shot(n);}
await p.keyboard.press('Escape');await p.waitForTimeout(2200);console.log('esc ->',await panel());
// drags
await drag(400,0);await shot('07-drag-right');           // swings camera left?
await drag(-900,0);await shot('08-drag-left');
await drag(400,0);
await drag(0,150);await shot('09-drag-down');
await drag(0,-300);await shot('10-drag-up');
// zoom limits
await p.keyboard.press('Escape');await p.waitForTimeout(2200);
for(let i=0;i<30;i++){await p.mouse.wheel(0,-300);await p.waitForTimeout(40)}await shot('11-zoom-in-max');
for(let i=0;i<60;i++){await p.mouse.wheel(0,300);await p.waitForTimeout(40)}await shot('12-zoom-out-max');
// perf
const fps=await p.evaluate(()=>new Promise(r=>{let n=0,t0=performance.now(),mx=0,last=t0;function f(t){n++;mx=Math.max(mx,t-last);last=t;if(t-t0<4000)requestAnimationFrame(f);else r({fps:n/((t-t0)/1000),worstFrameMs:mx})}requestAnimationFrame(f)}));
console.log('perf',JSON.stringify(fps));
console.log('requests',reqs.filter(r=>/glb|json|jpg|png|bin/.test(r)).join(' | '));
console.log(JSON.stringify({logs,fails}));
await b.close();
