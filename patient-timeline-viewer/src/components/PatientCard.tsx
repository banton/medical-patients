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
      layoutId={layoutId || `patient-${patient.id.toString()}`}
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
        border rounded p-1.5 mb-1 shadow-sm hover:shadow-md
        transition-shadow duration-200 cursor-pointer
        min-w-0 relative
      `}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {/* Header row with status and triage */}
      <div className="flex items-center justify-between mb-0.5">
        <div className="flex items-center space-x-1">
          <span className="text-sm">{styles.icon}</span>
          <span className="text-xs font-medium">{styles.statusText}</span>
        </div>
        
        {/* Triage category */}
        <div className={`
          ${getTriageColor(patient.triage_category)}
          text-white text-xs font-bold px-1 py-0.5 rounded-full
          min-w-[18px] text-center
        `}>
          {patient.triage_category}
        </div>
      </div>

      {/* Patient name and nationality */}
      <div className="font-medium text-sm mb-0.5 truncate">
        {(() => {
          const firstName = patient.demographics?.given_name || patient.given_name || '';
          const lastName = patient.demographics?.family_name || patient.family_name || '';
          const nationality = patient.nationality || patient.demographics?.nationality || '';
          
          if (firstName && lastName) {
            return `${firstName.charAt(0)}. ${lastName}, ${nationality}`;
          }
          return `ID: ${patient.id}, ${nationality}`;
        })()}
      </div>

      {/* Activity and Front info */}
      <div className="flex items-center justify-between text-xs opacity-75">
        <span className="truncate">
          {location.eventType && location.eventType !== 'active' 
            ? location.eventType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
            : 'Active'
          }
        </span>
        {patient.front && (
          <span className="text-xs opacity-60 ml-1 truncate">
            {patient.front}
          </span>
        )}
      </div>

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