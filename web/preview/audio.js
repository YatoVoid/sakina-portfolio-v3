export class Ambience {
  constructor(){
    this.ctx=null;this.rainOn=false;this.lofiOn=false;this.timer=null;this.step=0;
  }
  init(){
    if(this.ctx)return;
    const ctx=this.ctx=new AudioContext();
    this.master=ctx.createGain();this.master.gain.value=0.9;this.master.connect(ctx.destination);
    this.rainGain=ctx.createGain();this.rainGain.gain.value=0;this.rainGain.connect(this.master);
    const len=ctx.sampleRate*4;
    const buf=ctx.createBuffer(2,len,ctx.sampleRate);
    for(let c=0;c<2;c++){
      const d=buf.getChannelData(c);let last=0;
      for(let i=0;i<len;i++){const w=Math.random()*2-1;last=(last+0.02*w)/1.02;d[i]=w*0.6+last*3.5}
    }
    const src=ctx.createBufferSource();src.buffer=buf;src.loop=true;
    const hp=ctx.createBiquadFilter();hp.type="highpass";hp.frequency.value=700;
    const lp=ctx.createBiquadFilter();lp.type="lowpass";lp.frequency.value=7500;
    const lfo=ctx.createOscillator();lfo.frequency.value=0.13;
    const lfoG=ctx.createGain();lfoG.gain.value=0.05;
    lfo.connect(lfoG).connect(this.rainGain.gain);lfo.start();
    src.connect(hp).connect(lp).connect(this.rainGain);src.start();
    this.lofiGain=ctx.createGain();this.lofiGain.gain.value=0;
    const tone=ctx.createBiquadFilter();tone.type="lowpass";tone.frequency.value=1800;
    const wob=ctx.createOscillator();wob.frequency.value=0.35;
    const wobG=ctx.createGain();wobG.gain.value=8;
    this.lofiGain.connect(tone).connect(this.master);
    this.wobG=wobG;wob.connect(wobG);wob.start();
    this.crackle=this.makeCrackle();
  }
  makeCrackle(){
    const ctx=this.ctx,len=ctx.sampleRate*3,buf=ctx.createBuffer(1,len,ctx.sampleRate),d=buf.getChannelData(0);
    for(let i=0;i<len;i++)d[i]=Math.random()<0.0009?(Math.random()*2-1)*0.9:0;
    const s=ctx.createBufferSource();s.buffer=buf;s.loop=true;
    const g=ctx.createGain();g.gain.value=0.05;
    s.connect(g).connect(this.lofiGain);s.start();
    return s;
  }
  async setRain(on){
    this.init();await this.ctx.resume();this.rainOn=on;
    this.rainGain.gain.cancelScheduledValues(this.ctx.currentTime);
    this.rainGain.gain.setTargetAtTime(on?0.32:0,this.ctx.currentTime,0.6);
  }
  async setLofi(on){
    this.init();await this.ctx.resume();this.lofiOn=on;
    this.lofiGain.gain.setTargetAtTime(on?0.55:0,this.ctx.currentTime,0.8);
    clearInterval(this.timer);
    if(on){this.tick();this.timer=setInterval(()=>this.tick(),60/72*2*1000)}
  }
  tick(){
    const chords=[[57,60,64,67],[53,57,60,64],[50,53,57,60],[52,56,59,62]];
    const ch=chords[this.step++%chords.length],t=this.ctx.currentTime,dur=60/72*2;
    ch.forEach((n,i)=>this.note(n,t+i*0.03,dur*1.05,0.11));
    this.note(ch[0]-12,t,dur*0.9,0.2);
    [0,1,2,3].forEach(b=>{
      if(b%2===1){const m=ch[(b*3)%4]+12;this.note(m,t+b*dur/4,dur/4,0.05)}
    });
    this.kick(t);this.kick(t+dur*0.5);
  }
  note(m,t,d,v){
    const ctx=this.ctx,o=ctx.createOscillator(),g=ctx.createGain();
    o.type="triangle";o.frequency.value=440*Math.pow(2,(m-69)/12);
    this.wobG.connect(o.detune);
    g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(v,t+0.02);
    g.gain.exponentialRampToValueAtTime(0.0008,t+d);
    o.connect(g).connect(this.lofiGain);o.start(t);o.stop(t+d+0.05);
    o.onended=()=>{try{this.wobG.disconnect(o.detune)}catch{}};
  }
  kick(t){
    const ctx=this.ctx,o=ctx.createOscillator(),g=ctx.createGain();
    o.frequency.setValueAtTime(120,t);o.frequency.exponentialRampToValueAtTime(40,t+0.12);
    g.gain.setValueAtTime(0.35,t);g.gain.exponentialRampToValueAtTime(0.001,t+0.18);
    o.connect(g).connect(this.lofiGain);o.start(t);o.stop(t+0.2);
  }
}
