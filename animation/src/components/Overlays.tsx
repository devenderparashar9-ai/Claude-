import React from 'react';
import {AbsoluteFill, interpolate} from 'remotion';
import {Word} from '../lib/production';
import {inOut, rng, springAt} from '../lib/motion';
import {EASE, FONT, PALETTE, SPRING} from '../theme';

/** Phrase grouping identical in spirit to pipeline captions.group_phrases. */
export const groupPhrases = (words: Word[], maxWords = 5, maxChars = 28, maxGap = 0.45, maxDur = 2.6) => {
	const out: Word[][] = [];
	let cur: Word[] = [];
	for (const w of words) {
		if (cur.length) {
			const gap = w.start - cur[cur.length - 1].end;
			const len = [...cur, w].map((x) => x.word).join(' ').length;
			const last = cur[cur.length - 1].word.slice(-1);
			if (cur.length >= maxWords || len > maxChars || gap > maxGap || w.end - cur[0].start > maxDur || '.?!,;:'.includes(last)) {
				out.push(cur);
				cur = [];
			}
		}
		cur.push(w);
	}
	if (cur.length) out.push(cur);
	return out;
};

/** Karaoke captions: each word fills gold exactly while it is spoken, with a small lift. */
export const Captions: React.FC<{words: Word[]; frame: number; fps: number; hideFrom?: number}> = ({words, frame, fps, hideFrom = 1e9}) => {
	const t = frame / fps;
	const phrases = groupPhrases(words);
	const ph = phrases.find((p) => t >= p[0].start - 0.05 && t <= p[p.length - 1].end + 0.25);
	if (!ph || frame >= hideFrom) return null;
	const f0 = Math.round((ph[0].start - 0.05) * fps);
	const enter = springAt(frame, fps, f0, SPRING.pop);
	return (
		<AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 70}}>
			<div style={{
				fontFamily: FONT, fontWeight: 700, fontSize: 64, letterSpacing: 0.5,
				padding: '10px 30px 14px', borderRadius: 30, background: 'rgba(42,24,64,0.55)',
				transform: `translateY(${(1 - enter) * 24}px) scale(${0.92 + 0.08 * enter})`, opacity: enter,
				display: 'flex', gap: 18,
			}}>
				{ph.map((w, i) => {
					const on = t >= w.start;
					const k = interpolate(t, [w.start, w.start + 0.12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: EASE.out});
					return (
						<span key={i} style={{
							color: on ? PALETTE.windowLit : PALETTE.cream,
							transform: `translateY(${-6 * k * (1 - interpolate(t, [w.end, w.end + 0.2], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}))}px)`,
							display: 'inline-block',
							WebkitTextStroke: `3px ${PALETTE.ink}`, paintOrder: 'stroke fill',
							textShadow: on ? `0 0 18px rgba(255,207,107,0.55)` : 'none',
						}}>{w.word}</span>
					);
				})}
			</div>
		</AbsoluteFill>
	);
};

/** Kinetic title: letters spring in with stagger, then exit faster than they entered. */
export const KineticTitle: React.FC<{text: string; frame: number; fps: number; start: number; end: number; y?: number; size?: number}> = ({text, frame, fps, start, end, y = 120, size = 76}) => {
	if (frame < start || frame > end) return null;
	const out = interpolate(frame, [end - 10, end], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: EASE.in});
	return (
		<AbsoluteFill style={{alignItems: 'center', paddingTop: y}}>
			<div style={{fontFamily: FONT, fontWeight: 700, fontSize: size, display: 'flex', whiteSpace: 'pre'}}>
				{text.split('').map((ch, i) => {
					const s = springAt(frame, fps, start + i * 0.55, SPRING.pop);
					return (
						<span key={i} style={{
							display: 'inline-block', color: PALETTE.cream, WebkitTextStroke: `5px ${PALETTE.ink}`, paintOrder: 'stroke fill',
							transform: `translateY(${(1 - s) * 50 - out * 30}px) rotate(${(1 - s) * 12}deg) scale(${0.6 + 0.4 * s})`,
							opacity: s * (1 - out), textShadow: `0 6px 0 ${PALETTE.shadow}`,
						}}>{ch}</span>
					);
				})}
			</div>
		</AbsoluteFill>
	);
};

/** Cinematic finish: warm grade, purple-tinted vignette, bloom-ish highlight lift, seeded film grain. */
export const Grade: React.FC<{frame: number; warmth?: number}> = ({frame, warmth = 1}) => {
	const seed = Math.floor(frame / 2) % 97;
	return (
		<AbsoluteFill style={{pointerEvents: 'none'}}>
			<AbsoluteFill style={{background: `linear-gradient(160deg, rgba(255,190,110,${0.16 * warmth}), rgba(0,0,0,0) 45%, rgba(90,61,154,0.18))`, mixBlendMode: 'soft-light'}} />
			<AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 55%, rgba(42,24,64,0.55) 100%)'}} />
			<svg width={1920} height={1080} style={{position: 'absolute', opacity: 0.07, mixBlendMode: 'overlay'}}>
				<filter id="grain">
					<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={2} seed={seed} />
					<feColorMatrix type="saturate" values="0" />
				</filter>
				<rect width={1920} height={1080} filter="url(#grain)" />
			</svg>
		</AbsoluteFill>
	);
};

/** Circular iris transition (opens from a point of interest). */
export const Iris: React.FC<{frame: number; start: number; dur: number; x: number; y: number; children: React.ReactNode}> = ({frame, start, dur, x, y, children}) => {
	const t = EASE.inOut(Math.max(0, Math.min(1, (frame - start) / dur)));
	if (t <= 0) return null;
	const r = t * 2300;
	return (
		<AbsoluteFill style={{clipPath: `circle(${r}px at ${x}px ${y}px)`}}>
			{children}
			<svg width={1920} height={1080} style={{position: 'absolute'}}>
				{t < 1 ? <circle cx={x} cy={y} r={r} fill="none" stroke={PALETTE.rim} strokeWidth={14} /> : null}
			</svg>
		</AbsoluteFill>
	);
};

/** End card: staggered words, Pip-colour accents, subtle idle motion. */
export const EndCard: React.FC<{frame: number; fps: number; start: number; title: string}> = ({frame, fps, start, title}) => {
	if (frame < start) return null;
	const bg = springAt(frame, fps, start, SPRING.soft);
	const words = title.split(' ');
	const r = rng(3);
	return (
		<AbsoluteFill style={{clipPath: `circle(${bg * 1500}px at 960px 540px)`, background: `radial-gradient(circle at 50% 40%, ${PALETTE.duskMid}, ${PALETTE.duskTop})`}}>
			<svg width={1920} height={1080} style={{position: 'absolute'}}>
				{Array.from({length: 26}, (_, i) => {
					const x = r() * 1920;
					const y = r() * 1080;
					return <circle key={i} cx={x} cy={y - ((frame - start) * (0.6 + r())) % 200} r={4 + r() * 6} fill={PALETTE.rim} opacity={0.25 + 0.2 * Math.sin(frame / 9 + i)} />;
				})}
			</svg>
			<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', flexDirection: 'column', gap: 26}}>
				<div style={{display: 'flex', gap: 26, fontFamily: FONT, fontWeight: 700, fontSize: 104}}>
					{words.map((w, i) => {
						const s = springAt(frame, fps, start + 8 + i * 5, SPRING.pop);
						return <span key={i} style={{display: 'inline-block', color: i % 2 ? PALETTE.windowLit : PALETTE.cream, WebkitTextStroke: `6px ${PALETTE.ink}`, paintOrder: 'stroke fill',
							transform: `translateY(${(1 - s) * 60}px) scale(${0.5 + 0.5 * s})`, opacity: s, textShadow: `0 8px 0 ${PALETTE.shadow}`}}>{w}</span>;
					})}
				</div>
				<div style={{fontFamily: FONT, fontWeight: 600, fontSize: 44, color: PALETTE.cream, opacity: inOut(frame, start + 30, start + 400, 16),
					transform: `translateY(${(1 - springAt(frame, fps, start + 30, SPRING.soft)) * 20}px)`}}>Learn with Pip</div>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
