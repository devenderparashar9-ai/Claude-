import React from 'react';
import {spring} from 'remotion';
import {Limb, Lit, ellipse} from '../components/Lit';
import {rng} from '../lib/motion';
import {OUTLINE, PALETTE, SPRING, shade} from '../theme';

/**
 * Pip — model sheet in code. Proportions, palette and outline are constants
 * (on-model in every shot); only pose/expression parameters change.
 * Local space: origin at the feet, +y down, total height ≈ 480 units.
 */
export type Arms = {lS: number; lE: number; rS: number; rE: number};
export type PipProps = {
	x: number;
	y: number;
	scale?: number;
	facing?: 1 | -1;
	arms: Arms;
	look?: {x: number; y: number}; // -1..1
	mouth?: number; // 0..1 open
	smile?: number; // 0..1
	brow?: number; // -1 frown … 0 neutral … 1 raised
	blink?: number; // 0 open … 1 closed
	wink?: number; // right eye only
	squash?: number; // + squash, - stretch
	tilt?: number; // body lean, degrees
	headTilt?: number;
	bob?: number; // breathing offset (px)
	hairSway?: number; // follow-through, degrees
	rimGlow?: number;
};

// Arm angle convention: degrees from hanging straight down, positive = outward/up
// on that arm's own side. Forearm absolute angle = shoulder + elbow.
export const POSES: Record<string, Arms> = {
	idle: {lS: 12, lE: -8, rS: 12, rE: -8},
	wave: {lS: 14, lE: -6, rS: 122, rE: 40},
	point: {lS: 12, lE: -10, rS: 92, rE: -4},
	lookUp: {lS: 20, lE: 30, rS: 20, rE: 30},
	in: {lS: 128, lE: 14, rS: 18, rE: -10},
	out: {lS: 20, lE: -12, rS: 98, rE: -8},
	cheer: {lS: 138, lE: -22, rS: 138, rE: -22},
	think: {lS: 14, lE: -6, rS: 4, rE: -158},
};

/** Blend between scheduled poses with a snappy spring (overshoot = follow-through). */
export const poseAt = (frame: number, fps: number, schedule: [number, keyof typeof POSES][]): Arms => {
	let cur: Arms = POSES[schedule[0][1]];
	for (let i = 1; i < schedule.length; i++) {
		const [f, name] = schedule[i];
		if (frame < f - 3) break;
		const p = spring({frame: frame - (f - 3), fps, config: SPRING.snappy});
		const tgt = POSES[name];
		cur = {
			lS: cur.lS + (tgt.lS - cur.lS) * p,
			lE: cur.lE + (tgt.lE - cur.lE) * p,
			rS: cur.rS + (tgt.rS - cur.rS) * p,
			rE: cur.rE + (tgt.rE - cur.rE) * p,
		};
	}
	return cur;
};

/** Natural, deterministic blinks every ~2.5–4.5 s (close fast, open slower). */
export const blinkAt = (frame: number, fps: number, seed = 5): number => {
	const r = rng(seed);
	let t = Math.round(fps * (0.8 + r() * 1.2));
	while (t < frame + 10) {
		const d = frame - t;
		if (d >= 0 && d < 7) return [0.5, 1, 1, 0.75, 0.45, 0.2, 0][d];
		t += Math.round(fps * (2.5 + r() * 2));
	}
	return 0;
};

const SHOULDER_Y = -238;
const UPPER = 62;
const FORE = 58;

const armPoints = (side: -1 | 1, s: number, e: number) => {
	const sx = 64 * side;
	const a1 = (s * Math.PI) / 180;
	const a2 = ((s + e) * Math.PI) / 180;
	const ex = sx + side * Math.sin(a1) * UPPER;
	const ey = SHOULDER_Y + Math.cos(a1) * UPPER;
	const hx = ex + side * Math.sin(a2) * FORE;
	const hy = ey + Math.cos(a2) * FORE;
	return [[sx, SHOULDER_Y], [ex, ey], [hx, hy]];
};

const Eye: React.FC<{cx: number; look: {x: number; y: number}; close: number}> = ({cx, look, close}) => {
	const cy = -366;
	const sy = Math.max(0.08, 1 - close);
	if (close >= 0.85) {
		// closed eye / wink: a happy curved lash line, not a squashed eyeball
		return <path d={`M${cx - 19} ${cy + 2} Q${cx} ${cy + 14} ${cx + 19} ${cy + 2}`} stroke={PALETTE.ink} strokeWidth={6} fill="none" strokeLinecap="round" />;
	}
	return (
		<g transform={`translate(${cx} ${cy}) scale(1 ${sy}) translate(${-cx} ${-cy})`}>
			<path d={ellipse(cx, cy, 21, 26)} fill={PALETTE.cream} stroke={PALETTE.ink} strokeWidth={OUTLINE * 0.7} />
			{true ? (
				<>
					<circle cx={cx + look.x * 8} cy={cy + look.y * 10 + 2} r={12.5} fill={PALETTE.ink} />
					<circle cx={cx + look.x * 8 - 4} cy={cy + look.y * 10 - 4} r={4.2} fill={PALETTE.cream} />
					<circle cx={cx + look.x * 8 + 4} cy={cy + look.y * 10 + 6} r={1.8} fill={PALETTE.cream} opacity={0.8} />
				</>
			) : null}
		</g>
	);
};

export const Pip: React.FC<PipProps> = ({
	x, y, scale = 1, facing = 1, arms, look = {x: 0, y: 0}, mouth = 0, smile = 0.6, brow = 0, blink = 0,
	wink = 0, squash = 0, tilt = 0, headTilt = 0, bob = 0, hairSway = 0, rimGlow = 0,
}) => {
	const L = armPoints(-1, arms.lS, arms.lE);
	const R = armPoints(1, arms.rS, arms.rE);
	const mo = Math.max(0, Math.min(1, mouth));
	const mw = 22 + 10 * smile;
	const mh = 5 + 30 * mo;
	const my = -326;
	const mouthOpen = `M${-mw} ${my} Q0 ${my + 3 - 6 * smile} ${mw} ${my} Q${mw * 0.9} ${my + mh} 0 ${my + mh + 4} Q${-mw * 0.9} ${my + mh} ${-mw} ${my} Z`;
	const torso = 'M-74 -112 C-84 -190 -68 -262 0 -268 C68 -262 84 -190 74 -112 Q0 -96 -74 -112 Z';
	const hair = 'M-97 -392 C-104 -470 -32 -505 8 -482 C42 -508 108 -482 99 -398 C82 -436 44 -448 12 -436 C-18 -452 -70 -444 -97 -392 Z';
	return (
		<g transform={`translate(${x} ${y}) scale(${scale * facing} ${scale})`}>
			<ellipse cx={0} cy={2} rx={112 * (1 + squash)} ry={15} fill={PALETTE.shadow} opacity={0.38} />
			<g transform={`scale(${1 + squash * 0.6} ${1 - squash}) rotate(${tilt} 0 -110)`}>
				{/* legs + shoes */}
				<Limb points={[[-30, -118], [-32, -22]]} width={34} color={PALETTE.pants} />
				<Limb points={[[30, -118], [32, -22]]} width={34} color={PALETTE.pants} />
				<Lit d={ellipse(-38, -12, 32, 17)} fill={PALETTE.shoe} />
				<Lit d={ellipse(38, -12, 32, 17)} fill={PALETTE.shoe} />
				<g transform={`translate(0 ${bob})`}>
					{/* back arm drawn behind torso */}
					<Limb points={L} width={30} color={PALETTE.hoodie} />
					<Lit d={ellipse(L[2][0], L[2][1], 19, 19)} fill={PALETTE.skin} />
					<Lit d={torso} fill={PALETTE.hoodie} glow={rimGlow} />
					<path d="M-38 -150 Q0 -138 38 -150 L34 -124 Q0 -116 -34 -124 Z" fill={shade(PALETTE.hoodie)} stroke={PALETTE.ink} strokeWidth={OUTLINE * 0.6} />
					<path d={ellipse(0, -262, 66, 22)} fill={PALETTE.hoodieDark} stroke={PALETTE.ink} strokeWidth={OUTLINE} />
					<path d="M-14 -246 L-18 -200 M14 -246 L18 -200" stroke={PALETTE.cream} strokeWidth={5} strokeLinecap="round" />
					{/* head */}
					<g transform={`rotate(${headTilt} 0 -268) translate(0 ${bob * 0.4})`}>
						<Lit d={ellipse(-104, -360, 19, 22)} fill={PALETTE.skin} />
						<Lit d={ellipse(104, -360, 19, 22)} fill={PALETTE.skin} />
						<Lit d={ellipse(0, -366, 108, 102)} fill={PALETTE.skin} glow={rimGlow} />
						<ellipse cx={-64} cy={-326} rx={17} ry={10} fill={PALETTE.cheek} opacity={0.55} />
						<ellipse cx={64} cy={-326} rx={17} ry={10} fill={PALETTE.cheek} opacity={0.55} />
						<Eye cx={-38} look={look} close={blink} />
						<Eye cx={38} look={look} close={Math.max(blink, wink)} />
						{[-1, 1].map((s) => (
							<path
								key={s}
								d={`M${s * 38 - 15} -404 Q${s * 38} -${414 + brow * 4} ${s * 38 + 15} -404`}
								transform={`translate(0 ${-brow * 7}) rotate(${s * brow * -6} ${s * 38} -404)`}
								stroke={PALETTE.ink}
								strokeWidth={6.5}
								strokeLinecap="round"
								fill="none"
							/>
						))}
						<ellipse cx={0} cy={-344} rx={8} ry={6} fill={shade(PALETTE.skin)} />
						{mo > 0.06 ? (
							<g>
								<defs>
									<clipPath id="pipMouth">
										<path d={mouthOpen} />
									</clipPath>
								</defs>
								<path d={mouthOpen} fill={PALETTE.mouth} />
								<ellipse cx={0} cy={my + mh * 0.85} rx={mw * 0.55} ry={mh * 0.35} fill={PALETTE.tongue} clipPath="url(#pipMouth)" />
								<path d={mouthOpen} fill="none" stroke={PALETTE.ink} strokeWidth={OUTLINE * 0.8} strokeLinejoin="round" />
							</g>
						) : (
							<path d={`M${-mw} ${my} Q0 ${my + 6 + 16 * smile} ${mw} ${my}`} stroke={PALETTE.ink} strokeWidth={OUTLINE * 1.1} fill="none" strokeLinecap="round" />
						)}
						<Lit d={hair} fill={PALETTE.hair} rim={1.3} glow={rimGlow} />
						<path
							d="M8 -482 C4 -512 34 -522 40 -500 C44 -486 28 -480 22 -492"
							transform={`rotate(${hairSway} 8 -482)`}
							stroke={PALETTE.ink}
							strokeWidth={9}
							fill="none"
							strokeLinecap="round"
						/>
					</g>
					{/* front arm */}
					<Limb points={R} width={30} color={PALETTE.hoodie} />
					<Lit d={ellipse(R[2][0], R[2][1], 19, 19)} fill={PALETTE.skin} />
				</g>
			</g>
		</g>
	);
};
