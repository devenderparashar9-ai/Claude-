import {interpolate, spring} from 'remotion';
import {EASE} from '../theme';

type Ease = (t: number) => number;
export type Key = [frame: number, value: number, ease?: Ease];

/** Keyframe track: value at `frame`, eased per segment (never linear by default). */
export const track = (frame: number, keys: Key[], fallbackEase: Ease = EASE.inOut): number => {
	if (frame <= keys[0][0]) return keys[0][1];
	for (let i = 0; i < keys.length - 1; i++) {
		const [f0, v0] = keys[i];
		const [f1, v1, e] = keys[i + 1];
		if (frame <= f1) {
			return interpolate(frame, [f0, f1], [v0, v1], {
				easing: e ?? fallbackEase,
				extrapolateLeft: 'clamp',
				extrapolateRight: 'clamp',
			});
		}
	}
	return keys[keys.length - 1][1];
};

/** Spring that starts at `start` frame (0 before). */
export const springAt = (frame: number, fps: number, start: number, config = {}, durationInFrames?: number) =>
	frame < start ? 0 : spring({frame: frame - start, fps, config, durationInFrames});

/** Eased 0→1 over [start, start+dur]. */
export const ramp = (frame: number, start: number, dur: number, ease: Ease = EASE.out) =>
	interpolate(frame, [start, start + dur], [0, 1], {easing: ease, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

/** Enter then exit (exit faster than entrance). */
export const inOut = (frame: number, start: number, end: number, inDur = 18, outDur = 10) =>
	Math.min(ramp(frame, start, inDur, EASE.out), 1 - ramp(frame, end - outDur, outDur, EASE.in));

/** Idle "breathing" micro-motion so nothing on screen is ever dead still. */
export const breathe = (frame: number, fps: number, period = 3.2, amp = 1, phase = 0) =>
	Math.sin(((frame / fps) * 2 * Math.PI) / period + phase) * amp;

/** Deterministic PRNG (mulberry32). Never use Math.random in a render. */
export const rng = (seed: number) => {
	let a = seed >>> 0;
	return () => {
		a |= 0;
		a = (a + 0x6d2b79f5) | 0;
		let t = Math.imul(a ^ (a >>> 15), 1 | a);
		t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
		return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
	};
};

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

/** Point on a cubic bezier. */
export const bez = (p0: number[], p1: number[], p2: number[], p3: number[], t: number) => {
	const u = 1 - t;
	return [0, 1].map((i) => u * u * u * p0[i] + 3 * u * u * t * p1[i] + 3 * u * t * t * p2[i] + t * t * t * p3[i]);
};
