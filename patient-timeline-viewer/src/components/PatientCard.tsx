import React from 'react';
import { motion } from 'framer-motion';
import { Patient, PatientLocation } from '../types/patient.types';

interface PatientCardProps {
  patient: Patient;
  location: PatientLocation;
  layoutId?: string;
}

export const PatientCard: React.FC<PatientCardProps> = ({ 
  patient, 
  location,
  layoutId 
}) => {
  // Determine card styling based on status
  const getCardStyles = () => {
    switch (location.status) {
      case 'kia':
        return {
          bg: 'bg-red-100 border-red-300',
          text: 'text-red-800',
          icon: '💀',
          statusText: 'KIA'
        };
      case 'rtd':
        return {
          bg: 'bg-green-100 border-green-300',
          text: 'text-green-800',
          icon: '✅',
          statusText: 'RTD'
        };
      case 'transit':
        return {
          bg: 'bg-yellow-100 border-yellow-300',
          text: 'text-yellow-800',
          icon: '🚁',
          statusText: 'Transit'
        };
      default:
        return {
          bg: 'bg-white border-gray-300',
          text: 'text-gray-800',
          icon: '🏥',
          statusText: 'Active'
        };
    }
  };

  // Get triage color
  const getTriageColor = (triage: string) => {
    switch (triage) {
      case 'T1':
        return 'bg-red-500';
      case 'T2':
        return 'bg-yellow-500';
      case 'T3':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  const styles = getCardStyles();

  return (
    <motion.div
      layoutId={layoutId || `patient-${patient.id}`}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 25,
        layout: {
          type: "spring",
          stiffness: 400,
          damping: 30
        }
      }}
      className={`
        ${styles.bg} ${styles.text}
        border-2 rounded-lg p-3 m-1 shadow-sm hover:shadow-md
        transition-shadow duration-200 cursor-pointer
        min-w-0 relative
      `}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {/* Status indicator */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-1">
          <span className="text-sm">{styles.icon}</span>
          <span className="text-xs font-medium">{styles.statusText}</span>
        </div>
        
        {/* Triage category */}
        <div className={`
          ${getTriageColor(patient.triage_category)}
          text-white text-xs font-bold px-2 py-1 rounded-full
          min-w-[24px] text-center
        `}>
          {patient.triage_category}
        </div>
      </div>

      {/* Patient ID */}
      <div className="font-medium text-sm mb-1 truncate">
        ID: {patient.id}
      </div>

      {/* Nationality */}
      <div className="text-xs opacity-75 mb-1">
        {patient.nationality}
      </div>

      {/* Injury type if available */}
      {patient.injury_type && (
        <div className="text-xs opacity-60 truncate">
          {patient.injury_type}
        </div>
      )}

      {/* Event type indicator */}
      {location.eventType && location.eventType !== 'active' && (
        <div className="text-xs mt-1 font-medium capitalize">
          {location.eventType.replace('_', ' ')}
        </div>
      )}

      {/* Animation for transit status */}
      {location.status === 'transit' && (
        <motion.div
          className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [1, 0.7, 1]
          }}
          transition={{
            duration: 1,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      )}

      {/* Animation for KIA status */}
      {location.status === 'kia' && (
        <motion.div
          className="absolute inset-0 border-2 border-red-500 rounded-lg pointer-events-none"
          animate={{
            opacity: [0.3, 0.7, 0.3]
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      )}

      {/* Animation for RTD status */}
      {location.status === 'rtd' && (
        <motion.div
          className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full"
          animate={{
            scale: [1, 1.3, 1],
            opacity: [1, 0.5, 1]
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      )}
    </motion.div>
  );
};