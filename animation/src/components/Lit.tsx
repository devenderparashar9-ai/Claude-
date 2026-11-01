import React, {useId} from 'react';
import {LIGHT, OUTLINE, PALETTE, RIM_WIDTH, SHADOW_WIDTH, rimOf, shade} from '../theme';

/**
 * A lit cartoon shape: base fill, purple shadow crescent away from the light,
 * warm golden rim on the lit edge, constant-width ink outline.
 * Every character/prop shape goes through this so the lighting is consistent.
 */
export const Lit: React.FC<{
	d: string;
	fill: string;
	rim?: number; // rim width multiplier (0 = none)
	shadow?: number; // shadow width multiplier
	outline?: number;
	light?: {dx: number; dy: number};
	glow?: number; // 0..1 extra rim intensity (e.g. when facing the sun)
}> = ({d, fill, rim = 1, shadow = 1, outline = 1, light = LIGHT, glow = 0}) => {
	const id = useId().replace(/[^a-zA-Z0-9]/g, '');
	const len = Math.hypot(light.dx, light.dy) || 1;
	const lx = light.dx / len;
	const ly = light.dy / len;
	const s = SHADOW_WIDTH * shadow;
	const r = RIM_WIDTH * rim;
	return (
		<g>
			<defs>
				<clipPath id={`c${id}`}>
					<path d={d} />
				</clipPath>
				{r > 0 ? (
					<mask id={`m${id}`} maskUnits="userSpaceOnUse" x={-5000} y={-5000} width={10000} height={10000}>
						<path d={d} fill="white" />
						<path d={d} fill="black" transform={`translate(${-lx * r} ${-ly * r})`} />
					</mask>
				) : null}
			</defs>
			<g clipPath={`url(#c${id})`}>
				<path d={d} fill={shadow > 0 ? shade(fill) : fill} />
				<path d={d} fill={fill} transform={`translate(${lx * s} ${ly * s})`} />
				{r > 0 ? <path d={d} fill={glow > 0.5 ? PALETTE.rimHot : rimOf(fill)} mask={`url(#m${id})`} opacity={0.85 + 0.15 * glow} /> : null}
			</g>
			{outline > 0 ? <path d={d} fill="none" stroke={PALETTE.ink} strokeWidth={OUTLINE * outline} strokeLinejoin="round" /> : null}
		</g>
	);
};

/** Thick rounded limb (arm/leg) with outline, shadow edge and rim edge. */
export const Limb: React.FC<{points: number[][]; width: number; color: string}> = ({points, width, color}) => {
	const d = 'M' + points.map((p) => `${p[0].toFixed(2)} ${p[1].toFixed(2)}`).join(' L');
	return (
		<g strokeLinecap="round" strokeLinejoin="round" fill="none">
			<path d={d} stroke={PALETTE.ink} strokeWidth={width + OUTLINE * 2} />
			<path d={d} stroke={shade(color)} strokeWidth={width} />
			<path d={d} stroke={color} strokeWidth={width * 0.62} transform={`translate(${LIGHT.dx * width * 0.12} ${LIGHT.dy * width * 0.12})`} />
			<path d={d} stroke={rimOf(color)} strokeWidth={width * 0.14} transform={`translate(${LIGHT.dx * width * 0.3} ${LIGHT.dy * width * 0.3})`} opacity={0.9} />
		</g>
	);
};

/** Rounded-rectangle path helper. */
export const rrect = (x: number, y: number, w: number, h: number, r: number) =>
	`M${x + r} ${y} H${x + w - r} Q${x + w} ${y} ${x + w} ${y + r} V${y + h - r} Q${x + w} ${y + h} ${x + w - r} ${y + h} H${x + r} Q${x} ${y + h} ${x} ${y + h - r} V${y + r} Q${x} ${y} ${x + r} ${y} Z`;

export const ellipse = (cx: number, cy: number, rx: number, ry: number) =>
	`M${cx - rx} ${cy} A${rx} ${ry} 0 1 0 ${cx + rx} ${cy} A${rx} ${ry} 0 1 0 ${cx - rx} ${cy} Z`;
