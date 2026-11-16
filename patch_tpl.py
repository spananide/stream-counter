# patch index.tpl.html: newest photo by default, random photo (all / one hour / one person)
s = open('index.tpl.html', encoding='utf8').read()
def rep(a, b):
    global s
    assert a in s, a[:60]
    s = s.replace(a, b)

lines = s.split('\n')
i = next(n for n, l in enumerate(lines) if l.startswith('<div class="proof">'))
lines[i] = ('<div class="proof"><img class="shot" id="shot" alt="Foto aus der Facecam" width="186" height="160"><div class="cap"><b id="capT"></b><span id="capS"></span>'
            '<div class="ctl"><button type="button" id="bLatest">Neuestes</button><button type="button" id="bRnd">Zufällig</button><button type="button" id="bHour" hidden>Nochmal aus dieser Stunde</button></div>'
            '<div class="chips" id="chips" role="group" aria-label="Zufällig von"><button type="button" data-f="" class="on">Alle</button><button type="button" data-f="N">Nooreax</button><button type="button" data-f="V">Veto</button><button type="button" data-f="D">Dima</button><button type="button" data-f="-">Niemand</button></div></div></div>')
s = '\n'.join(lines)

rep('let S=[],sel=null;', 'let S=[],mode="latest",filt="",hourSel=null,cur=null,tries=0;')
rep('{N:0,V:0,D:0,"-":0,n:0,imgs:null}', '{N:0,V:0,D:0,"-":0,n:0,list:null}')
rep('if(s.img)(c.imgs=c.imgs||[]).push(s);}', '(c.list=c.list||[]).push(s);}')
rep('c&&c.imgs?" ph":""', '""')
a = s.index(' if(sel)show(sel[0],sel[1]);else rand();')
b = s.index('document.getElementById("note").innerHTML=')
new_js = r''' if(mode==="latest")showSample(S[S.length-1]);else mark();
}
const $=id=>document.getElementById(id),ph=x=>`ph/${x.q.day}/${x.t}.jpg`;
const has=(x,f)=>f===""||(f==="-"?x.p==="-":x.p.includes(f));
const names=x=>x.p==="-"?"Niemand in der Cam":x.p.split("").map(l=>WHO[l]).join(" + ");
function mark(){document.querySelectorAll(".c.sel").forEach(e=>e.classList.remove("sel"));if(!cur)return;
 const el=document.querySelector(`.c[data-day="${cur.q.day}"][data-h="${cur.q.h}"]`);if(el)el.classList.add("sel")}
function showSample(x){if(!x)return;cur=x;const im=$("shot");
 im.onerror=()=>{if(tries++>8)return;if(mode==="latest")showSample(S[S.indexOf(x)-1]);else if(mode==="hour")randomHour(hourSel[0],hourSel[1]);else randomAny()};
 im.onload=()=>{tries=0};im.src=ph(x);
 const d=new Date(x.q.day+"T12:00:00");
 $("capT").textContent=names(x);
 $("capS").textContent=(mode==="latest"?"Neuestes Foto · ":mode==="hour"?"Aus dieser Stunde · ":"Zufällig · ")+`${wd[d.getDay()]} ${f2(d.getDate())}.${f2(d.getMonth()+1)}., ${f2(x.q.h)}:${f2(x.q.m)} Uhr`;
 mark()}
function latest(){mode="latest";hourSel=null;$("bHour").hidden=true;showSample(S[S.length-1])}
function randomAny(){mode="random";hourSel=null;$("bHour").hidden=true;const a=S.filter(x=>has(x,filt));if(a.length)showSample(a[Math.floor(Math.random()*a.length)])}
function randomHour(day,h){const c=window._days[day]&&window._days[day][h];if(!c||!c.list)return;mode="hour";hourSel=[day,h];$("bHour").hidden=false;
 let a=c.list.filter(x=>has(x,filt));if(!a.length)a=c.list;showSample(a[Math.floor(Math.random()*a.length)])}
$("grid").addEventListener("click",e=>{const t=e.target.closest(".c");if(t)randomHour(t.dataset.day,+t.dataset.h)});
$("bLatest").addEventListener("click",latest);$("bRnd").addEventListener("click",randomAny);
$("bHour").addEventListener("click",()=>hourSel&&randomHour(hourSel[0],hourSel[1]));
$("chips").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;filt=b.dataset.f;
 document.querySelectorAll("#chips button").forEach(x=>x.classList.toggle("on",x===b));if(mode==="hour")randomHour(hourSel[0],hourSel[1]);else randomAny()});
'''
s = s[:a] + new_js + s[b:]
rep('"Tippe auf ein Kästchen mit Rahmen, um ein Foto aus dieser Stunde zu sehen. Ein Kästchen zeigt, wer in dieser Stunde am häufigsten in der Cam saß. Zeiten in Berlin."',
    '"Oben siehst du das neueste Foto. Tippe auf ein Kästchen für ein zufälliges Foto aus dieser Stunde, oder wähle mit den Knöpfen ein zufälliges Foto aus allen Messungen, auch nur von einer Person. Ein Kästchen zeigt, wer in dieser Stunde am häufigsten in der Cam saß. Zeiten in Berlin."')
# style
open('index.tpl.html', 'w', encoding='utf8').write(s)
print('patched')
