import {continueRender, delayRender, staticFile} from 'remotion';

// Vendored Fredoka (SIL OFL 1.1, see public/fonts/OFL.txt) — no network needed at render time.
const weights = [400, 600, 700];
const handle = delayRender('Loading Fredoka');
Promise.all(
	weights.map((w) => new FontFace('Fredoka', `url(${staticFile(`fonts/Fredoka-${w}.ttf`)})`, {weight: String(w)}).load()),
)
	.then((faces) => {
		faces.forEach((f) => document.fonts.add(f));
		continueRender(handle);
	})
	.catch((e) => {
		console.error('font load failed', e);
		continueRender(handle);
	});
