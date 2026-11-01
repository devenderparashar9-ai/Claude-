// Render review stills at chosen frames (bundle once). Usage:
//   node scripts/stills.mjs <CompositionId> <outDir> <frame,frame,...> [scale]
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'node:path';
import fs from 'node:fs';

const [comp, outDir, framesArg, scaleArg] = process.argv.slice(2);
const browserExecutable = process.env.MUSEVID_CHROME || '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
fs.mkdirSync(outDir, {recursive: true});
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const composition = await selectComposition({serveUrl, id: comp, browserExecutable});
for (const f of framesArg.split(',').map(Number)) {
	const output = path.join(outDir, `f${String(f).padStart(4, '0')}.png`);
	await renderStill({serveUrl, composition, frame: f, output, browserExecutable, scale: Number(scaleArg || 0.5)});
	console.log(output);
}
