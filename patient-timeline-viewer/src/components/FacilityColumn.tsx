import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Patient, FacilityName } from '../types/patient.types';
import { PatientCard } from './PatientCard';
import { getPatientLocationAtTime } from '../utils/timelineEngine';

interface FacilityColumnProps {
  name: FacilityName;
  patients: Patient[];
  currentTime: Date;
  className?: string;
}

export const FacilityColumn: React.FC<FacilityColumnProps> = ({ 
  name, 
  patients, 
  currentTime,
  className = '' 
}) => {
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
          displayName: 'Role 1 Medical',
          icon: '🏕️',
          color: 'border-orange-400 bg-orange-50',
          description: 'Forward medical care'
        };
      case 'Role2':
        return {
          displayName: 'Role 2 Medical',
          icon: '🏥',
          color: 'border-blue-400 bg-blue-50',
          description: 'Field hospital'
        };
      case 'Role3':
        return {
          displayName: 'Role 3 Medical',
          icon: '🏢',
          color: 'border-purple-400 bg-purple-50',
          description: 'Combat support hospital'
        };
      case 'Role4':
        return {
          displayName: 'Role 4 Medical',
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

  // Filter and get location info for each patient
  const patientsWithLocation = patients.map(patient => ({
    patient,
    location: getPatientLocationAtTime(patient, currentTime)
  })).filter(({ location }) => location.facility === name);

  // Count patients by status
  const statusCounts = patientsWithLocation.reduce((acc, { location }) => {
    acc[location.status] = (acc[location.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className={`
        ${facilityInfo.color}
        border-2 rounded-t-lg p-4 flex-shrink-0
      `}>
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-2xl">{facilityInfo.icon}</span>
          <div>
            <h3 className="font-bold text-lg text-gray-800">
              {facilityInfo.displayName}
            </h3>
            <p className="text-sm text-gray-600">{facilityInfo.description}</p>
          </div>
        </div>

        {/* Patient count and status summary */}
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="bg-white px-2 py-1 rounded-full font-medium">
            Total: {patientsWithLocation.length}
          </span>
          {statusCounts.active > 0 && (
            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
              Active: {statusCounts.active}
            </span>
          )}
          {statusCounts.kia > 0 && (
            <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full">
              KIA: {statusCounts.kia}
            </span>
          )}
          {statusCounts.rtd > 0 && (
            <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full">
              RTD: {statusCounts.rtd}
            </span>
          )}
        </div>
      </div>

      {/* Patient list */}
      <div className="flex-1 border-l-2 border-r-2 border-b-2 border-gray-300 rounded-b-lg bg-white overflow-y-auto">
        <div className="p-2">
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
                  key={patient.id}
                  patient={patient}
                  location={location}
                  layoutId={`patient-${patient.id}-${name}`}
                />
              ))
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};