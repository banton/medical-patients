from collections import Counter, defaultdict
from datetime import datetime, timedelta

def transform_job_data_for_visualization(job_data):
    """
    Transforms job data, specifically the list of Patient objects,
    for the visualization dashboard.
    """
    patients = job_data.get("patients_data", [])
    sankey_base_nodes = [ # Define base nodes for reuse
        {"name": 'POI'}, {"name": 'R1'}, {"name": 'R2'}, {"name": 'R3'},
        {"name": 'R4'}, {"name": 'RTD'}, {"name": 'KIA'}
    ]

    if not patients:
        # Return structure similar to mock data but empty or with defaults
        return {
            "summary": {"total_patients": 0, "kia_rate": 0, "rtd_rate": 0, "average_treatment_time": 0},
            "patient_flow": {"nodes": sankey_base_nodes, "links": []}, # Use base nodes
            "facility_usage": [],
            "timeline_analysis": [],
            "front_comparison": [],
            "treatment_effectiveness": [], # Placeholder
            "nationalityDistribution": [],
            "injuryDistribution": [],
            "triageDistribution": [],
            "casualtyFlowByDay": []
        }

    total_patients = len(patients)
    kia_count = sum(1 for p in patients if p.current_status == "KIA")
    rtd_count = sum(1 for p in patients if p.current_status == "RTD")

    summary_data = {
        "total_patients": total_patients,
        "kia_rate": (kia_count / total_patients) if total_patients > 0 else 0,
        "rtd_rate": (rtd_count / total_patients) if total_patients > 0 else 0,
        "average_treatment_time": 0  # Placeholder, needs calculation based on treatment_history
    }

    # Patient Flow (Sankey)
    # sankey_nodes are already defined as sankey_base_nodes
    sankey_node_map = {node["name"]: i for i, node in enumerate(sankey_base_nodes)}
    sankey_links_counter = Counter()

    for p in patients:
        path = ["POI"] # All patients start at POI implicitly or explicitly
        for treatment_event in sorted(p.treatment_history, key=lambda x: x.get("date", "")):
            facility = treatment_event.get("facility")
            if facility and facility not in ["RTD", "KIA"]: # RTD/KIA are terminal, handled by current_status
                 path.append(facility)
        
        # Add final status if it's RTD or KIA and not the last in path
        if p.current_status in ["RTD", "KIA"] and (not path or path[-1] != p.current_status):
            path.append(p.current_status)

        # Deduplicate consecutive facilities in path (e.g. R1 -> R1)
        deduplicated_path = []
        if path:
            deduplicated_path.append(path[0])
            for i in range(1, len(path)):
                if path[i] != path[i-1]:
                    deduplicated_path.append(path[i])
        
        for i in range(len(deduplicated_path) - 1):
            source_node_name = deduplicated_path[i]
            target_node_name = deduplicated_path[i+1]
            if source_node_name in sankey_node_map and target_node_name in sankey_node_map:
                source_idx = sankey_node_map[source_node_name]
                target_idx = sankey_node_map[target_node_name]
                sankey_links_counter[(source_idx, target_idx)] += 1
    
    sankey_links = [{"source": src, "target": tgt, "value": val} for (src, tgt), val in sankey_links_counter.items()]
    patient_flow_data = {"nodes": sankey_base_nodes, "links": sankey_links} # Use base nodes

    # Facility Usage
    facility_usage_counter = Counter()
    for p in patients:
        visited_facilities = set(["POI"]) # Implicitly all start at POI
        for th in p.treatment_history:
            if th.get("facility") and th["facility"] not in ["RTD", "KIA"]:
                 visited_facilities.add(th["facility"])
        for facility in visited_facilities:
            if facility in ["R1", "R2", "R3", "R4"]: # Only count usage for actual treatment facilities
                facility_usage_counter[facility] += 1
    
    facility_usage_data = [
        {"name": facility, "used": count, "capacity": 100} # Capacity is a placeholder from mock
        for facility, count in facility_usage_counter.items()
    ]
    facility_usage_data.sort(key=lambda x: x["name"])


    # Timeline Analysis (Casualties per day_of_injury)
    # Assuming p.day_of_injury is an integer like 1, 2, 3...
    timeline_counter = Counter()
    for p in patients:
        if p.day_of_injury is not None:
            timeline_counter[f"Day {p.day_of_injury}"] += 1
    timeline_analysis_data = [{"day": day, "casualties": count} for day, count in sorted(timeline_counter.items())]


    # Front Comparison
    front_data = defaultdict(lambda: {"casualties": 0, "rtd": 0, "kia": 0})
    for p in patients:
        if p.front:
            front_data[p.front]["casualties"] += 1
            if p.current_status == "RTD":
                front_data[p.front]["rtd"] += 1
            elif p.current_status == "KIA":
                front_data[p.front]["kia"] += 1
    front_comparison_data = [{"front": front, **counts} for front, counts in front_data.items()]

    # Nationality Distribution
    nationality_counter = Counter(p.nationality for p in patients if p.nationality)
    nationality_distribution_data = [{"name": nat, "value": count} for nat, count in nationality_counter.items()]

    # Injury Distribution
    injury_counter = Counter(p.injury_type for p in patients if p.injury_type)
    injury_distribution_data = [{"name": injury, "value": count} for injury, count in injury_counter.items()]

    # Triage Distribution
    triage_counter = Counter(p.triage_category for p in patients if p.triage_category)
    triage_distribution_data = [{"name": triage, "value": count} for triage, count in triage_counter.items()]

    # Casualty Flow By Day (Simplified: total new casualties per day at POI)
    # This requires knowing the entry point (POI) and its day.
    # Assuming day_of_injury refers to the day they became a casualty / entered POI.
    casualty_flow_by_day_data = []
    daily_poi_entries = Counter()
    for p in patients:
        if p.day_of_injury is not None:
            daily_poi_entries[p.day_of_injury] +=1

    for day_num, poi_count in sorted(daily_poi_entries.items()):
        # This is a simplification. A full flow would track transitions daily.
        casualty_flow_by_day_data.append({
            "day": f"Day {day_num}",
            "POI": poi_count, 
            # Other facilities would require more complex daily state tracking
            "R1": 0, "R2": 0, "R3": 0, "R4": 0, "RTD": 0, "KIA": 0 
        })


    return {
        "summary": summary_data,
        "patient_flow": patient_flow_data,
        "facility_usage": facility_usage_data,
        "timeline_analysis": timeline_analysis_data,
        "front_comparison": front_comparison_data,
        "treatment_effectiveness": [ # Placeholder as per mock
            {"treatment": 'Tourniquet', "effectiveness": 0.9},
            {"treatment": 'Chest Seal', "effectiveness": 0.8},
            {"treatment": 'IV Fluids', "effectiveness": 0.7},
        ],
        "nationalityDistribution": nationality_distribution_data,
        "injuryDistribution": injury_distribution_data,
        "triageDistribution": triage_distribution_data,
        "casualtyFlowByDay": casualty_flow_by_day_data 
    }
