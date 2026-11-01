// Virtual camera over a wide 2D world. Layers carry a parallax factor p:
// p=0 is pinned to the screen (sky), p=1 is the main action plane, p>1 is foreground.
export type Cam = {x: number; y: number; zoom: number};
export const SCREEN = {w: 1920, h: 1080};
const REF = {x: 960, y: 540};

export const layerTransform = (cam: Cam, p: number) => {
	const cx = REF.x + (cam.x - REF.x) * p;
	const cy = REF.y + (cam.y - REF.y) * p;
	const z = 1 + (cam.zoom - 1) * p;
	return {cx, cy, z, css: `translate(${SCREEN.w / 2} ${SCREEN.h / 2}) scale(${z}) translate(${-cx} ${-cy})`};
};

export const worldToScreen = (cam: Cam, p: number, pt: [number, number]): [number, number] => {
	const {cx, cy, z} = layerTransform(cam, p);
	return [(pt[0] - cx) * z + SCREEN.w / 2, (pt[1] - cy) * z + SCREEN.h / 2];
};

// World landmarks (main plane, p = 1). Ground line at y = 880.
export const W = {
	ground: 880,
	pip: [690, 880] as [number, number],
	sun: [430, 250] as [number, number], // on the p=0.3 layer
	panel: {x1: 1088, y1: 610, x2: 1236, y2: 470}, // along the sun-facing roof slope
	inverter: [1452, 740] as [number, number],
	poles: [1760, 2260, 2760],
	city: [3080, 3980],
	substation: [3110, 690] as [number, number],
};
