export interface TimelineEvent {
  event_type: 'arrival' | 'evacuation_start' | 'transit_start' | 'kia' | 'rtd' | 'remains_role4';
  facility?: string;
  timestamp: string;
  hours_since_injury: number;
  
  // Optional additional data based on event type
  evacuation_duration_hours?: number;
  transit_duration_hours?: number;
  from_facility?: string;
  to_facility?: string;
  triage_category?: string;
  kia_timing?: string;
  rtd_timing?: string;
  evacuation_hours_completed?: number;
  transit_hours_completed?: number;
  destination_facility?: string;
}

export interface Patient {
  id: string | number;
  nationality: string;
  gender?: string;
  injury_type?: string;
  triage_category: 'T1' | 'T2' | 'T3';
  day_of_injury?: string;
  last_facility: string;
  final_status: 'KIA' | 'RTD' | 'Remains_Role4';
  movement_timeline: TimelineEvent[];
  injury_timestamp?: string;
  current_status?: string;
  
  // Name fields (can be at top level or in demographics)
  given_name?: string;
  family_name?: string;
  
  // Additional fields that might be present in generator output
  demographics?: any;
  medical_data?: any;
  treatment_history?: any;
  front?: string;
  primary_condition?: any;
  primary_conditions?: any;
  additional_conditions?: any;
  timeline_summary?: any;
}

export type FacilityName = 'POI' | 'Role1' | 'Role2' | 'Role3' | 'Role4';

export interface PatientLocation {
  facility: FacilityName | null;
  status: 'active' | 'kia' | 'rtd' | 'transit' | 'completed' | 'hidden';
  eventType?: string;
}

export interface PlaybackState {
  isPlaying: boolean;
  currentTime: Date;
  speed: number;
  startTime: Date;
  endTime: Date;
}

export interface PatientsByFacility {
  POI: Patient[];
  Role1: Patient[];
  Role2: Patient[];
  Role3: Patient[];
  Role4: Patient[];
}