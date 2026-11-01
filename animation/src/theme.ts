// Single source of style. Components must not inline colours, easings or springs.
import {Easing} from 'remotion';

export const PALETTE = {
	ink: '#2a1840', // outline — never pure black
	cream: '#fff6e8', // never pure white
	shadow: '#5a3d9a', // purple shadow tint, mixed into every base colour
	rim: '#ffcf6b', // warm golden rim light
	rimHot: '#fff0b8',
	skyTop: '#7b6fd6',
	skyMid: '#f3a7b8',
	skyLow: '#ffd38a',
	duskTop: '#2e2466',
	duskMid: '#7a4f9e',
	duskLow: '#f08a6b',
	sun: '#ffd45c',
	hillFar: '#9a86d8',
	hillMid: '#7fb08a',
	hillNear: '#5f9c6c',
	grass: '#6fb86f',
	// Pip
	skin: '#f5c19e',
	cheek: '#f28b8b',
	hair: '#3b2433',
	hoodie: '#3fb6a8',
	hoodieDark: '#2f8f86',
	pants: '#4a3a8c',
	shoe: '#ff7a59',
	mouth: '#7a2338',
	tongue: '#ff8a8a',
	// world
	wall: '#ffe1b8',
	roof: '#d4573f',
	panel: '#2f4fa8',
	panelLine: '#9ec5ff',
	metal: '#c9c3d9',
	wire: '#3a2a55',
	city: ['#8f7fd1', '#a48fe0', '#7a6cc4', '#b39ce6', '#8a78cc'],
	window: '#4b3f86',
	windowLit: '#ffd76a',
	electron: '#6fd3ff',
	photon: '#ffe27a',
	nType: '#5aa9ff',
	pType: '#ff8fa3',
};

export const OUTLINE = 5; // constant outline thickness in character units
export const LIGHT = {dx: -1, dy: -1}; // light from upper-left (the sun); shadows fall lower-right
export const RIM_WIDTH = 7;
export const SHADOW_WIDTH = 16;

export const EASE = {
	out: Easing.bezier(0.16, 1, 0.3, 1), // expo-ish out: fast start, soft landing
	inOut: Easing.bezier(0.65, 0, 0.35, 1),
	in: Easing.bezier(0.7, 0, 0.84, 0),
	camera: Easing.bezier(0.45, 0, 0.15, 1), // cinematic: slow ease-in, long settle
	anticipate: Easing.bezier(0.36, -0.4, 0.4, 1.4), // dips back before going, overshoots
};

export const SPRING = {
	pop: {damping: 11, stiffness: 170, mass: 0.7}, // UI / props appearing, light overshoot
	snappy: {damping: 18, stiffness: 220, mass: 0.6}, // gestures
	soft: {damping: 26, stiffness: 90, mass: 1}, // big body moves
	wobbly: {damping: 7, stiffness: 120, mass: 0.8}, // cartoon follow-through
};

export const FONT = 'Fredoka, "DejaVu Sans", sans-serif';

export const mix = (a: string, b: string, t: number): string => {
	const p = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
	const [x, y] = [p(a), p(b)];
	return '#' + x.map((v, i) => Math.round(v + (y[i] - v) * t).toString(16).padStart(2, '0')).join('');
};

export const shade = (base: string) => mix(base, PALETTE.shadow, 0.5);
export const rimOf = (base: string) => mix(base, PALETTE.rim, 0.75);
