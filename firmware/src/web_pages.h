#pragma once
#include <pgmspace.h>
static const char PAGE_COMMON_JS[] PROGMEM = R"JS(
var ws,$=function(i){return document.getElementById(i)};
function conn(){ws=new WebSocket('ws://'+location.hostname+':81/');
ws.onopen=function(){$('lnk').textContent='online';$('lnk').className='ok'};
ws.onclose=function(){$('lnk').textContent='offline';$('lnk').className='bad';setTimeout(conn,1000)};
ws.onmessage=function(e){onMsg(e.data)}}
function tx(m){if(ws&&ws.readyState==1)ws.send(m)}
setInterval(function(){tx('hb')},300);
)JS";

static const char PAGE_CSS[] PROGMEM = R"CSS(
body{font-family:sans-serif;background:#111;color:#eee;margin:0;padding:12px;max-width:480px;margin:auto}
button{background:#2a6;color:#fff;border:0;border-radius:8px;padding:16px 0;font-size:18px;width:100%}
button.s{background:#c33}button.g{background:#456}button.on{outline:3px solid #fc0}
.row{display:flex;gap:8px;margin:8px 0}.row>*{flex:1}
.ok{color:#6f6}.bad{color:#f66}input[type=range]{width:100%}
h3{margin:14px 0 4px}.leg{border:1px solid #444;border-radius:8px;padding:8px;margin:8px 0}
small{color:#999}input[type=number]{width:70px}a{color:#8cf}
)CSS";

static const char PAGE_INDEX[] PROGMEM = R"HTML(<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1,user-scalable=no"><title>Nautilus Dog</title>
<style>%CSS%
body{max-width:none;user-select:none;-webkit-user-select:none;-webkit-touch-callout:none}
#wrap{display:flex;flex-direction:column;gap:10px}
#pad{position:relative;width:min(88vw,52vh,420px);aspect-ratio:1;margin:auto;border-radius:50%;background:#222;border:2px solid #444;touch-action:none}
#knob{position:absolute;left:50%;top:50%;width:28%;height:28%;margin:-14% 0 0 -14%;border-radius:50%;background:#2a6;pointer-events:none}
.btns button{padding:12px 0;font-size:22px;touch-action:none}
#stop{font-size:22px;padding:18px 0}
#lock{display:none;background:#633;padding:10px;border-radius:8px;text-align:center}
@media (orientation:landscape){#wrap{flex-direction:row;align-items:center}#wrap>div{flex:1}#pad{width:min(46vw,80vh)}}
</style></head><body>
<h3 style="margin:4px 0">Nautilus Dog <small id=lnk class=bad>offline</small>
 &nbsp; <small>Battery <b id=bat>--</b>% <span id=volt></span> <b id=low class=bad></b></small></h3>
<div id=lock>Someone else is driving. <button class=g style="width:auto;padding:8px 14px" onclick="tx('take')">Take control</button></div>
<div id=wrap>
<div><div id=pad><div id=knob></div></div></div>
<div>
<div>Moving: <b id=dir>Stop</b></div>
<div class="row btns"><button id=bFL data-c=FL>&#8598;</button><button id=bF data-c=F>&#9650;</button><button id=bFR data-c=FR>&#8599;</button></div>
<div class="row btns"><button id=bL data-c=L>&#10226;</button><button id=bB data-c=B>&#9660;</button><button id=bR data-c=R>&#10227;</button></div>
<div class="row btns"><button id=bBL data-c=BL>&#8601;</button><span></span><button id=bBR data-c=BR>&#8600;</button></div>
<div class=row><button class=s id=stop onclick="halt()">&#9632; STOP</button></div>
<div>Max speed <span id=spv>50</span>%<input type=range id=sp min=0 max=100 value=50 oninput="sp()"></div>
<div class=row><button class=g id=g0 onclick="gt('trot')">Trot</button><button class=g id=g1 onclick="gt('walk')">Walk</button><button class=g id=love style="background:#a36" onclick="tx('emote love')">&#10084; Love</button></div>
<p><a href="/cal">Calibration</a> <small id=msg></small></p>
</div></div>
<script>%JS%
var DN=['S','F','B','L','R','FL','FR','BL','BR','J'],DT={S:'Stop',F:'Forward',B:'Back',L:'Spin left',R:'Spin right',FL:'Forward-left',FR:'Forward-right',BL:'Back-left',BR:'Back-right',J:'Joystick'};
var me=-1,drv=-1,hold=null,jx=0,jy=0,joyOn=false,pid=null;
function mine(){return me>=0&&me==drv}
function show(c){$('dir').textContent=DT[c]||c;document.querySelectorAll('.btns button').forEach(function(b){b.className=b.dataset.c==hold?'on':''})}
function halt(){hold=null;joyOn=false;jx=jy=0;knob(0,0);if(mine()){tx('joy 0 0');tx('drive S')}show('S')}
function sp(){$('spv').textContent=$('sp').value;tx('spd '+$('sp').value)}
function gt(g){tx('gait '+g)}
// held button: resend every JOY_SEND_MS (100 ms); release, leave or cancel stops
document.querySelectorAll('.btns button').forEach(function(b){
 b.addEventListener('pointerdown',function(e){e.preventDefault();b.setPointerCapture(e.pointerId);hold=b.dataset.c;tx('drive '+hold);show(hold)});
 ['pointerup','pointercancel','lostpointercapture'].forEach(function(ev){b.addEventListener(ev,function(){if(hold==b.dataset.c)halt()})});
});
var pad=$('pad');
function knob(x,y){$('knob').style.transform='translate('+(x*130)+'%,'+(-y*130)+'%)'}
function pmove(e){var r=pad.getBoundingClientRect(),R=r.width/2,x=(e.clientX-r.left-R)/R,y=-(e.clientY-r.top-R)/R,m=Math.hypot(x,y);
 if(m>1){x/=m;y/=m}jx=x;jy=y;knob(x,y)}
pad.addEventListener('pointerdown',function(e){e.preventDefault();pad.setPointerCapture(e.pointerId);pid=e.pointerId;joyOn=true;hold=null;pmove(e);tx('joy '+jx.toFixed(2)+' '+jy.toFixed(2))});
pad.addEventListener('pointermove',function(e){if(joyOn&&e.pointerId==pid)pmove(e)});
['pointerup','pointercancel','lostpointercapture'].forEach(function(ev){pad.addEventListener(ev,function(e){if(joyOn&&e.pointerId==pid)halt()})});
setInterval(function(){if(joyOn)tx('joy '+jx.toFixed(2)+' '+jy.toFixed(2));else if(hold)tx('drive '+hold)},100);
function onMsg(m){var p=m.split(' ');
 if(p[0]=='id')me=+p[1];
 else if(p[0]=='drv'){drv=+p[1];$('lock').style.display=mine()?'none':'block';if(!mine()){hold=null;joyOn=false;knob(0,0)}}
 else if(p[0]=='msg')$('msg').textContent=p.slice(1).join(' ');
 else if(p[0]=='st'){$('bat').textContent=p[1];$('volt').textContent=p[2]+' V';
 $('low').textContent=p[3]=='1'?'LOW BATTERY':'';$('g0').className='g'+(p[5]=='0'?' on':'');$('g1').className='g'+(p[5]=='1'?' on':'');
 if(!hold&&!joyOn&&DN[+p[4]]!=null)show(DN[+p[4]]);if(p[6]!=null){drv=+p[6];$('lock').style.display=mine()?'none':'block'}$('love').className='g'+(p[7]=='1'?' on':'')}}
window.onblur=halt;document.addEventListener('visibilitychange',function(){if(document.hidden)halt()});
conn();
</script></body></html>)HTML";

static const char PAGE_CAL[] PROGMEM = R"HTML(<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Calibration</title>
<style>%CSS%</style></head><body>
<h2>Calibration <small id=lnk class=bad>offline</small></h2>
<p><small>Lift the robot so the legs hang free. 1) Stop trim: press +/- until the servo stops creeping, then &ldquo;Save&rdquo;.
2) Nudge each leg to its reference pose and press &ldquo;Phase zero&rdquo;. 3) Spin 5 s, count turns, enter sec/rev. 4) Save.
Nudges only work while stopped.</small></p>
<div id=legs></div>
<div class=row><button onclick="tx('save')">Save to NVS</button><button class=s onclick="tx('drive S')">Stop</button></div>
<p><a href="/">Back to control</a> <span id=msg></span></p>
<script>%JS%
var N=['FL','FR','RL','RR'],h='';
for(var i=0;i<4;i++){h+='<div class=leg><b>'+N[i]+'</b> <small id=i'+i+'></small>'+
'<div class=row><button onclick="tx(\'nudge '+i+' -1\')">&#8634; Nudge -</button><button onclick="tx(\'nudge '+i+' 1\')">Nudge + &#8635;</button></div>'+
'<div class=row><button class=g onclick="tx(\'trim '+i+' -2\')">Trim -2us</button><button class=g onclick="tx(\'trim '+i+' 2\')">Trim +2us</button><button class=g onclick="tx(\'sign '+i+'\')">Flip dir</button></div>'+
'<div class=row><button class=g onclick="tx(\'zero '+i+'\')">Phase zero</button><button class=g onclick="tx(\'spin '+i+'\')">Spin 5 s</button></div>'+
'<div>sec/rev <input type=number step=0.05 id=r'+i+' value=1.2> <button class=g style="width:auto;padding:8px" onclick="tx(\'rev '+i+' \'+$(\'r'+i+'\').value)">Set</button></div></div>'}
$('legs').innerHTML=h;
function onMsg(m){var p=m.split(' ');if(p[0]=='cal'){var i=p[1];$('i'+i).textContent='neutral '+p[2]+'us dir '+p[3]+' sec/rev '+p[4]+' phase err '+p[5];}
else if(p[0]=='msg')$('msg').textContent=p.slice(1).join(' ');}
conn();
</script></body></html>)HTML";
