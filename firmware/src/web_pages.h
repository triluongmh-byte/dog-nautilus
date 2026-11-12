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
<meta name=viewport content="width=device-width,initial-scale=1"><title>Nautilus Dog</title>
<style>%CSS%</style></head><body>
<h2>Nautilus Dog <small id=lnk class=bad>offline</small></h2>
<div>Battery: <b id=bat>--</b>% <small id=volt></small> <b id=low class=bad></b></div>
<div class=row><span></span><button onclick="d('F')">&#9650; Forward</button><span></span></div>
<div class=row><button onclick="d('L')">&#9664; Left</button><button class=s onclick="d('S')">Stop</button><button onclick="d('R')">Right &#9654;</button></div>
<div class=row><span></span><button onclick="d('B')">&#9660; Back</button><span></span></div>
<h3>Speed <span id=spv>50</span>%</h3>
<input type=range id=sp min=0 max=100 value=50 oninput="sp()">
<h3>Gait</h3>
<div class=row><button class=g id=g0 onclick="gt('trot')">Trot</button><button class=g id=g1 onclick="gt('walk')">Walk</button></div>
<p><a href="/cal">Calibration</a></p>
<script>%JS%
var cur='S';
function d(x){cur=x;tx('drive '+x);mark()}
function sp(){$('spv').textContent=$('sp').value;tx('spd '+$('sp').value)}
function gt(g){tx('gait '+g)}
function mark(){}
function onMsg(m){var p=m.split(' ');if(p[0]=='st'){$('bat').textContent=p[1];$('volt').textContent=p[2]+' V';
$('low').textContent=p[3]=='1'?'LOW BATTERY':'';$('g0').className='g'+(p[5]=='0'?' on':'');$('g1').className='g'+(p[5]=='1'?' on':'');}}
window.onblur=function(){tx('drive S')};
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
