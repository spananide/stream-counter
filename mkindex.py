# build index.html from the css of the artifact page (E:\nooreax-cam\index.html) and index.tpl.html
import re
css = re.search(r'<style>.*?</style>', open(r'E:\nooreax-cam\index.html', encoding='utf8').read(), re.S).group(0)
css = css.replace('.shot{flex:none;width:186px;height:160px;border-radius:3px;background-color:var(--nodata);background-repeat:no-repeat;background-size:2400% 100%;image-rendering:auto}',
                  '.shot{flex:none;width:186px;height:160px;border-radius:3px;background:var(--nodata);object-fit:cover;display:block}')
css = css.replace('*{box-sizing:border-box}', '*{box-sizing:border-box}html{background:var(--bg)}body{margin:0}'
  '.live{display:inline-flex;align-items:center;gap:8px;font-size:13px;color:var(--mute);margin:0 0 14px}.dot{width:9px;height:9px;border-radius:50%;background:var(--away)}'
  '.on .dot{background:#2fbf71;animation:p 2s infinite}@keyframes p{0%{box-shadow:0 0 0 0 #2fbf7188}70%{box-shadow:0 0 0 8px transparent}}'
  '@media (prefers-reduced-motion:reduce){.on .dot{animation:none}}.grid .c.ph{box-shadow:inset 0 0 0 1px rgba(255,255,255,.35)}')
open('index.html', 'w', encoding='utf8').write(open('index.tpl.html', encoding='utf8').read().replace('__CSS__', css))
