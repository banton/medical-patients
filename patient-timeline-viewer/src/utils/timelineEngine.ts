import { Patient, TimelineEvent, PatientLocation, FacilityName } from '../types/patient.types';

export function getPatientLocationAtTime(patient: Patient, currentTime: Date): PatientLocation {
  if (!patient.movement_timeline || patient.movement_timeline.length === 0) {
    return { facility: 'POI', status: 'active' };
  }

  // Convert current time to hours since injury for comparison
  // Support both injury_timestamp and injury_time fields (generator uses injury_time)
  const injuryTimeStr = patient.injury_timestamp || (patient as any).injury_time;
  const injuryTime = injuryTimeStr ? new Date(injuryTimeStr) : new Date('2024-01-01T00:00:00Z');
  const currentHours = (currentTime.getTime() - injuryTime.getTime()) / (1000 * 60 * 60);

  // Check if injury has happened yet - if not, patient doesn't exist yet
  if (currentHours < 0) {
    return { facility: 'POI', status: 'hidden' };
  }

  // Sort timeline events by hours_since_injury
  const sortedEvents = [...patient.movement_timeline].sort((a, b) => a.hours_since_injury - b.hours_since_injury);

  // Find the most recent event before or at current time
  let activeEvent: TimelineEvent | null = null;
  let nextEvent: TimelineEvent | null = null;

  for (let i = 0; i < sortedEvents.length; i++) {
    const event = sortedEvents[i];
    if (event.hours_since_injury <= currentHours) {
      activeEvent = event;
      nextEvent = sortedEvents[i + 1] || null;
    } else {
      break;
    }
  }

  // If no events have occurred yet (but injury has happened), patient is at POI
  if (!activeEvent) {
    return { facility: 'POI', status: 'active' };
  }

  // Check for terminal events (KIA, RTD) - hide after 15 minutes (0.25 hours)
  if (activeEvent.event_type === 'kia') {
    const timeFromEvent = currentHours - activeEvent.hours_since_injury;
    if (timeFromEvent >= 0.25) { // 15 minutes in hours
      return { 
        facility: activeEvent.facility as FacilityName || 'POI', 
        status: 'hidden',
        eventType: activeEvent.event_type 
      };
    }
    return { 
      facility: activeEvent.facility as FacilityName || 'POI', 
      status: 'kia',
      eventType: activeEvent.event_type 
    };
  }

  if (activeEvent.event_type === 'rtd') {
    const timeFromEvent = currentHours - activeEvent.hours_since_injury;
    if (timeFromEvent >= 0.25) { // 15 minutes in hours
      return { 
        facility: activeEvent.facility as FacilityName || 'POI', 
        status: 'hidden',
        eventType: activeEvent.event_type 
      };
    }
    return { 
      facility: activeEvent.facility as FacilityName || 'POI', 
      status: 'rtd',
      eventType: activeEvent.event_type 
    };
  }

  // Handle different event types
  switch (activeEvent.event_type) {
    case 'arrival':
      // If the next event is a transit_start the patient is waiting for evacuation
      if (nextEvent && nextEvent.event_type === 'transit_start') {
        return {
          facility: activeEvent.facility as FacilityName || 'POI',
          status: 'waiting' as any,
          eventType: 'awaiting_transport'
        };
      }
      return {
        facility: activeEvent.facility as FacilityName || 'POI',
        status: 'active',
        eventType: activeEvent.event_type
      };

    case 'evacuation_start':
      // Check if patient is still evacuating or has moved to next phase
      const evacuationEndHours = activeEvent.hours_since_injury + (activeEvent.evacuation_duration_hours || 0);
      
      if (currentHours < evacuationEndHours) {
        // Still evacuating
        return { 
          facility: activeEvent.facility as FacilityName || 'POI', 
          status: 'active',
          eventType: 'evacuating' 
        };
      } else {
        // Evacuation completed, check next event
        if (nextEvent && nextEvent.event_type === 'transit_start') {
          return { 
            facility: activeEvent.facility as FacilityName || 'POI', 
            status: 'active',
            eventType: 'evacuation_complete' 
          };
        }
        return { 
          facility: activeEvent.facility as FacilityName || 'POI', 
          status: 'active',
          eventType: 'evacuation_complete' 
        };
      }

    case 'transit_start':
      // Check if patient is still in transit
      const transitEndHours = activeEvent.hours_since_injury + (activeEvent.transit_duration_hours || 0);
      
      if (currentHours < transitEndHours) {
        // Still in transit
        return { 
          facility: null, 
          status: 'transit',
          eventType: 'in_transit' 
        };
      } else {
        // Transit completed, patient should be at destination
        const destination = activeEvent.to_facility as FacilityName || 'Role1';
        return { 
          facility: destination, 
          status: 'active',
          eventType: 'transit_complete' 
        };
      }

    default:
      return { 
        facility: activeEvent.facility as FacilityName || 'POI', 
        status: 'active',
        eventType: activeEvent.event_type 
      };
  }
}

export function getTimelineExtent(patients: Patient[]): { start: Date; end: Date } {
  if (patients.length === 0) {
    const defaultStart = new Date('2024-01-01T00:00:00Z');
    return { 
      start: defaultStart, 
      end: new Date(defaultStart.getTime() + 24 * 60 * 60 * 1000) // 24 hours later
    };
  }

  let earliestTime = new Date('2099-12-31T23:59:59Z'); // Start with far future date
  let latestTime = new Date(0);

  patients.forEach(patient => {
    // Find injury timestamp - support both injury_timestamp and injury_time fields
    const injuryTimeStr = patient.injury_timestamp || (patient as any).injury_time;
    const injuryTime = injuryTimeStr ? new Date(injuryTimeStr) : new Date('2024-01-01T00:00:00Z');
    
    if (injuryTime < earliestTime) {
      earliestTime = injuryTime;
    }

    // Find the latest event time
    patient.movement_timeline.forEach(event => {
      const eventTime = new Date(injuryTime.getTime() + event.hours_since_injury * 60 * 60 * 1000);
      if (eventTime > latestTime) {
        latestTime = eventTime;
      }
    });
  });

  // Add some padding to the end time
  latestTime = new Date(latestTime.getTime() + 6 * 60 * 60 * 1000); // 6 hours padding

  return { start: earliestTime, end: latestTime };
}

export function formatTimeDisplay(date: Date): string {
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
}

export function calculateHoursSinceInjury(currentTime: Date, injuryTime: Date): number {
  return (currentTime.getTime() - injuryTime.getTime()) / (1000 * 60 * 60);
}

export function formatElapsedTime(totalHours: number): string {
  const days = Math.floor(totalHours / 24);
  const hours = Math.floor(totalHours % 24);
  
  if (days === 0) {
    return `${totalHours.toFixed(1)} hours elapsed`;
  } else {
    return `${totalHours.toFixed(1)} hours elapsed (${days} day${days !== 1 ? 's' : ''}, ${hours} hour${hours !== 1 ? 's' : ''})`;
  }
}