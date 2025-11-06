import React from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import Svg, { Path } from 'react-native-svg';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

interface WaveBackgroundProps {
  topColor?: string;
  bottomColor?: string;
  wavePosition?: number; // Percentage of screen height where wave starts (0-1)
}

// Original SVG path from wave2.svg (500x500 dimensions)
const ORIGINAL_SVG_PATH = "M0 0 C165 0 330 0 500 0 C500 87.12 500 174.24 500 264 C484.49 266.31 468.98 268.62 453 271 C424.96742199 278.47535413 402.83238196 289.37624267 381 308.40234375 C378.09180721 310.92050548 375.12430701 313.34158907 372.125 315.75 C364.79054146 321.76341053 358.97690015 328.18076045 353.19628906 335.66137695 C349.04611314 341.01288211 344.58171234 346.01453523 340 351 C338.87060071 352.28782181 337.745415 353.57935422 336.625 354.875 C335.41865659 356.25174617 334.21017823 357.62662347 333 359 C332.31679688 359.77730469 331.63359375 360.55460937 330.9296875 361.35546875 C305.87823362 389.26649374 279.88891089 411.9378297 244.9140625 426.5 C239.9113909 428.58513603 235.00920632 430.84136906 230.109375 433.15625 C220.8000503 437.54284279 211.41840199 441.5312361 201.75 445.0625 C200.25170654 445.61756226 200.25170654 445.61756226 198.72314453 446.18383789 C187.77698455 450.06969729 176.70653278 451.44294583 165.13623047 451.90771484 C163.71008847 451.96932418 162.28449321 452.04521911 160.85986328 452.13525391 C140.85379561 453.33938361 121.00331233 449.53166472 101.32275391 446.36981201 C99.27261633 446.04340399 97.22042772 445.72993494 95.16796875 445.41845703 C79.09438197 442.96067151 63.89548633 438.41061544 48.50488281 433.27685547 C35.71188559 429.03021877 23.10750272 426.01720538 9.625 424.875 C1.12244463 424.12244463 1.12244463 424.12244463 0 423 C-0.09813731 420.75870732 -0.12371098 418.51424448 -0.12304783 416.27080441 C-0.12477845 415.19740756 -0.12477845 415.19740756 -0.12654402 414.10232592 C-0.12921628 411.67520451 -0.12468456 409.24814779 -0.12025452 406.82102966 C-0.12069149 405.07961003 -0.12156757 403.33819046 -0.12284851 401.59677124 C-0.12510398 396.77815606 -0.12106112 391.95956287 -0.11607273 387.14095049 C-0.11172593 381.87743752 -0.11316602 376.61392568 -0.11389065 371.35041142 C-0.11442372 361.11920236 -0.10979273 350.88800204 -0.10338932 340.65679524 C-0.0962078 328.82983039 -0.09539559 317.00287083 -0.09460449 305.17590332 C-0.08934762 273.92976749 -0.0753866 242.68363362 -0.0625 211.4375 C-0.041875 141.663125 -0.02125 71.88875 0 0 Z";

const ORIGINAL_SVG_WIDTH = 500;
const ORIGINAL_SVG_HEIGHT = 500;

export default function WaveBackground({ 
  topColor = '#DBEDEC', // White for top section
  bottomColor = '#FFFFFF', // DBEDEC for bottom section
  wavePosition = 0.5 // Not used with custom SVG, but kept for compatibility
}: WaveBackgroundProps) {
  // SVG only covers upper half of screen
  const svgHeight = SCREEN_HEIGHT / 1.8;
  
  return (
    <View style={styles.container}>
      {/* Background for bottom section */}
      <View style={[styles.bottomSection, { backgroundColor: bottomColor, top: svgHeight }]} />
      
      {/* Wave SVG - uses wave2.svg path, only covers upper half */}
      <Svg
        style={[styles.wave, { height: svgHeight }]}
        width={SCREEN_WIDTH}
        height={svgHeight}
        viewBox={`0 0 ${ORIGINAL_SVG_WIDTH} ${ORIGINAL_SVG_HEIGHT}`}
        preserveAspectRatio="none"
      >
        {/* Background for upper section (bottomColor) */}
        <Path
          d={`M 0 0 L ${ORIGINAL_SVG_WIDTH} 0 L ${ORIGINAL_SVG_WIDTH} ${ORIGINAL_SVG_HEIGHT} L 0 ${ORIGINAL_SVG_HEIGHT} Z`}
          fill={bottomColor}
        />
        {/* Wave shape from wave2.svg in top color */}
        <Path
          d={ORIGINAL_SVG_PATH}
          fill={topColor}
        />
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 0,
  },
  wave: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
  },
  bottomSection: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
  },
});

