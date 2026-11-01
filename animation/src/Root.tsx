import React from 'react';
import {Composition} from 'remotion';
import './fonts';
import {ModelSheet} from './compositions/ModelSheet';
import {SOLAR_PIP, SolarPip} from './compositions/SolarPip';

export const Root: React.FC = () => (
	<>
		<Composition id="SolarPip" component={SolarPip} {...SOLAR_PIP} />
		<Composition id="ModelSheet" component={ModelSheet} durationInFrames={1} fps={30} width={1920} height={1080} />
	</>
);
