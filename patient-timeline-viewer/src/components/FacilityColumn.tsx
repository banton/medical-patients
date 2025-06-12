import React, { useRef, useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Patient, FacilityName } from '../types/patient.types';
import { PatientCard } from './PatientCard';
import { getPatientLocationAtTime } from '../utils/timelineEngine';

interface FacilityColumnProps {
  name: FacilityName;
  patients: Patient[];
  currentTime: Date;
  cumulativeCounts: { kia: number; rtd: number };
  className?: string;
}

export const FacilityColumn: React.FC<FacilityColumnProps> = ({ 
  name, 
  patients, 
  currentTime,
  cumulativeCounts,
  className = '' 
}) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [scrollInfo, setScrollInfo] = useState({ atBottom: true, hiddenCount: 0 });
  // Get facility metadata
  const getFacilityInfo = (facilityName: FacilityName) => {
    switch (facilityName) {
      case 'POI':
        return {
          displayName: 'Point of Injury',
          icon: '🎯',
          color: 'border-red-400 bg-red-50',
          description: 'Initial injury site'
        };
      case 'Role1':
        return {
          displayName: 'Role 1',
          icon: '🏕️',
          color: 'border-orange-400 bg-orange-50',
          description: 'Forward medical care'
        };
      case 'Role2':
        return {
          displayName: 'Role 2',
          icon: '🏥',
          color: 'border-blue-400 bg-blue-50',
          description: 'Field hospital'
        };
      case 'Role3':
        return {
          displayName: 'Role 3',
          icon: '🏢',
          color: 'border-purple-400 bg-purple-50',
          description: 'Combat support hospital'
        };
      case 'Role4':
        return {
          displayName: 'Role 4',
          icon: '🏛️',
          color: 'border-green-400 bg-green-50',
          description: 'Definitive medical care'
        };
      default:
        return {
          displayName: facilityName,
          icon: '🏥',
          color: 'border-gray-400 bg-gray-50',
          description: 'Medical facility'
        };
    }
  };

  const facilityInfo = getFacilityInfo(name);

  // Filter and get location info for each patient (exclude hidden patients)
  const patientsWithLocation = patients.map(patient => ({
    patient,
    location: getPatientLocationAtTime(patient, currentTime)
  })).filter(({ location }) => 
    location.facility === name && location.status !== 'hidden'
  );

  // Count patients by status
  const statusCounts = patientsWithLocation.reduce((acc, { location }) => {
    acc[location.status] = (acc[location.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Handle scroll tracking for viewport grouping
  const handleScroll = () => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const { scrollTop, scrollHeight, clientHeight } = container;
    const atBottom = scrollTop + clientHeight >= scrollHeight - 10; // 10px threshold
    
    // Estimate hidden patients below viewport
    const cardHeight = 60; // Approximate height of each compact patient card
    const scrollRemaining = scrollHeight - (scrollTop + clientHeight);
    const estimatedHiddenCount = Math.max(0, Math.floor(scrollRemaining / cardHeight));
    
    setScrollInfo({ atBottom, hiddenCount: estimatedHiddenCount });
  };

  // Set up scroll listener
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    container.addEventListener('scroll', handleScroll);
    handleScroll(); // Initial check

    return () => {
      container.removeEventListener('scroll', handleScroll);
    };
  }, [patientsWithLocation.length]);

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header - Fixed Height */}
      <div className={`
        ${facilityInfo.color}
        border-2 rounded-t-lg p-2 flex-shrink-0 h-24
      `}>
        {/* Title row */}
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center space-x-2">
            <span className="text-xl">{facilityInfo.icon}</span>
            <div className="flex-1 min-w-0">
              <h3 className="font-bold text-base text-gray-800 truncate">
                {facilityInfo.displayName}
              </h3>
            </div>
          </div>
          
          {/* Cumulative counters - always visible */}
          <div className="flex space-x-1 text-xs">
            {name === 'POI' ? (
              // POI shows only KIA (gets all pre-Role1 deaths)
              <span className={`
                px-2 py-0.5 rounded-full font-bold text-xs min-w-[40px] text-center
                ${cumulativeCounts.kia > 0 
                  ? 'bg-red-200 text-red-900' 
                  : 'bg-gray-100 text-gray-500'
                }
              `}>
                ⚰️ {cumulativeCounts.kia}
              </span>
            ) : (
              // Other facilities show both KIA and RTD
              <>
                <span className={`
                  px-2 py-0.5 rounded-full font-bold text-xs min-w-[40px] text-center
                  ${cumulativeCounts.kia > 0 
                    ? 'bg-red-200 text-red-900' 
                    : 'bg-gray-100 text-gray-500'
                  }
                `}>
                  ⚰️ {cumulativeCounts.kia}
                </span>
                <span className={`
                  px-2 py-0.5 rounded-full font-bold text-xs min-w-[40px] text-center
                  ${cumulativeCounts.rtd > 0 
                    ? 'bg-green-200 text-green-900' 
                    : 'bg-gray-100 text-gray-500'
                  }
                `}>
                  ✅ {cumulativeCounts.rtd}
                </span>
              </>
            )}
          </div>
        </div>
        
        {/* Bottom row - current counts */}
        <div className="flex items-center justify-between">
          <p className="text-xs text-gray-600 truncate">{facilityInfo.description}</p>
          <div className="flex gap-1 text-xs">
            <span className="bg-white px-1.5 py-0.5 rounded font-medium">
              {patientsWithLocation.length}
            </span>
            {statusCounts.active > 0 && (
              <span className="bg-blue-100 text-blue-800 px-1 py-0.5 rounded">
                {statusCounts.active}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Patient list */}
      <div className="flex-1 border-l-2 border-r-2 border-gray-300 bg-white overflow-hidden relative">
        <div 
          ref={scrollContainerRef}
          className="h-full overflow-y-auto scrollbar-hide"
        >
          <div className="p-1">
            <AnimatePresence mode="popLayout">
              {patientsWithLocation.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="text-center text-gray-400 py-8"
                >
                  <div className="text-4xl mb-2">🏥</div>
                  <p className="text-sm">No patients</p>
                </motion.div>
              ) : (
                patientsWithLocation.map(({ patient, location }) => (
                  <PatientCard
                    key={patient.id.toString()}
                    patient={patient}
                    location={location}
                    layoutId={`patient-${patient.id.toString()}-${name}`}
                  />
                ))
              )}
            </AnimatePresence>
          </div>
        </div>
        
        {/* Bottom scroll indicator */}
        {!scrollInfo.atBottom && scrollInfo.hiddenCount > 0 && (
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-blue-100 to-transparent p-2">
            <div className="text-center">
              <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
                +{scrollInfo.hiddenCount} more below ↓
              </span>
            </div>
          </div>
        )}
      </div>
      
      {/* Bottom border */}
      <div className="border-b-2 border-gray-300 rounded-b-lg"></div>
    </div>
  );
};