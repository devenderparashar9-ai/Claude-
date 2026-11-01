import React from 'react';
import {AbsoluteFill} from 'remotion';
import {POSES, Pip} from '../characters/Pip';
import {FONT, PALETTE} from '../theme';

/** Turnaround of every pose/expression — render as a still and review before animating. */
export const ModelSheet: React.FC = () => {
	const names = Object.keys(POSES) as (keyof typeof POSES)[];
	const exprs = [
		{mouth: 0, smile: 0.6, brow: 0},
		{mouth: 0.8, smile: 0.7, brow: 0.6},
		{mouth: 0.3, smile: 0.2, brow: 1},
		{mouth: 0, smile: 0.9, brow: 0.3, wink: 1},
		{mouth: 0.5, smile: 1, brow: 0.4},
		{mouth: 0, smile: 0.1, brow: -0.6},
		{mouth: 0.9, smile: 0.9, brow: 1},
		{mouth: 0, smile: 0.4, brow: -0.2},
	];
	return (
		<AbsoluteFill style={{background: `linear-gradient(${PALETTE.skyMid}, ${PALETTE.skyLow})`, fontFamily: FONT}}>
			<svg viewBox="0 0 1920 1080" width={1920} height={1080}>
				{names.map((n, i) => {
					const cx = 130 + (i % 4) * 450 + 100;
					const cy = i < 4 ? 500 : 1020;
					return (
						<g key={n}>
							<Pip x={cx} y={cy} scale={0.88} arms={POSES[n]} look={{x: i % 2 ? 0.6 : -0.4, y: -0.2}} {...exprs[i]} />
							<text x={cx + 150} y={cy - 360} fontSize={34} fill={PALETTE.ink} fontWeight={600} fontFamily={FONT}>{n}</text>
						</g>
					);
				})}
			</svg>
		</AbsoluteFill>
	);
};
