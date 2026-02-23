from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import random
from typing import Dict, List, Optional, Tuple
import uuid


@dataclass
class CasualtyEvent:
    """Represents a single casualty or mass casualty event"""

    timestamp: datetime
    patient_count: int
    warfare_type: str
    is_mass_casualty: bool
    event_id: str
    environmental_factors: List[str] = field(default_factory=list)
    special_event_type: Optional[str] = None


class TemporalPatternGenerator:
    """Generates temporal distribution patterns for casualties"""

    def __init__(self, warfare_patterns_path: str):
        """Initialize with warfare patterns configuration"""
        with open(warfare_patterns_path) as f:
            self.warfare_patterns = json.load(f)

        self.hourly_baseline = self.warfare_patterns["hourly_activity_baseline"]

    def generate_timeline(
        self,
        days: int,
        total_patients: int,
        active_warfare_types: Dict[str, bool],
        intensity: str,
        tempo: str,
        environmental_conditions: Dict[str, bool],
        special_events: Dict[str, bool],
        base_date: str,
    ) -> List[CasualtyEvent]:
        """Generate a complete timeline of casualty events"""

        # Parse base date
        base_datetime = datetime.strptime(base_date, "%Y-%m-%d")

        # Get active warfare types and their weights
        active_types = [wtype for wtype, active in active_warfare_types.items() if active]
        if not active_types:
            msg = "No active warfare types selected"
            raise ValueError(msg)

        # Calculate warfare weights
        warfare_weights = self._calculate_warfare_weights(active_types)

        # Get intensity and tempo modifiers
        intensity_mod = self.warfare_patterns["intensity_levels"][intensity]
        tempo_pattern = self.warfare_patterns["tempo_patterns"][tempo]

        # Use exact requested patient count - don't apply multiplier
        # The intensity should affect distribution/severity, not total count
        adjusted_total = total_patients

        # Distribute patients across days based on tempo
        daily_distribution = self._distribute_patients_by_day(adjusted_total, days, tempo_pattern["daily_intensity"])

        # Generate events for each day
        all_events = []

        for day in range(days):
            day_patients = daily_distribution[day]
            day_datetime = base_datetime + timedelta(days=day)

            # Check for special events on this day
            day_special_events = self._get_special_events_for_day(day + 1, special_events, day_patients, base_date)

            # Distribute patients among warfare types for this day
            warfare_distribution = self._distribute_patients_by_warfare(
                day_patients, warfare_weights, day_special_events
            )

            # Generate hourly events for each warfare type
            for warfare_type, type_patients in warfare_distribution.items():
                if type_patients > 0:
                    events = self._generate_warfare_type_events(
                        warfare_type, type_patients, day, day_datetime, environmental_conditions, intensity_mod
                    )
                    all_events.extend(events)

            # Add special events
            all_events.extend(day_special_events)

        # Apply environmental modifiers to all events
        all_events = self._apply_environmental_modifiers(all_events, environmental_conditions)

        # Sort events by timestamp
        all_events.sort(key=lambda e: e.timestamp)

        # Validate total patient count
        total_generated = sum(e.patient_count for e in all_events)
        if total_generated != adjusted_total:
            # Adjust last event to match exactly
            difference = adjusted_total - total_generated
            if all_events and difference != 0:
                all_events[-1].patient_count += difference

        return all_events

    def _calculate_warfare_weights(self, active_types: List[str]) -> Dict[str, float]:
        """Calculate normalized weights for active warfare types"""
        weights = {}
        total_weight = 0

        for wtype in active_types:
            multiplier = self.warfare_patterns["warfare_types"][wtype]["weight_multiplier"]
            weights[wtype] = multiplier
            total_weight += multiplier

        # Normalize
        if total_weight > 0:
            for wtype in weights:
                weights[wtype] /= total_weight

        return weights

    def _distribute_patients_by_day(self, total: int, days: int, daily_intensity: List[float]) -> List[int]:
        """Distribute patients across days based on tempo pattern"""
        # Ensure we have intensity values for all days
        if len(daily_intensity) < days:
            # Repeat last value for additional days
            daily_intensity = daily_intensity + [daily_intensity[-1]] * (days - len(daily_intensity))

        # Calculate raw distribution
        total_intensity = sum(daily_intensity[:days])
        daily_patients = []

        for i in range(days):
            patients = int(total * daily_intensity[i] / total_intensity)
            daily_patients.append(patients)

        # Adjust for rounding errors
        difference = total - sum(daily_patients)
        if difference > 0:
            # Add to highest intensity days
            for _ in range(difference):
                max_day = daily_intensity[:days].index(max(daily_intensity[:days]))
                daily_patients[max_day] += 1
                daily_intensity[max_day] *= 0.99  # Slightly reduce to spread

        return daily_patients

    def _distribute_patients_by_warfare(
        self, day_patients: int, warfare_weights: Dict[str, float], special_events: List[CasualtyEvent]
    ) -> Dict[str, int]:
        """Distribute patients among warfare types for a day"""
        # Reserve patients for special events
        special_event_patients = sum(e.patient_count for e in special_events)
        remaining_patients = day_patients - special_event_patients

        distribution = {}
        allocated = 0

        # Sort by weight to allocate larger portions first
        sorted_types = sorted(warfare_weights.items(), key=lambda x: x[1], reverse=True)

        for i, (wtype, weight) in enumerate(sorted_types):
            if i == len(sorted_types) - 1:
                # Last type gets all remaining
                patients = remaining_patients - allocated
            else:
                patients = int(remaining_patients * weight)

            distribution[wtype] = patients
            allocated += patients

        return distribution

    def _generate_warfare_type_events(
        self,
        warfare_type: str,
        total_patients: int,
        day: int,
        day_datetime: datetime,
        environmental_conditions: Dict[str, bool],
        intensity_mod: Dict,
    ) -> List[CasualtyEvent]:
        """Generate casualty events for a specific warfare type on a day"""
        warfare_config = self.warfare_patterns["warfare_types"][warfare_type]
        pattern_type = warfare_config["temporal_pattern"]["type"]

        # Generate hourly distribution based on pattern type
        if pattern_type == "sustained_combat":
            hourly_distribution = self._generate_sustained_pattern(total_patients, warfare_config["temporal_pattern"])
        elif pattern_type == "surge":
            hourly_distribution = self._generate_surge_pattern(total_patients, day, warfare_config["temporal_pattern"])
        elif pattern_type == "sporadic":
            hourly_distribution = self._generate_sporadic_pattern(total_patients, warfare_config["temporal_pattern"])
        elif pattern_type == "precision_strike":
            hourly_distribution = self._generate_precision_strike_pattern(
                total_patients, warfare_config["temporal_pattern"]
            )
        elif pattern_type == "phased_assault":
            hourly_distribution = self._generate_phased_assault_pattern(
                total_patients, warfare_config["temporal_pattern"]
            )
        else:
            # Default to even distribution
            hourly_distribution = [(h, total_patients // 24) for h in range(24)]

        # Generate actual events from hourly distribution
        events = []
        active_env = [env for env, active in environmental_conditions.items() if active]

        for hour, hour_patients in hourly_distribution:
            if hour_patients > 0:
                hour_events = self._generate_hour_events(
                    warfare_type,
                    hour_patients,
                    day,
                    hour,
                    day_datetime,
                    warfare_config["casualty_clustering"],
                    active_env,
                    intensity_mod,
                )
                events.extend(hour_events)

        return events

    def _generate_sustained_pattern(self, total_patients: int, params: Dict) -> List[Tuple[int, int]]:
        """Generate sustained combat pattern (conventional warfare)"""
        hourly_casualties = []
        peak_hours = params["peak_hours"]
        peak_intensity = params["peak_intensity"]
        base_intensity = params["base_intensity"]
        night_reduction = params["night_reduction"]

        # Calculate base hourly rate
        total_weight = 0
        hourly_weights = []

        for hour in range(24):
            if hour in peak_hours:
                weight = peak_intensity * self.hourly_baseline[hour]
            elif hour in range(6) or hour in range(22, 24):
                # Further reduce early morning hours to avoid clustering
                reduction_factor = 0.5 if hour == 0 else 0.7
                weight = base_intensity * night_reduction * self.hourly_baseline[hour] * reduction_factor
            else:
                weight = base_intensity * self.hourly_baseline[hour]

            hourly_weights.append(weight)
            total_weight += weight

        # Distribute patients more evenly
        if total_weight == 0:
            # Fallback: distribute evenly
            patients_per_hour = total_patients // 24
            remainder = total_patients % 24
            for hour in range(24):
                patients = patients_per_hour + (1 if hour < remainder else 0)
                hourly_casualties.append((hour, patients))
        else:
            allocated = 0
            for hour in range(24):
                weight = hourly_weights[hour]

                if hour == 23:  # Last hour gets remainder
                    patients = total_patients - allocated
                else:
                    # Use rounding instead of int() for better distribution
                    patients = round(total_patients * weight / total_weight)

                # Ensure we don't over-allocate
                patients = max(0, min(patients, total_patients - allocated))

                hourly_casualties.append((hour, patients))
                allocated += patients

        return hourly_casualties

    def _generate_surge_pattern(self, total_patients: int, day: int, params: Dict) -> List[Tuple[int, int]]:
        """Generate surge pattern (artillery)"""
        surges_per_day = params["surges_per_day"]
        surge_duration = params["surge_duration_hours"]
        surge_intensity = params["surge_intensity"]
        between_surge = params["between_surge_intensity"]
        preferred_hours = params["preferred_hours"]

        # Randomly select surge start times
        surge_starts = []
        available_hours = preferred_hours.copy()

        for _ in range(min(surges_per_day, len(available_hours))):
            if available_hours:
                start = random.choice(available_hours)
                surge_starts.append(start)
                # Remove this hour and nearby hours to prevent overlap
                available_hours = [h for h in available_hours if abs(h - start) > surge_duration]

        # Build surge hours set
        surge_hours = set()
        for start in surge_starts:
            for h in range(surge_duration):
                hour = (start + h) % 24
                surge_hours.add(hour)

        # Allocate 80% of casualties to surge hours
        surge_casualties = int(total_patients * 0.8)
        non_surge_casualties = total_patients - surge_casualties

        # Distribute casualties
        hourly_casualties = []

        for hour in range(24):
            if hour in surge_hours:
                # High intensity during surge
                base_rate = surge_casualties / len(surge_hours)
                patients = int(base_rate * surge_intensity * random.uniform(0.8, 1.2))
            # Low intensity between surges
            elif 24 - len(surge_hours) > 0:
                base_rate = non_surge_casualties / (24 - len(surge_hours))
                patients = int(base_rate * between_surge * random.uniform(0.5, 1.5))
            else:
                patients = 0

            hourly_casualties.append((hour, patients))

        # Adjust for total
        self._adjust_hourly_total(hourly_casualties, total_patients)

        # Validate distribution to avoid hour 0 clustering
        return self._validate_hourly_distribution(hourly_casualties, total_patients)

    def _generate_sporadic_pattern(self, total_patients: int, params: Dict) -> List[Tuple[int, int]]:
        """Generate sporadic pattern (guerrilla warfare)"""
        events_range = params["events_per_day_range"]
        dawn_dusk_pref = params["dawn_dusk_preference"]
        night_activity = params["night_activity_level"]

        # Determine number of events
        num_events = random.randint(*events_range)

        # Create weight map for hours
        hour_weights = []
        dawn_hours = [5, 6, 7]
        dusk_hours = [17, 18, 19]
        night_hours = list(range(6)) + list(range(20, 24))

        for hour in range(24):
            if hour in dawn_hours or hour in dusk_hours:
                weight = self.hourly_baseline[hour] * dawn_dusk_pref
            elif hour in night_hours:
                weight = self.hourly_baseline[hour] * night_activity
            else:
                weight = self.hourly_baseline[hour]

            hour_weights.append(weight)

        # Randomly select event hours
        event_hours = []
        total_weight = sum(hour_weights)

        for _ in range(num_events):
            r = random.uniform(0, total_weight)
            cumulative = 0
            for hour, weight in enumerate(hour_weights):
                cumulative += weight
                if r <= cumulative:
                    event_hours.append(hour)
                    break

        # Distribute patients among events
        hourly_casualties = [0] * 24
        patients_per_event = total_patients // num_events
        remainder = total_patients % num_events

        for i, hour in enumerate(event_hours):
            patients = patients_per_event
            if i < remainder:
                patients += 1
            hourly_casualties[hour] += patients

        return [(h, p) for h, p in enumerate(hourly_casualties)]

    def _generate_precision_strike_pattern(self, total_patients: int, params: Dict) -> List[Tuple[int, int]]:
        """Generate precision strike pattern (drone warfare)"""
        strikes_range = params["strikes_per_day_range"]
        preference = params["strike_window_preference"]
        randomization = params["time_randomization"]

        # Determine number of strikes
        num_strikes = random.randint(*strikes_range)

        # Define preferred hours based on preference
        if preference == "daylight":
            preferred_hours = list(range(6, 18))
        elif preference == "night":
            preferred_hours = list(range(6)) + list(range(18, 24))
        else:
            preferred_hours = list(range(24))

        # Select strike hours with randomization
        strike_hours = []
        for _ in range(num_strikes):
            if random.random() < randomization:
                # Random hour
                hour = random.randint(0, 23)
            else:
                # Preferred hour
                hour = random.choice(preferred_hours)
            strike_hours.append(hour)

        # Distribute patients
        hourly_casualties = [0] * 24
        patients_per_strike = total_patients // num_strikes
        remainder = total_patients % num_strikes

        for i, hour in enumerate(strike_hours):
            patients = patients_per_strike
            if i < remainder:
                patients += 1
            hourly_casualties[hour] += patients

        return [(h, p) for h, p in enumerate(hourly_casualties)]

    def _generate_phased_assault_pattern(self, total_patients: int, params: Dict) -> List[Tuple[int, int]]:
        """Generate phased assault pattern (urban warfare)"""
        phases = params["assault_phases"]
        baseline = params["baseline_intensity"]

        # Calculate total weight
        total_weight = 0
        phase_hours = set()

        for phase in phases:
            for h in range(phase["duration"]):
                hour = (phase["start_hour"] + h) % 24
                phase_hours.add(hour)
                total_weight += phase["intensity"] * self.hourly_baseline[hour]

        # Add baseline for non-phase hours
        for hour in range(24):
            if hour not in phase_hours:
                total_weight += baseline * self.hourly_baseline[hour]

        # Distribute patients
        hourly_casualties = []
        allocated = 0

        for hour in range(24):
            # Check if hour is in a phase
            in_phase = False
            for phase in phases:
                phase_start = phase["start_hour"]
                phase_end = (phase_start + phase["duration"]) % 24

                if phase_start <= phase_end:
                    if phase_start <= hour < phase_end:
                        in_phase = True
                        intensity = phase["intensity"]
                        break
                elif hour >= phase_start or hour < phase_end:
                    in_phase = True
                    intensity = phase["intensity"]
                    break

            if not in_phase:
                intensity = baseline

            weight = intensity * self.hourly_baseline[hour]
            if hour == 23:  # Last hour
                patients = total_patients - allocated
            else:
                patients = int(total_patients * weight / total_weight)

            hourly_casualties.append((hour, patients))
            allocated += patients

        return hourly_casualties

    def _generate_hour_events(
        self,
        warfare_type: str,
        hour_patients: int,
        day: int,
        hour: int,
        day_datetime: datetime,
        clustering_params: Dict,
        environmental_factors: List[str],
        intensity_mod: Dict,
    ) -> List[CasualtyEvent]:
        """Generate specific casualty events for an hour"""
        events = []
        remaining_patients = hour_patients

        # Check for mass casualty event
        mass_casualty_prob = clustering_params["mass_casualty_probability"]
        mass_casualty_prob *= intensity_mod.get("mass_casualty_reduction", 1.0)

        if random.random() < mass_casualty_prob and remaining_patients > 5:
            # Generate mass casualty event
            size_range = clustering_params["cluster_size_range"]
            size = random.randint(*size_range)
            size = min(size, remaining_patients)

            # Random minute within the hour
            minute = random.randint(0, 59)
            timestamp = day_datetime + timedelta(hours=hour, minutes=minute)

            event = CasualtyEvent(
                timestamp=timestamp,
                patient_count=size,
                warfare_type=warfare_type,
                is_mass_casualty=True,
                event_id=f"MC_{warfare_type}_{day}_{hour}_{minute}_{uuid.uuid4().hex[:8]}",
                environmental_factors=environmental_factors,
            )
            events.append(event)
            remaining_patients -= size

        # Distribute remaining as individual or small group casualties
        while remaining_patients > 0:
            # Small groups of 1-3
            group_size = min(random.randint(1, 3), remaining_patients)

            # Random minute
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            timestamp = day_datetime + timedelta(hours=hour, minutes=minute, seconds=second)

            event = CasualtyEvent(
                timestamp=timestamp,
                patient_count=group_size,
                warfare_type=warfare_type,
                is_mass_casualty=False,
                event_id=f"IND_{warfare_type}_{day}_{hour}_{minute}_{uuid.uuid4().hex[:8]}",
                environmental_factors=environmental_factors,
            )
            events.append(event)
            remaining_patients -= group_size

        return events

    def _get_special_events_for_day(
        self, day: int, special_events: Dict[str, bool], day_patients: int, base_date: str
    ) -> List[CasualtyEvent]:
        """Generate special events for a specific day"""
        events = []

        # Parse base_date properly
        base_datetime = datetime.strptime(base_date, "%Y-%m-%d")

        # Handle mass casualty events more dynamically
        if special_events.get("mass_casualty") and random.random() < 0.2:
            template = self.warfare_patterns["special_event_templates"]["mass_casualty"]

            # Select a random hour for the mass casualty event (prefer daylight)
            hour = random.randint(6, 18)  # Daylight hours

            # Calculate patient count (5-15% of day's patients)
            casualty_percentage = random.uniform(0.05, 0.15)
            patients = int(day_patients * casualty_percentage * template["casualty_multiplier"])
            patients = min(patients, 100)  # Cap at 100 for single event

            timestamp = base_datetime + timedelta(days=day - 1, hours=hour)

            event = CasualtyEvent(
                timestamp=timestamp,
                patient_count=patients,
                warfare_type="mixed",
                is_mass_casualty=True,
                event_id=f"SE_mass_casualty_{day}_{hour}_{uuid.uuid4().hex[:8]}",
                special_event_type="mass_casualty",
            )
            events.append(event)

        if special_events.get("major_offensive") and day == 2:
            template = self.warfare_patterns["special_event_templates"]["major_offensive"]
            hour = random.choice(template["preferred_start_hours"])
            patients = int(day_patients * 0.3 * template["casualty_multiplier"])

            timestamp = base_datetime + timedelta(days=day - 1, hours=hour)

            event = CasualtyEvent(
                timestamp=timestamp,
                patient_count=patients,
                warfare_type="mixed",
                is_mass_casualty=True,
                event_id=f"SE_major_offensive_{day}_{hour}_{uuid.uuid4().hex[:8]}",
                special_event_type="major_offensive",
            )
            events.append(event)

        if special_events.get("ambush") and day in [1, 4, 6]:
            template = self.warfare_patterns["special_event_templates"]["ambush"]
            hour = random.choice(template["preferred_start_hours"])
            patients = int(day_patients * 0.1 * template["casualty_multiplier"])

            timestamp = base_datetime + timedelta(days=day - 1, hours=hour)

            event = CasualtyEvent(
                timestamp=timestamp,
                patient_count=patients,
                warfare_type="mixed",
                is_mass_casualty=True,
                event_id=f"SE_ambush_{day}_{hour}_{uuid.uuid4().hex[:8]}",
                special_event_type="ambush",
            )
            events.append(event)

        return events

    def _apply_environmental_modifiers(
        self, events: List[CasualtyEvent], environmental_conditions: Dict[str, bool]
    ) -> List[CasualtyEvent]:
        """Apply environmental effects to all events"""
        active_conditions = [cond for cond, active in environmental_conditions.items() if active]

        if not active_conditions:
            return events

        # Calculate compound modifiers
        total_casualty_mod = 1.0
        total_visibility = 1.0
        total_delay = 0

        for condition in active_conditions:
            mod = self.warfare_patterns["environmental_modifiers"][condition]
            total_casualty_mod *= mod["casualty_modifier"]
            total_visibility *= mod["visibility"]
            total_delay += mod["evacuation_delay_minutes"]

        # Apply to each event
        modified_events = []

        for event in events:
            # Adjust patient count
            adjusted_count = max(1, int(event.patient_count * total_casualty_mod))

            # Add discovery delay for low visibility
            if total_visibility < 0.5 and not event.is_mass_casualty:
                delay = random.randint(0, int(total_delay))
                adjusted_timestamp = event.timestamp + timedelta(minutes=delay)
            else:
                adjusted_timestamp = event.timestamp

            # Create modified event
            modified_event = CasualtyEvent(
                timestamp=adjusted_timestamp,
                patient_count=adjusted_count,
                warfare_type=event.warfare_type,
                is_mass_casualty=event.is_mass_casualty,
                event_id=event.event_id,
                environmental_factors=active_conditions,
                special_event_type=event.special_event_type,
            )

            modified_events.append(modified_event)

        return modified_events

    def _adjust_hourly_total(self, hourly_casualties: List[Tuple[int, int]], target_total: int):
        """Adjust hourly casualties to match target total"""
        current_total = sum(h[1] for h in hourly_casualties)

        if current_total == target_total:
            return

        difference = target_total - current_total

        # Find hours with casualties to adjust
        hours_with_casualties = [(i, h[1]) for i, h in enumerate(hourly_casualties) if h[1] > 0]

        if not hours_with_casualties:
            # If no hours have casualties, distribute evenly
            per_hour = target_total // 24
            remainder = target_total % 24
            for i in range(24):
                casualties = per_hour
                if i < remainder:
                    casualties += 1
                hourly_casualties[i] = (i, casualties)
            return

        # Distribute difference among hours with casualties
        safety_counter = 0
        max_iterations = 1000  # Prevent infinite loops
        while difference != 0 and safety_counter < max_iterations:
            safety_counter += 1
            made_progress = False

            for i, _ in hours_with_casualties:
                if difference == 0:
                    break

                if difference > 0:
                    hourly_casualties[i] = (hourly_casualties[i][0], hourly_casualties[i][1] + 1)
                    difference -= 1
                    made_progress = True
                elif hourly_casualties[i][1] > 1:  # Don't reduce below 1
                    hourly_casualties[i] = (hourly_casualties[i][0], hourly_casualties[i][1] - 1)
                    difference += 1
                    made_progress = True

            # If no progress made in a full loop, break to prevent infinite loop
            if not made_progress:
                break

    def _validate_hourly_distribution(
        self, hourly_casualties: List[Tuple[int, int]], total_patients: int
    ) -> List[Tuple[int, int]]:
        """Validate hourly distribution and redistribute if too concentrated at hour 0"""
        if not hourly_casualties or total_patients == 0:
            return hourly_casualties

        # Check if hour 0 has more than 10% of patients
        hour_0_patients = hourly_casualties[0][1] if hourly_casualties else 0

        if hour_0_patients > total_patients * 0.1:
            # Calculate excess to redistribute
            target_hour_0 = int(total_patients * 0.05)  # Target 5% for hour 0
            excess = hour_0_patients - target_hour_0

            if excess > 0:
                # Create mutable list
                hourly_list = list(hourly_casualties)

                # Reduce hour 0
                hourly_list[0] = (0, target_hour_0)

                # Redistribute excess to daytime hours (6-18)
                daytime_hours = list(range(6, 19))
                patients_per_hour = excess // len(daytime_hours)
                remainder = excess % len(daytime_hours)

                for i, hour in enumerate(daytime_hours):
                    additional = patients_per_hour + (1 if i < remainder else 0)
                    current = hourly_list[hour][1]
                    hourly_list[hour] = (hour, current + additional)

                return hourly_list

        return hourly_casualties
