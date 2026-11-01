import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {Pip, blinkAt, poseAt} from '../characters/Pip';
import {Captions, EndCard, Grade, Iris, KineticTitle} from '../components/Overlays';
import {Bulb, Burst, InverterCard, Photons, SiliconInsert} from '../graphics/Explainer';
import {Key, breathe, ramp, track} from '../lib/motion';
import {Production, lineFrames, makeCue, mouthAt} from '../lib/production';
import {EASE} from '../theme';
import {Cam, W, worldToScreen} from '../world/camera';
import {Foreground, World} from '../world/World';
import production from '../generated/solar-pip.json';

const P = production as Production;

export const SOLAR_PIP = {fps: P.fps, width: P.width, height: P.height, durationInFrames: P.durationInFrames};

export const SolarPip: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const c = makeCue(P);
	const sec = (s: number) => Math.round(s * fps);
	const cues = Object.fromEntries(Object.keys(P.cues).map((k) => [k, c(k)]));
	const l1 = lineFrames(P, 'l1');
	const l7 = lineFrames(P, 'l7');

	// ---------------- camera: every move is motivated by a narration cue
	const E = EASE.camera;
	const camKeys: Record<'x' | 'y' | 'zoom', Key[]> = {
		x: [[0, 980], [c('pointCity'), 840, E], [c('panToSun'), 930, E], [c('panToSun') + sec(1.4), 780, E], [c('pushPanel'), 820, E],
			[c('hit'), 1250, EASE.out], [c('toInsert'), 1255, E], [c('toInsert') + 1, 1483], [c('trackLines'), 1470, E],
			[c('trackLines') + sec(0.8), 1720, E], [c('cityLights') - sec(0.1), 3420, E], [c('toPip') - 1, 3450, E], [c('toPip'), 730], [c('endCard'), 740, E]],
		y: [[0, 610], [c('pointCity'), 640, E], [c('panToSun'), 630, E], [c('panToSun') + sec(1.4), 470, E], [c('pushPanel'), 485, E],
			[c('hit'), 560, EASE.out], [c('toInsert'), 565, E], [c('toInsert') + 1, 780], [c('trackLines'), 770, E],
			[c('trackLines') + sec(0.8), 670, E], [c('cityLights') - sec(0.1), 600, E], [c('toPip') - 1, 600, E], [c('toPip'), 610], [c('endCard'), 600, E]],
		zoom: [[0, 1.12], [c('pointCity'), 1.36, E], [c('panToSun'), 1.3, E], [c('panToSun') + sec(1.4), 0.92, E], [c('pushPanel'), 0.98, E],
			[c('hit'), 2.5, E], [c('toInsert'), 2.75, E], [c('toInsert') + 1, 2.3], [c('trackLines'), 2.45, E],
			[c('trackLines') + sec(0.8), 1.45, E], [c('cityLights') - sec(0.1), 1.0, E], [c('toPip') - 1, 1.08, E], [c('toPip'), 1.85], [c('endCard'), 2.02, E]],
	};
	const camAt = (f: number): Cam => ({x: track(f, camKeys.x), y: track(f, camKeys.y), zoom: track(f, camKeys.zoom)});
	const cam: Cam = camAt(frame);
	// motion blur proportional to on-screen camera speed (a fast pass-by should smear, not read as a crop)
	const prevCam = camAt(frame - 1);
	// directional: blur along the axis of motion (anisotropic gaussian), zoom adds a little to both axes
	const vx = Math.abs(cam.x - prevCam.x) * cam.zoom;
	const vy = Math.abs(cam.y - prevCam.y) * cam.zoom;
	const vz = Math.abs(cam.zoom - prevCam.zoom) * 250;
	const bx = frame > 0 ? Math.min(14, Math.max(0, (vx + vz - 16) / 4)) : 0;
	const by = frame > 0 ? Math.min(8, Math.max(0, (vy + vz - 16) / 5)) : 0;
	const moveBlur = bx + by > 0.3;
	// handheld-free micro drift so holds never freeze
	cam.x += breathe(frame, fps, 7, 6);
	cam.y += breathe(frame, fps, 9, 4, 1);

	// ---------------- world state
	const lightsOn = ramp(frame, c('cityLights'), sec(1.1), EASE.out);
	const s = {
		frame, fps,
		dusk: ramp(frame, c('trackLines'), c('cityLights') + sec(0.3) - c('trackLines'), EASE.inOut) * 0.85,
		panelFlash: Math.max(frame > c('photons') && frame < c('toInsert') ? 0.18 + 0.12 * Math.sin(frame / 2.5) : 0, 1 - ramp(frame, c('hit'), sec(0.7))),
		inverterGlow: ramp(frame, c('inverter'), sec(0.4)),
		lights: lightsOn,
		wirePulse: ramp(frame, c('trackLines') - 6, sec(0.4)),
	};
	if (frame < c('hit')) s.panelFlash = Math.min(s.panelFlash, frame > c('photons') ? 0.3 : 0);

	// ---------------- Pip's acting
	const schedule: [number, 'idle' | 'wave' | 'lookUp' | 'point' | 'in' | 'out' | 'cheer'][] = [
		[0, 'idle'], [c('wave'), 'wave'], [c('wave') + sec(1.3), 'idle'], [c('lookSun'), 'lookUp'], [c('pointCity'), 'point'],
		[c('pointCity') + sec(1.1), 'idle'], [c('inGesture'), 'in'], [c('outGesture'), 'out'], [c('bulb'), 'cheer'],
	];
	const arms = poseAt(frame, fps, schedule);
	if (frame >= c('wave') && frame < c('wave') + sec(1.3)) arms.rE += Math.sin((frame - c('wave')) / 3.2) * 26; // the wave itself
	const look = (() => {
		if (frame >= c('toPip')) {
			if (frame >= c('wink')) return {x: 0, y: 0.05};
			if (frame >= c('bulb')) return {x: 0.35, y: -1};
			if (frame >= c('outGesture')) return {x: 0.85, y: -0.1};
			if (frame >= c('inGesture')) return {x: -0.75, y: -0.6};
			return {x: 0, y: 0.05};
		}
		if (frame >= c('photons')) return {x: 0.75, y: -0.55}; // following photons to the roof
		if (frame >= c('panToSun')) return {x: -0.7, y: -0.9};
		if (frame >= c('pointCity')) return {x: 1, y: 0};
		if (frame >= c('lookSun')) return {x: -0.85, y: -0.85};
		return {x: 0, y: 0.1};
	})();
	const headTilt = frame >= c('lookSun') && frame < c('pointCity') ? -9 : frame >= c('pointCity') && frame < c('panToSun') ? 5 : frame >= c('bulb') ? -4 : 0;
	const speaking = (frame >= l1.start && frame <= l1.end + 3) || (frame >= l7.start && frame <= l7.end + 3);
	const mouth = speaking ? mouthAt(P, frame) * 0.95 : 0;
	// hop on the "bright idea": anticipation squash → airborne stretch → landing squash
	const jt = (frame - c('bulb')) / sec(0.5);
	const hop = jt > 0 && jt < 1 ? Math.sin(jt * Math.PI) * 70 : 0;
	const squash =
		frame >= c('bulb') - 6 && frame < c('bulb') ? 0.09 * ramp(frame, c('bulb') - 6, 6) :
		jt > 0 && jt < 1 ? -0.07 * Math.sin(jt * Math.PI) :
		jt >= 1 && jt < 1.4 ? 0.08 * (1 - (jt - 1) / 0.4) :
		frame >= c('wave') - 5 && frame < c('wave') ? 0.05 : 0;
	const vel = jt > 0 && jt < 1 ? Math.cos(jt * Math.PI) * 70 : 0;

	// ---------------- screen-space anchors for graphics
	const panelScr = worldToScreen(cam, 1, [(W.panel.x1 + W.panel.x2) / 2 + 22, (W.panel.y1 + W.panel.y2) / 2 + 24]);
	const headScr = worldToScreen(cam, 1, [W.pip[0] + 175, W.pip[1] - 420 - hop*0.4]);
	const whip = Math.max(0, 1 - Math.abs(frame - c('toPip')) / 4); // motion blur across the whip-cut
	const insertOn = frame >= c('toInsert') && frame < c('toInverter');
	const insertOut = 1 - ramp(frame, c('toInverter') - 8, 8, EASE.in);

	return (
		<AbsoluteFill style={{background: '#000'}}>
			<svg width={0} height={0} style={{position: 'absolute'}}>
				<filter id="camBlur" x="-5%" y="-5%" width="110%" height="110%">
					<feGaussianBlur stdDeviation={`${Math.max(bx, whip * 18).toFixed(2)} ${Math.max(by, whip * 4).toFixed(2)}`} edgeMode="duplicate" />
				</filter>
			</svg>
			<AbsoluteFill style={{filter: whip > 0 || moveBlur ? 'url(#camBlur)' : undefined}}>
				<World cam={cam} s={s} />
				<AbsoluteFill>
					<svg width={1920} height={1080} style={{position: 'absolute'}}>
						<g transform={`translate(1920 ${0}) scale(0)`} />
						{(() => {
							const [px, py] = worldToScreen(cam, 1, [W.pip[0], W.pip[1] - hop]);
							const z = cam.zoom;
							return (
								<Pip x={px} y={py} scale={z * 0.98} arms={arms} look={look} mouth={mouth} smile={frame >= c('bulb') ? 0.95 : 0.65}
									brow={frame >= c('bulb') ? 0.8 : frame >= c('lookSun') && frame < c('pointCity') ? 0.6 : 0.15}
									blink={blinkAt(frame, fps)} wink={frame >= c('wink') && frame < c('wink') + 14 ? 1 : 0}
									squash={squash} headTilt={headTilt + breathe(frame, fps, 4.2, 1.5)} bob={breathe(frame, fps, 3.2, 3)}
									hairSway={-vel * 0.25 + breathe(frame, fps, 2.1, 4)} rimGlow={frame >= c('toPip') ? 0.4 : 0.15} />
							);
						})()}
					</svg>
				</AbsoluteFill>
				<Photons cam={cam} frame={frame} start={c('photons') - 4} end={c('toInsert')} rate={2} />
				<Burst x={panelScr[0]} y={panelScr[1]} frame={frame} at={c('hit')} scale={2.2} />
				<Foreground cam={cam} frame={frame} blur={cam.zoom > 1.7 ? 7 : 3} />
				<InverterCard frame={frame} fps={fps} cues={cues} until={c('trackLines') + 8} />
				<Bulb x={headScr[0]} y={headScr[1]} frame={frame} fps={fps} at={c('bulb')} />
			</AbsoluteFill>
			{insertOn ? (
				<AbsoluteFill style={{opacity: insertOut, transform: `scale(${0.9 + 0.1 * insertOut})`}}>
					<Iris frame={frame} start={c('toInsert')} dur={sec(0.5)} x={panelScr[0]} y={panelScr[1]}>
						<SiliconInsert frame={frame} fps={fps} cues={cues} />
					</Iris>
				</AbsoluteFill>
			) : null}
			{whip > 0.6 ? <AbsoluteFill style={{background: '#fff3d6', opacity: (whip - 0.6) * 0.8}} /> : null}
			<KineticTitle text={P.title} frame={frame} fps={fps} start={0} end={sec(3.1)} y={64} size={74} />
			<EndCard frame={frame} fps={fps} start={c('endCard')} title="Sunlight in. Electricity out." />
			{frame >= c('endCard') + 10 ? (
				<svg width={1920} height={1080} style={{position: 'absolute'}}>
					{(() => {
						const e = c('endCard') + 10;
						const enter = Math.min(1, (frame - e) / 14);
						const arms2 = poseAt(frame, fps, [[0, 'idle'], [e + 8, 'wave']]);
						arms2.rE += Math.sin((frame - e) / 3.2) * 24;
						return (
							<Pip x={270} y={1020 + 300 * (1 - EASE.out(enter))} scale={0.95} arms={arms2} look={{x: 0.6, y: -0.2}} smile={0.9}
								mouth={0} brow={0.4} blink={blinkAt(frame, fps, 11)} bob={breathe(frame, fps, 3, 3)} hairSway={breathe(frame, fps, 2, 5)} rimGlow={0.3} />
						);
					})()}
				</svg>
			) : null}
			<Grade frame={frame} warmth={1 - s.dusk * 0.4} />
			<Captions words={P.lines.flatMap((l) => l.words)} frame={frame} fps={fps} hideFrom={c('endCard')} />
		</AbsoluteFill>
	);
};
