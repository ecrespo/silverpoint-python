// The conformance kit (silverpoint REQ-666) against the vendored module build, in Node (PY-REQ-015).
// The cases are the pinned `conformance.json`; exit code 1 on any failure.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const vendor = new URL('../src/silverpoint/_vendor/', import.meta.url);
const sp = await import(new URL('silverpoint-embed.full.mjs', vendor).href);
const cases = JSON.parse(readFileSync(fileURLToPath(new URL('conformance.json', vendor)), 'utf8'));

const result = await sp.conformance((spec) => {
  const out = sp.renderToSVG(spec);
  if (!out.ok) throw new Error(sp.specErrorMessage ? sp.specErrorMessage(out.error) : JSON.stringify(out.error));
  return out.value.svg;
}, undefined, cases);

console.log(`conformance ${cases.version}: ${result.passed} passed, ${result.failed.length} failed`);
for (const f of result.failed) console.log(`  ${f.name}: expected ${f.expected}, got ${f.actual}`);
process.exit(result.failed.length === 0 && cases.version === sp.version ? 0 : 1);
