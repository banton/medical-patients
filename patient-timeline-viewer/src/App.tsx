import { useState, useEffect, useMemo } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Patient, PlaybackState, FacilityName } from './types/patient.types';
import { FileUploader } from './components/FileUploader';
import { FacilityColumn } from './components/FacilityColumn';
import { TimelineControls } from './components/TimelineControls';
import { getTimelineExtent } from './utils/timelineEngine';
import './index.css';

const FACILITIES: FacilityName[] = ['POI', 'Role1', 'Role2', 'Role3', 'Role4'];

function App() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [playbackState, setPlaybackState] = useState<PlaybackState>({
    isPlaying: false,
    currentTime: new Date('2024-01-01T00:00:00Z'),
    speed: 1,
    startTime: new Date('2024-01-01T00:00:00Z'),
    endTime: new Date('2024-01-01T24:00:00Z')
  });

  // Update timeline extent when patients change
  useEffect(() => {
    if (patients.length > 0) {
      const extent = getTimelineExtent(patients);
      setPlaybackState(prev => ({
        ...prev,
        currentTime: extent.start,
        startTime: extent.start,
        endTime: extent.end
      }));
    }
  }, [patients]);

  // Timeline playback effect
  useEffect(() => {
    if (!playbackState.isPlaying) return;

    const interval = setInterval(() => {
      setPlaybackState(prev => {
        const nextTime = new Date(prev.currentTime.getTime() + (3600000 * prev.speed)); // Advance by 1 hour * speed
        
        // Stop if we've reached the end
        if (nextTime >= prev.endTime) {
          return {
            ...prev,
            currentTime: prev.endTime,
            isPlaying: false
          };
        }
        
        return {
          ...prev,
          currentTime: nextTime
        };
      });
    }, 100); // Update every 100ms for smooth animation

    return () => clearInterval(interval);
  }, [playbackState.isPlaying, playbackState.speed]);

  // Control handlers
  const handlePlayPause = () => {
    setPlaybackState(prev => ({
      ...prev,
      isPlaying: !prev.isPlaying
    }));
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackState(prev => ({
      ...prev,
      speed
    }));
  };

  const handleReset = () => {
    setPlaybackState(prev => ({
      ...prev,
      currentTime: prev.startTime,
      isPlaying: false
    }));
  };

  const handleTimeSeek = (time: Date) => {
    setPlaybackState(prev => ({
      ...prev,
      currentTime: time,
      isPlaying: false
    }));
  };

  const handleLoadPatients = (loadedPatients: Patient[]) => {
    setPatients(loadedPatients);
    console.log(`Loaded ${loadedPatients.length} patients`);
  };

  // Calculate statistics
  const statistics = useMemo(() => {
    if (patients.length === 0) return null;

    const totalPatients = patients.length;
    const finalStatuses = patients.reduce((acc, patient) => {
      acc[patient.final_status] = (acc[patient.final_status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const triageCounts = patients.reduce((acc, patient) => {
      acc[patient.triage_category] = (acc[patient.triage_category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      total: totalPatients,
      finalStatuses,
      triageCounts
    };
  }, [patients]);

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 p-4">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Patient Timeline Visualizer
          </h1>
          <p className="text-gray-600">
            Military Medical Evacuation Flow Simulator - Load patients.json to visualize patient movement through medical facilities
          </p>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {patients.length === 0 ? (
          // File upload state
          <div className="flex-1 flex items-center justify-center">
            <div className="max-w-2xl w-full px-4">
              <FileUploader onLoad={handleLoadPatients} />
              
              {/* Instructions */}
              <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h3 className="font-semibold text-blue-900 mb-3">How to use:</h3>
                <ol className="list-decimal list-inside space-y-2 text-blue-800 text-sm">
                  <li>Generate patient data from the main application</li>
                  <li>Download the patients.json file</li>
                  <li>Upload the file using the drag-and-drop area above</li>
                  <li>Use the timeline controls to visualize patient flow</li>
                  <li>Watch patients move through POI → Role1 → Role2 → Role3 → Role4</li>
                </ol>
              </div>
            </div>
          </div>
        ) : (
          // Timeline visualization
          <>
            {/* Statistics bar */}
            {statistics && (
              <div className="bg-white border-b border-gray-200 p-4">
                <div className="max-w-6xl mx-auto flex items-center justify-between">
                  <div className="flex items-center space-x-6 text-sm">
                    <span className="font-medium">
                      Total Patients: {statistics.total}
                    </span>
                    <div className="flex space-x-3">
                      <span className="text-red-600">
                        KIA: {statistics.finalStatuses.KIA || 0}
                      </span>
                      <span className="text-green-600">
                        RTD: {statistics.finalStatuses.RTD || 0}
                      </span>
                      <span className="text-blue-600">
                        Remains: {statistics.finalStatuses.Remains_Role4 || 0}
                      </span>
                    </div>
                  </div>
                  <div className="flex space-x-3 text-sm">
                    <span className="bg-red-100 text-red-800 px-2 py-1 rounded">
                      T1: {statistics.triageCounts.T1 || 0}
                    </span>
                    <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                      T2: {statistics.triageCounts.T2 || 0}
                    </span>
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded">
                      T3: {statistics.triageCounts.T3 || 0}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Facility columns */}
            <div className="flex-1 grid grid-cols-5 gap-4 p-4 overflow-hidden">
              <AnimatePresence>
                {FACILITIES.map((facility) => (
                  <FacilityColumn
                    key={facility}
                    name={facility}
                    patients={patients}
                    currentTime={playbackState.currentTime}
                    className="h-full"
                  />
                ))}
              </AnimatePresence>
            </div>

            {/* Timeline controls */}
            <TimelineControls
              playbackState={playbackState}
              onPlayPause={handlePlayPause}
              onSpeedChange={handleSpeedChange}
              onReset={handleReset}
              onTimeSeek={handleTimeSeek}
            />
          </>
        )}
      </main>
    </div>
  );
}

export default App;