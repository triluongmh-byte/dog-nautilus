// Syntax-checks the <script> blocks embedded in firmware/src/web_pages.h. Usage: node check_pages.js <web_pages.h>
const fs = require('fs'), vm = require('vm');
const t = fs.readFileSync(process.argv[2], 'utf8');
const get = n => new RegExp('R"' + n + '\\(([\\s\\S]*?)\\)' + n + '"').exec(t.slice(t.indexOf(n === 'JS' ? 'PAGE_COMMON_JS' : 'PAGE_INDEX')))[1];
const js = get('JS');
let ok = true;
for (const m of t.matchAll(/R"HTML\(([\s\S]*?)\)HTML"/g)) {
  const sc = /<script>([\s\S]*?)<\/script>/.exec(m[1])[1].replace('%JS%', js);
  try { new vm.Script(sc); } catch (e) { ok = false; console.error('JS error:', e.message); }
}
console.log(ok ? 'pages JS OK' : 'pages JS FAIL'); process.exit(ok ? 0 : 1);
