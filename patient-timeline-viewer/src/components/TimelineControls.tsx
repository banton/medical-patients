import React from 'react';
import { motion } from 'framer-motion';
import { PlaybackState } from '../types/patient.types';
import { formatTimeDisplay, calculateHoursSinceInjury } from '../utils/timelineEngine';

interface TimelineControlsProps {
  playbackState: PlaybackState;
  onPlayPause: () => void;
  onSpeedChange: (speed: number) => void;
  onReset: () => void;
  onTimeSeek?: (time: Date) => void;
  className?: string;
}

export const TimelineControls: React.FC<TimelineControlsProps> = ({
  playbackState,
  onPlayPause,
  onSpeedChange,
  onReset,
  onTimeSeek,
  className = ''
}) => {
  const { isPlaying, currentTime, speed, startTime, endTime } = playbackState;

  // Calculate progress percentage
  const totalDuration = endTime.getTime() - startTime.getTime();
  const currentProgress = Math.max(0, Math.min(100, 
    ((currentTime.getTime() - startTime.getTime()) / totalDuration) * 100
  ));

  // Speed options (adjusted for slower playback)
  const speedOptions = [
    { value: 0.25, label: '0.25x' },
    { value: 0.5, label: '0.5x' },
    { value: 1, label: '1x' },
    { value: 2, label: '2x' },
    { value: 5, label: '5x' },
    { value: 10, label: '10x' }
  ];

  // Handle progress bar click
  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!onTimeSeek) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percentage = clickX / rect.width;
    
    const newTime = new Date(startTime.getTime() + (totalDuration * percentage));
    onTimeSeek(newTime);
  };

  // Calculate hours since start
  const hoursSinceStart = calculateHoursSinceInjury(currentTime, startTime);

  return (
    <div className={`bg-white border-t border-gray-200 p-4 ${className}`}>
      <div className="max-w-6xl mx-auto space-y-4">
        {/* Time display and progress */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-sm text-gray-600">
            <span>{formatTimeDisplay(currentTime)}</span>
            <span className="font-medium">
              {hoursSinceStart.toFixed(1)} hours elapsed
            </span>
            <span>{formatTimeDisplay(endTime)}</span>
          </div>
          
          {/* Progress bar */}
          <div 
            className="relative h-2 bg-gray-200 rounded-full cursor-pointer overflow-hidden"
            onClick={handleProgressClick}
          >
            <motion.div
              className="absolute left-0 top-0 h-full bg-blue-500 rounded-full"
              initial={{ width: '0%' }}
              animate={{ width: `${currentProgress}%` }}
              transition={{ duration: 0.1 }}
            />
            
            {/* Playhead indicator */}
            <motion.div
              className="absolute top-0 w-1 h-full bg-blue-700 shadow-sm"
              style={{ left: `${currentProgress}%` }}
              animate={{ x: -2 }}
            />
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-center space-x-6">
          {/* Play/Pause button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onPlayPause}
            className={`
              flex items-center justify-center w-12 h-12 rounded-full
              text-white font-medium transition-colors duration-200
              ${isPlaying 
                ? 'bg-red-500 hover:bg-red-600' 
                : 'bg-green-500 hover:bg-green-600'
              }
            `}
          >
            {isPlaying ? (
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
              </svg>
            ) : (
              <svg className="w-6 h-6 ml-1" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
            )}
          </motion.button>

          {/* Reset button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onReset}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors duration-200"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>
            </svg>
            <span className="font-medium">Reset</span>
          </motion.button>

          {/* Speed control */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600 font-medium">Speed:</span>
            <div className="flex space-x-1">
              {speedOptions.map((option) => (
                <motion.button
                  key={option.value}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => onSpeedChange(option.value)}
                  className={`
                    px-3 py-1 rounded-md text-sm font-medium transition-colors duration-200
                    ${speed === option.value
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }
                  `}
                >
                  {option.label}
                </motion.button>
              ))}
            </div>
          </div>
        </div>

        {/* Status info */}
        <div className="flex justify-center space-x-6 text-xs text-gray-500">
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            <span>Active Patients</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
            <span>In Transit</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
            <span>KIA</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>RTD</span>
          </div>
        </div>
      </div>
    </div>
  );
};