import { useMemo } from 'react';
import { Patient } from '../types/patient.types';

export interface FilterState {
  searchQuery: string;
  nationality: string;
  triageCategory: string;
  injuryType: string;
  status: string;
  front: string;
}

interface FilterBarProps {
  patients: Patient[];
  filters: FilterState;
  onFilterChange: (filters: FilterState) => void;
  onClearFilters: () => void;
}

// Country code to flag emoji mapping
const getFlagEmoji = (countryCode: string): string => {
  const codePoints = countryCode
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
};

export function FilterBar({ patients, filters, onFilterChange, onClearFilters }: FilterBarProps) {
  // Extract unique values from patients for filter options
  const filterOptions = useMemo(() => {
    const nationalities = new Set<string>();
    const injuryTypes = new Set<string>();
    const fronts = new Set<string>();
    const triageCategories = new Set<string>();

    patients.forEach(patient => {
      if (patient.nationality) nationalities.add(patient.nationality);
      if (patient.injury_type) injuryTypes.add(patient.injury_type);
      if (patient.front) fronts.add(patient.front);
      if (patient.triage_category) triageCategories.add(patient.triage_category);
    });

    return {
      nationalities: Array.from(nationalities).sort(),
      injuryTypes: Array.from(injuryTypes).sort(),
      fronts: Array.from(fronts).sort(),
      triageCategories: Array.from(triageCategories).sort(),
    };
  }, [patients]);

  const hasActiveFilters =
    filters.searchQuery ||
    filters.nationality ||
    filters.triageCategory ||
    filters.injuryType ||
    filters.status ||
    filters.front;

  const handleChange = (key: keyof FilterState, value: string) => {
    onFilterChange({ ...filters, [key]: value });
  };

  return (
    <div className="bg-white border-b border-gray-200 p-3">
      <div className="flex flex-wrap items-center gap-3">
        {/* Search input */}
        <div className="flex-1 min-w-[200px] max-w-[300px]">
          <input
            type="text"
            placeholder="Search by ID or name..."
            value={filters.searchQuery}
            onChange={(e) => handleChange('searchQuery', e.target.value)}
            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Nationality filter */}
        <div className="flex items-center gap-1">
          <label className="text-xs text-gray-500 font-medium">Nation:</label>
          <select
            value={filters.nationality}
            onChange={(e) => handleChange('nationality', e.target.value)}
            className="px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All</option>
            {filterOptions.nationalities.map(nat => (
              <option key={nat} value={nat}>
                {getFlagEmoji(nat)} {nat}
              </option>
            ))}
          </select>
        </div>

        {/* Triage filter */}
        <div className="flex items-center gap-1">
          <label className="text-xs text-gray-500 font-medium">Triage:</label>
          <select
            value={filters.triageCategory}
            onChange={(e) => handleChange('triageCategory', e.target.value)}
            className="px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All</option>
            <option value="T1" className="text-red-600">T1 - Immediate</option>
            <option value="T2" className="text-yellow-600">T2 - Delayed</option>
            <option value="T3" className="text-green-600">T3 - Minimal</option>
          </select>
        </div>

        {/* Injury Type filter */}
        <div className="flex items-center gap-1">
          <label className="text-xs text-gray-500 font-medium">Injury:</label>
          <select
            value={filters.injuryType}
            onChange={(e) => handleChange('injuryType', e.target.value)}
            className="px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All</option>
            {filterOptions.injuryTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        {/* Status filter */}
        <div className="flex items-center gap-1">
          <label className="text-xs text-gray-500 font-medium">Status:</label>
          <select
            value={filters.status}
            onChange={(e) => handleChange('status', e.target.value)}
            className="px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All</option>
            <option value="active" className="text-blue-600">Active</option>
            <option value="KIA" className="text-red-600">KIA</option>
            <option value="RTD" className="text-green-600">RTD</option>
          </select>
        </div>

        {/* Front filter (if available) */}
        {filterOptions.fronts.length > 0 && (
          <div className="flex items-center gap-1">
            <label className="text-xs text-gray-500 font-medium">Front:</label>
            <select
              value={filters.front}
              onChange={(e) => handleChange('front', e.target.value)}
              className="px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All</option>
              {filterOptions.fronts.map(front => (
                <option key={front} value={front}>{front}</option>
              ))}
            </select>
          </div>
        )}

        {/* Clear filters button */}
        {hasActiveFilters && (
          <button
            onClick={onClearFilters}
            className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
          >
            Clear Filters
          </button>
        )}
      </div>
    </div>
  );
}

// Filter function to apply filters to patients
export function filterPatients(
  patients: Patient[],
  filters: FilterState,
  currentTime: Date
): Patient[] {
  return patients.filter(patient => {
    // Search query filter
    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase();
      const patientId = String(patient.id).toLowerCase();
      const givenName = (patient.given_name || '').toLowerCase();
      const familyName = (patient.family_name || '').toLowerCase();
      const demoName = patient.demographics?.name?.toLowerCase() || '';

      if (!patientId.includes(query) &&
          !givenName.includes(query) &&
          !familyName.includes(query) &&
          !demoName.includes(query)) {
        return false;
      }
    }

    // Nationality filter
    if (filters.nationality && patient.nationality !== filters.nationality) {
      return false;
    }

    // Triage category filter
    if (filters.triageCategory && patient.triage_category !== filters.triageCategory) {
      return false;
    }

    // Injury type filter
    if (filters.injuryType && patient.injury_type !== filters.injuryType) {
      return false;
    }

    // Front filter
    if (filters.front && patient.front !== filters.front) {
      return false;
    }

    // Status filter (requires checking timeline events)
    if (filters.status) {
      const injuryTime = patient.injury_timestamp
        ? new Date(patient.injury_timestamp)
        : new Date('2024-01-01T00:00:00Z');
      const currentHours = (currentTime.getTime() - injuryTime.getTime()) / (1000 * 60 * 60);

      if (patient.movement_timeline) {
        const eventsSoFar = patient.movement_timeline.filter(
          event => event.hours_since_injury <= currentHours
        );
        const isKIA = eventsSoFar.some(event => event.event_type === 'kia');
        const isRTD = eventsSoFar.some(event => event.event_type === 'rtd');

        if (filters.status === 'KIA' && !isKIA) return false;
        if (filters.status === 'RTD' && !isRTD) return false;
        if (filters.status === 'active' && (isKIA || isRTD)) return false;
      }
    }

    return true;
  });
}

export const initialFilterState: FilterState = {
  searchQuery: '',
  nationality: '',
  triageCategory: '',
  injuryType: '',
  status: '',
  front: '',
};
