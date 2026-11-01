import React from 'react';
import {Lit, ellipse, rrect} from '../components/Lit';
import {rng} from '../lib/motion';
import {PALETTE, mix} from '../theme';
import {Cam, SCREEN, W, layerTransform} from './camera';

export type WorldState = {
	frame: number;
	fps: number;
	dusk: number; // 0 afternoon → 1 dusk
	panelFlash: number; // 0..1
	inverterGlow: number; // 0..1
	lights: number; // 0..1 city light-up progress (staggered per window)
	wirePulse: number; // 0..1 electricity flowing along the lines
};

const Layer: React.FC<{cam: Cam; p: number; blur?: number; children: React.ReactNode}> = ({cam, p, blur = 0, children}) => (
	<g transform={layerTransform(cam, p).css} style={blur ? {filter: `blur(${blur}px)`} : undefined}>
		{children}
	</g>
);

const hills = (seed: number, y: number, amp: number, x0: number, x1: number, step: number) => {
	const r = rng(seed);
	let d = `M${x0} ${y + 400} L${x0} ${y}`;
	for (let x = x0; x < x1; x += step) {
		const h = y - amp * (0.4 + r() * 0.6);
		d += ` Q${x + step / 2} ${h} ${x + step} ${y - amp * 0.15 * r()}`;
	}
	return d + ` L${x1} ${y + 400} Z`;
};

const House: React.FC<{s: WorldState}> = ({s}) => {
	const {x1, y1, x2, y2} = W.panel;
	// panel quad: A→B along the roof slope, D = depth down the slope; 4×2 cells
	const D = [46, 50];
	const P = (t: number, u: number) => [x1 + (x2 - x1) * t + D[0] * u, y1 + (y2 - y1) * t + D[1] * u];
	const cells: string[] = [];
	for (let i = 0; i < 4; i++) {
		for (let j = 0; j < 2; j++) {
			const q = [P(i / 4, j / 2), P((i + 1) / 4, j / 2), P((i + 1) / 4, (j + 1) / 2), P(i / 4, (j + 1) / 2)];
			cells.push('M' + q.map((v) => `${v[0].toFixed(1)} ${v[1].toFixed(1)}`).join(' L') + ' Z');
		}
	}
	const lit = s.lights > 0.02;
	return (
		<g>
			<Lit d={rrect(1050, 620, 400, 262, 14)} fill={PALETTE.wall} />
			<Lit d="M1020 640 L1240 420 L1480 640 Z" fill={PALETTE.roof} rim={1.2} />
			<Lit d={rrect(1205, 740, 74, 140, 10)} fill={mix(PALETTE.roof, PALETTE.ink, 0.3)} />
			{[1110, 1330].map((x) => (
				<g key={x}>
					<Lit d={rrect(x, 680, 80, 76, 10)} fill={lit ? mix(PALETTE.window, PALETTE.windowLit, Math.min(1, s.lights * 1.6)) : PALETTE.window} shadow={0.4} />
					<path d={`M${x + 40} 680 V756 M${x} 718 H${x + 80}`} stroke={PALETTE.ink} strokeWidth={4} />
				</g>
			))}
			{/* solar panel on the sun-facing roof slope */}
			<g>
				{cells.map((d, i) => (
					<path key={i} d={d} fill={mix(PALETTE.panel, PALETTE.panelLine, s.panelFlash * 0.7 + 0.05 * Math.sin(s.frame / 9 + i))} stroke={PALETTE.panelLine} strokeWidth={2.5} />
				))}
				<path d={`M${x1} ${y1} L${x2} ${y2} L${x2 + 46} ${y2 + 50} L${x1 + 46} ${y1 + 50} Z`} fill="none" stroke={PALETTE.ink} strokeWidth={5} strokeLinejoin="round" />
				<path d={`M${x1 + 10} ${y1 + 4} L${x2 - 10} ${y2 + 4}`} stroke={PALETTE.rimHot} strokeWidth={3} opacity={0.6 + 0.4 * s.panelFlash} />
			</g>
			{/* inverter box on the wall */}
			<g>
				<circle cx={W.inverter[0] + 30} cy={W.inverter[1] + 40} r={70 * s.inverterGlow} fill={PALETTE.rim} opacity={0.35 * s.inverterGlow} />
				<Lit d={rrect(W.inverter[0], W.inverter[1], 62, 82, 9)} fill={PALETTE.metal} />
				<circle cx={W.inverter[0] + 31} cy={W.inverter[1] + 26} r={9} fill={mix('#6b5aa8', '#7dff9a', s.inverterGlow)} stroke={PALETTE.ink} strokeWidth={3} />
				<path d={`M${W.inverter[0] + 14} ${W.inverter[1] + 56} q8 -10 16 0 t16 0`} stroke={PALETTE.ink} strokeWidth={3.5} fill="none" />
			</g>
			{/* panel → inverter conduit */}
			<path d={`M${x2 + 40} ${y2 + 46} C1330 560 1400 620 ${W.inverter[0] + 31} ${W.inverter[1]}`} stroke={PALETTE.wire} strokeWidth={6} fill="none" />
		</g>
	);
};

const WIRE_Y = 640;
export const wirePath = () => {
	const pts = [[W.inverter[0] + 62, W.inverter[1] + 30], ...W.poles.map((x) => [x, WIRE_Y]), [W.substation[0], W.substation[1]]];
	let d = `M${pts[0][0]} ${pts[0][1]}`;
	for (let i = 1; i < pts.length; i++) {
		const [ax, ay] = pts[i - 1];
		const [bx, by] = pts[i];
		d += ` Q${(ax + bx) / 2} ${Math.max(ay, by) + 55} ${bx} ${by}`;
	}
	return d;
};

const Poles: React.FC<{s: WorldState}> = ({s}) => (
	<g>
		{W.poles.map((x) => (
			<g key={x}>
				<Lit d={rrect(x - 11, WIRE_Y - 20, 22, W.ground - WIRE_Y + 20, 8)} fill="#8a6a5a" shadow={0.6} />
				<Lit d={rrect(x - 60, WIRE_Y - 26, 120, 16, 7)} fill="#8a6a5a" shadow={0.4} />
			</g>
		))}
		<path d={wirePath()} stroke={PALETTE.wire} strokeWidth={5} fill="none" />
		<path d={wirePath()} stroke={PALETTE.electron} strokeWidth={9} fill="none" strokeLinecap="round"
			strokeDasharray="18 110" strokeDashoffset={-s.frame * 14} opacity={s.wirePulse} style={{filter: 'drop-shadow(0 0 8px #6fd3ff)'}} />
	</g>
);

const City: React.FC<{s: WorldState}> = ({s}) => {
	const r = rng(42);
	const bldgs = [];
	let x = W.city[0];
	let k = 0;
	while (x < W.city[1]) {
		const w = 110 + r() * 90;
		const h = 220 + r() * 300;
		bldgs.push({x, w, h, c: PALETTE.city[k % PALETTE.city.length], k});
		x += w + 14 + r() * 20;
		k++;
	}
	return (
		<g>
			<Lit d={rrect(W.substation[0] - 40, W.substation[1], 90, W.ground - W.substation[1], 10)} fill={PALETTE.metal} shadow={0.6} />
			{bldgs.map((b) => {
				const top = W.ground - b.h;
				const wins = [];
				const rr = rng(100 + b.k);
				for (let wy = top + 36; wy < W.ground - 60; wy += 58) {
					for (let wx = b.x + 22; wx < b.x + b.w - 40; wx += 44) {
						const order = rr();
						const on = Math.max(0, Math.min(1, (s.lights * 1.25 - order * 0.6) * 4));
						wins.push(
							<g key={`${wx}-${wy}`}>
								{on > 0.5 ? <rect x={wx - 8} y={wy - 8} width={42} height={48} rx={10} fill={PALETTE.windowLit} opacity={0.25 * on} /> : null}
								<rect x={wx} y={wy} width={26} height={32} rx={6} fill={mix(PALETTE.window, PALETTE.windowLit, on)} stroke={PALETTE.ink} strokeWidth={3} />
							</g>,
						);
					}
				}
				return (
					<g key={b.k}>
						<Lit d={rrect(b.x, top, b.w, b.h + 6, 18)} fill={mix(b.c, PALETTE.duskTop, s.dusk * 0.25)} />
						{wins}
					</g>
				);
			})}
		</g>
	);
};

export const World: React.FC<{cam: Cam; s: WorldState; fgBlur?: number}> = ({cam, s, fgBlur = 0}) => {
	const top = mix(PALETTE.skyTop, PALETTE.duskTop, s.dusk);
	const mid = mix(PALETTE.skyMid, PALETTE.duskMid, s.dusk);
	const low = mix(PALETTE.skyLow, PALETTE.duskLow, s.dusk);
	const stars = rng(9);
	return (
		<svg viewBox={`0 0 ${SCREEN.w} ${SCREEN.h}`} width={SCREEN.w} height={SCREEN.h} style={{position: 'absolute'}}>
			<defs>
				<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
					<stop offset="0" stopColor={top} />
					<stop offset="0.55" stopColor={mid} />
					<stop offset="1" stopColor={low} />
				</linearGradient>
				<radialGradient id="sunGlow">
					<stop offset="0" stopColor={PALETTE.rimHot} stopOpacity={0.95} />
					<stop offset="0.35" stopColor={PALETTE.sun} stopOpacity={0.55} />
					<stop offset="1" stopColor={PALETTE.sun} stopOpacity={0} />
				</radialGradient>
			</defs>
			<rect width={SCREEN.w} height={SCREEN.h} fill="url(#sky)" />
			{s.dusk > 0.3
				? Array.from({length: 40}, (_, i) => (
						<circle key={i} cx={stars() * SCREEN.w} cy={stars() * 420} r={1.5 + stars() * 2} fill={PALETTE.cream}
							opacity={(s.dusk - 0.3) * (0.5 + 0.5 * Math.sin(s.frame / 11 + i))} />
					))
				: null}
			<Layer cam={cam} p={0.3}>
				<circle cx={W.sun[0]} cy={W.sun[1] + s.dusk * 400} r={260} fill="url(#sunGlow)" />
				<g transform={`rotate(${s.frame * 0.25} ${W.sun[0]} ${W.sun[1] + s.dusk * 400})`}>
					{Array.from({length: 12}, (_, i) => {
						const a = (i / 12) * Math.PI * 2;
						const cy = W.sun[1] + s.dusk * 400;
						const r0 = 108 + 6 * Math.sin(s.frame / 8 + i);
						return <path key={i} d={`M${W.sun[0] + Math.cos(a) * r0} ${cy + Math.sin(a) * r0} L${W.sun[0] + Math.cos(a) * (r0 + 40)} ${cy + Math.sin(a) * (r0 + 40)}`}
							stroke={PALETTE.sun} strokeWidth={12} strokeLinecap="round" opacity={0.75} />;
					})}
				</g>
				<Lit d={ellipse(W.sun[0], W.sun[1] + s.dusk * 400, 88, 88)} fill={mix(PALETTE.sun, '#ff9a4d', s.dusk)} shadow={0.25} rim={0} />
				<path d={hills(3, 760, 180, -800, 5200, 520)} fill={mix(PALETTE.hillFar, PALETTE.duskTop, s.dusk * 0.5)} />
			</Layer>
			<Layer cam={cam} p={0.6}>
				<path d={hills(8, 830, 150, -600, 5200, 380)} fill={mix(PALETTE.hillMid, PALETTE.duskMid, s.dusk * 0.4)} />
			</Layer>
			<Layer cam={cam} p={1}>
				<rect x={-1000} y={W.ground - 6} width={7000} height={600} fill={mix(PALETTE.grass, PALETTE.duskMid, s.dusk * 0.35)} />
				<path d={`M-1000 ${W.ground - 6} H6000`} stroke={PALETTE.ink} strokeWidth={5} />
				<City s={s} />
				<Poles s={s} />
				<House s={s} />
			</Layer>
		</svg>
	);
};

/** Foreground plane (p > 1): soft-focus grass and flowers sliding past for depth. */
export const Foreground: React.FC<{cam: Cam; frame: number; blur: number}> = ({cam, frame, blur}) => {
	const r = rng(77);
	const tufts = Array.from({length: 60}, (_, i) => ({x: -400 + i * 95 + r() * 40, h: 40 + r() * 50, c: r() > 0.8}));
	return (
		<svg viewBox={`0 0 ${SCREEN.w} ${SCREEN.h}`} width={SCREEN.w} height={SCREEN.h} style={{position: 'absolute', filter: `blur(${blur}px)`}}>
			<g transform={layerTransform(cam, 1.35).css}>
				{tufts.map((t, i) => {
					const sway = Math.sin(frame / 14 + i) * 6;
					return (
						<g key={i}>
							<path d={`M${t.x} ${W.ground + 120} q${8 + sway} ${-t.h} ${18 + sway * 1.5} ${-t.h - 10} q-2 ${t.h * 0.6} 8 ${t.h + 10}`} fill={PALETTE.hillNear} stroke={PALETTE.ink} strokeWidth={4} />
							{t.c ? <circle cx={t.x + 20 + sway * 1.5} cy={W.ground + 120 - t.h - 14} r={11} fill={PALETTE.pType} stroke={PALETTE.ink} strokeWidth={4} /> : null}
						</g>
					);
				})}
			</g>
		</svg>
	);
};
