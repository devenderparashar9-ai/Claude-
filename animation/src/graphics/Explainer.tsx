import React from 'react';
import {AbsoluteFill, interpolate} from 'remotion';
import {Lit, ellipse, rrect} from '../components/Lit';
import {bez, breathe, inOut, ramp, rng, springAt} from '../lib/motion';
import {EASE, FONT, PALETTE, SPRING} from '../theme';
import {Cam, W, worldToScreen} from '../world/camera';

/** Photons streaming from the sun (p=0.3 layer) to the panel (p=1) — computed in screen space. */
export const Photons: React.FC<{cam: Cam; frame: number; start: number; end: number; rate?: number}> = ({cam, frame, start, end, rate = 3}) => {
	if (frame < start) return null;
	const sun = worldToScreen(cam, 0.3, W.sun);
	const r = rng(13);
	const dots = [];
	const life = 34;
	for (let k = 0; k * rate < Math.min(frame, end) - start + life; k++) {
		const born = start + k * rate + Math.floor(r() * 3);
		const tgtT = r();
		const jitter = (r() - 0.5) * 120;
		const age = frame - born;
		if (age < 0 || age > life || born > end) continue;
		const t = EASE.in(age / life);
		const panel = worldToScreen(cam, 1, [W.panel.x1 + (W.panel.x2 - W.panel.x1) * tgtT + 20, W.panel.y1 + (W.panel.y2 - W.panel.y1) * tgtT + 24]);
		const p = bez(sun, [sun[0] + 200, sun[1] + jitter], [panel[0] - 160, panel[1] - 120 + jitter], panel, t);
		const prev = bez(sun, [sun[0] + 200, sun[1] + jitter], [panel[0] - 160, panel[1] - 120 + jitter], panel, Math.max(0, t - 0.08));
		const size = 12 + 6 * Math.sin(age / 3 + k);
		dots.push(
			<g key={k} opacity={Math.min(1, age / 4) * (age > life - 3 ? (life - age) / 3 : 1)}>
				<line x1={prev[0]} y1={prev[1]} x2={p[0]} y2={p[1]} stroke={PALETTE.photon} strokeWidth={size * 0.9} strokeLinecap="round" opacity={0.45} />
				<circle cx={p[0]} cy={p[1]} r={size * 3.2} fill={PALETTE.photon} opacity={0.22} />
				<circle cx={p[0]} cy={p[1]} r={size * 1.7} fill={PALETTE.photon} opacity={0.35} />
				<circle cx={p[0]} cy={p[1]} r={size} fill={PALETTE.rimHot} stroke={PALETTE.ink} strokeWidth={3.5} />
				<circle cx={p[0] - size * 0.3} cy={p[1] - size * 0.3} r={size * 0.35} fill={PALETTE.cream} />
			</g>,
		);
	}
	return (
		<svg width={1920} height={1080} style={{position: 'absolute'}}>
			{dots}
		</svg>
	);
};

/** Impact burst where photons hit the panel. */
export const Burst: React.FC<{x: number; y: number; frame: number; at: number; scale?: number}> = ({x, y, frame, at, scale = 1}) => {
	const t = (frame - at) / 16;
	if (t < 0 || t > 1) return null;
	const e = EASE.out(t);
	return (
		<svg width={1920} height={1080} style={{position: 'absolute'}}>
			<circle cx={x} cy={y} r={30 + 140 * e * scale} fill="none" stroke={PALETTE.rimHot} strokeWidth={22 * (1 - e)} />
			<circle cx={x} cy={y} r={80 * scale * (1 - e)} fill={PALETTE.rimHot} opacity={0.6 * (1 - e)} />
			{Array.from({length: 10}, (_, i) => {
				const a = (i / 10) * Math.PI * 2;
				const r0 = 40 * scale + 120 * e * scale;
				return <line key={i} x1={x + Math.cos(a) * r0 * 0.6} y1={y + Math.sin(a) * r0 * 0.6} x2={x + Math.cos(a) * r0} y2={y + Math.sin(a) * r0}
					stroke={PALETTE.photon} strokeWidth={16 * (1 - e)} strokeLinecap="round" />;
			})}
		</svg>
	);
};

/** Silicon cross-section: photon hits → electron knocked loose → flows as current around a circuit. */
export const SiliconInsert: React.FC<{frame: number; fps: number; cues: Record<string, number>}> = ({frame, fps, cues}) => {
	const {electrons, silicon, flow, current, toInsert} = cues;
	const enter = springAt(frame, fps, toInsert, SPRING.soft);
	const L = {x: 360, w: 1200, top: 300};
	const r = rng(21);
	const atoms = Array.from({length: 26}, (_, i) => ({x: L.x + 60 + (i % 13) * 90, y: i < 13 ? L.top + 180 : L.top + 330, ph: r() * 6}));
	const loose = springAt(frame, fps, electrons, SPRING.wobbly);
	const flowT = (frame - flow) / fps;
	// circuit: from top contact up, across, down to a bulb, back along the bottom
	const circuit = `M${L.x + 600} ${L.top + 40} V170 H1700 V700 H${L.x + 600} V${L.top + 430}`;
	const label = (txt: string, x: number, y: number, at: number, color = PALETTE.cream) => {
		const s = springAt(frame, fps, at, SPRING.pop);
		return (
			<text x={x} y={y + (1 - s) * 18} opacity={s} fontFamily={FONT} fontWeight={600} fontSize={40} fill={color}
				transform={`rotate(${(1 - s) * -4} ${x} ${y})`}>{txt}</text>
		);
	};
	return (
		<AbsoluteFill style={{background: `radial-gradient(circle at 40% 30%, #4b3a8f, #1f1640 75%)`}}>
			<svg width={1920} height={1080} style={{transform: `scale(${0.9 + 0.1 * enter}) rotate(${(1 - enter) * -2}deg)`, transformOrigin: '50% 50%'}}>
				{/* circuit + bulb */}
				<path d={circuit} stroke="#7d6bb8" strokeWidth={12} fill="none" strokeLinejoin="round" />
				{frame > flow ? (
					<path d={circuit} stroke={PALETTE.electron} strokeWidth={14} fill="none" strokeLinejoin="round" strokeDasharray="10 70"
						strokeDashoffset={-flowT * 260} strokeLinecap="round" style={{filter: 'drop-shadow(0 0 10px #6fd3ff)'}} opacity={ramp(frame, flow, 10)} />
				) : null}
				<g transform="translate(1700 440)">
					<circle r={110 * ramp(frame, current, 20)} fill={PALETTE.windowLit} opacity={0.35} />
					<Lit d={ellipse(0, -10, 58, 62)} fill={frame > current ? PALETTE.windowLit : '#8d82b8'} glow={frame > current ? 1 : 0} />
					<Lit d={rrect(-26, 44, 52, 40, 8)} fill={PALETTE.metal} />
				</g>
				{/* layers */}
				<Lit d={rrect(L.x, L.top, L.w, 60, 16)} fill="#b9d8ff" shadow={0.5} />
				<Lit d={rrect(L.x, L.top + 60, L.w, 190, 6)} fill={PALETTE.nType} />
				<Lit d={rrect(L.x, L.top + 250, L.w, 190, 6)} fill={PALETTE.pType} />
				<path d={`M${L.x} ${L.top + 250} H${L.x + L.w}`} stroke={PALETTE.cream} strokeWidth={4} strokeDasharray="14 12" opacity={0.7} />
				{atoms.map((a, i) => (
					<g key={i} transform={`translate(${a.x + breathe(frame, fps, 1.4, 3, a.ph)} ${a.y})`}>
						<circle r={22} fill="#e9e3ff" stroke={PALETTE.ink} strokeWidth={4} />
						<text y={9} textAnchor="middle" fontFamily={FONT} fontWeight={700} fontSize={22} fill={PALETTE.ink}>Si</text>
					</g>
				))}
				{/* incoming photons + freed electrons */}
				{[0, 1, 2, 3, 4].map((k) => {
					const at = electrons - 22 + k * 7;
					const x = L.x + 260 + k * 170;
					const t = ramp(frame, at, 16, EASE.in);
					const hitT = frame - (at + 16);
					const free = springAt(frame, fps, at + 16, SPRING.wobbly);
					const fx = frame > flow ? x + ((flowT * 230 + k * 60) % 900) * 0 : x;
					const travel = frame > flow ? Math.min(1, (frame - flow - k * 4) / 26) : 0;
					const ex = fx + (L.x + 600 - fx) * EASE.inOut(Math.max(0, travel));
					const ey = L.top + 140 - free * 60 + (L.top + 20 - (L.top + 80)) * EASE.inOut(Math.max(0, travel));
					return (
						<g key={k}>
							{t > 0 && t < 1 ? <circle cx={x - 140 * (1 - t)} cy={L.top - 220 * (1 - t) + 40} r={13} fill={PALETTE.rimHot} stroke={PALETTE.rim} strokeWidth={3} /> : null}
							{hitT >= 0 && hitT < 10 ? <circle cx={x} cy={L.top + 60} r={20 + hitT * 6} fill="none" stroke={PALETTE.rimHot} strokeWidth={8 - hitT * 0.7} /> : null}
							{free > 0.01 && travel < 1 ? (
								<g transform={`translate(${ex} ${ey}) scale(${free})`}>
									<circle r={26} fill={PALETTE.electron} opacity={0.35} />
									<circle r={15} fill={PALETTE.electron} stroke={PALETTE.ink} strokeWidth={4} />
									<path d="M-7 0 H7" stroke={PALETTE.ink} strokeWidth={4} strokeLinecap="round" />
								</g>
							) : null}
						</g>
					);
				})}
				{label('Inside a solar cell', 360, 120, toInsert + 6, PALETTE.rim)}
				{label('n-type silicon', L.x + 24, L.top + 112, silicon - 4)}
				{label('p-type silicon', L.x + 24, L.top + 420, silicon + 4)}
				{label('free electron', L.x + 880, L.top - 30, electrons + 12, PALETTE.electron)}
				{frame > current - 2 ? (
					<g opacity={inOut(frame, current - 2, current + 200, 10)}>
						<rect x={1180} y={80} width={420} height={74} rx={37} fill={PALETTE.ink} opacity={0.75} />
						{label('electric current', 1220, 132, current, PALETTE.windowLit)}
					</g>
				) : null}
			</svg>
		</AbsoluteFill>
	);
};

/** DC → AC: a flat line morphs into a sine wave, then a home lights up. Screen-space card. */
export const InverterCard: React.FC<{frame: number; fps: number; cues: Record<string, number>; until: number}> = ({frame, fps, cues, until}) => {
	const {inverter, acWave, homes} = cues;
	const s = springAt(frame, fps, inverter + 4, SPRING.pop);
	const out = 1 - ramp(frame, until - 10, 10, EASE.in);
	if (frame < inverter) return null;
	const amp = interpolate(frame, [acWave, acWave + 22], [0, 46], {easing: EASE.out, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const phase = frame / 5;
	let wave = '';
	for (let i = 0; i <= 60; i++) {
		const x = 560 + i * 8;
		wave += `${i ? 'L' : 'M'}${x} ${240 + Math.sin(i / 4.7 + phase) * amp}`;
	}
	const home = springAt(frame, fps, homes, SPRING.pop);
	const word = (txt: string, x: number, at: number, c: string) => {
		const k = springAt(frame, fps, at, SPRING.pop);
		return <text x={x} y={170 - 10 * (1 - k)} opacity={k} fontFamily={FONT} fontSize={38} fontWeight={700} fill={c}>{txt}</text>;
	};
	return (
		<svg width={1920} height={1080} style={{position: 'absolute', opacity: out}}>
			<g transform={`translate(960 0) scale(${s}) translate(-960 0)`}>
				<rect x={330} y={110} width={1260} height={240} rx={44} fill={PALETTE.ink} opacity={0.82} />
				<path d="M380 240 H520" stroke={PALETTE.electron} strokeWidth={10} strokeLinecap="round" />
				{word('DC', 410, inverter + 6, PALETTE.electron)}
				<path d="M530 240 l20 -14 v28 z" fill={PALETTE.cream} />
				<path d={wave} stroke={PALETTE.windowLit} strokeWidth={10} fill="none" strokeLinecap="round" strokeLinejoin="round" />
				{word('AC', 760, acWave + 8, PALETTE.windowLit)}
				<path d="M1080 240 h120 l-18 -16 m18 16 l-18 16" stroke={PALETTE.cream} strokeWidth={8} fill="none" strokeLinecap="round" />
				<g transform={`translate(1330 250) scale(${0.6 + 0.4 * home})`}>
					<circle r={80 * home} fill={PALETTE.windowLit} opacity={0.25} />
					<Lit d="M-60 0 L0 -56 L60 0 Z" fill={PALETTE.roof} />
					<Lit d={rrect(-48, 0, 96, 70, 8)} fill={PALETTE.wall} />
					<Lit d={rrect(-16, 20, 32, 32, 6)} fill={home > 0.5 ? PALETTE.windowLit : PALETTE.window} glow={home} />
				</g>
			</g>
		</svg>
	);
};

/** Idea bulb that pops above Pip's head (anticipation squash → overshoot → glow). */
export const Bulb: React.FC<{x: number; y: number; frame: number; fps: number; at: number}> = ({x, y, frame, fps, at}) => {
	if (frame < at - 2) return null;
	const s = springAt(frame, fps, at, SPRING.wobbly);
	const glow = ramp(frame, at + 4, 14);
	return (
		<svg width={1920} height={1080} style={{position: 'absolute'}}>
			<g transform={`translate(${x} ${y - 30 * s}) scale(${s}) rotate(${(1 - s) * 25})`}>
				<circle r={150 * glow} fill={PALETTE.windowLit} opacity={0.3 + 0.1 * Math.sin(frame / 4)} />
				{Array.from({length: 8}, (_, i) => {
					const a = (i / 8) * Math.PI * 2 - Math.PI / 2;
					return <line key={i} x1={Math.cos(a) * 92} y1={Math.sin(a) * 92 - 10} x2={Math.cos(a) * (110 + 16 * glow)} y2={Math.sin(a) * (110 + 16 * glow) - 10}
						stroke={PALETTE.windowLit} strokeWidth={10} strokeLinecap="round" opacity={glow} />;
				})}
				<Lit d={ellipse(0, -14, 62, 66)} fill={PALETTE.windowLit} glow={1} />
				<path d="M-16 4 q8 -26 16 0 q8 26 16 0" stroke={PALETTE.shoe} strokeWidth={6} fill="none" strokeLinecap="round" />
				<Lit d={rrect(-28, 48, 56, 42, 9)} fill={PALETTE.metal} />
			</g>
		</svg>
	);
};
