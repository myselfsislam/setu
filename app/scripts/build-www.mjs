// Copies the Setu web app from the repository root into www/ for the native apps.
import { cpSync, rmSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '..', '..');
const www = resolve(here, '..', 'www');
rmSync(www, { recursive: true, force: true });
mkdirSync(www, { recursive: true });
for (const f of ['fonts', 'icons']) cpSync(resolve(root, f), resolve(www, f), { recursive: true });
let html = readFileSync(resolve(root, 'index.html'), 'utf8');
// The app doesn't need the web-only bits: install manifest and search-engine verification.
html = html.replace(/<link rel="manifest"[^>]*>\n?/, '').replace(/<meta name="google-site-verification"[^>]*>\n?/, '');
writeFileSync(resolve(www, 'index.html'), html);
console.log('www ready:', www);
