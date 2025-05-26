# In patient_generator/visualization_data.py


def transform_job_data_for_visualization(job_data):
    """
    Transforms job data for the enhanced military medical visualization dashboard.
    Focus on patient flow through the treatment chain.
    """
    patients = job_data.get("patients_data", [])
    total_patients = len(patients)

    # Define nodes for the Sankey diagram
    sankey_nodes = [
        {"id": "POI", "name": "Point of Injury"},
        {"id": "R1", "name": "Role 1"},
        {"id": "R2", "name": "Role 2"},
        {"id": "R3", "name": "Role 3"},
        {"id": "R4", "name": "Role 4"},
        {"id": "RTD", "name": "Return to Duty"},
        {"id": "KIA", "name": "Killed in Action"},
    ]

    # Create a mapping of node id to index for creating links
    node_map = {node["id"]: idx for idx, node in enumerate(sankey_nodes)}

    # Track patient flow between facilities
    flow_links = []

    # Initialize counters for each path
    path_counters = {
        # From POI
        ("POI", "KIA"): 0,
        ("POI", "RTD"): 0,
        ("POI", "R1"): 0,
        # From R1
        ("R1", "KIA"): 0,
        ("R1", "RTD"): 0,
        ("R1", "R2"): 0,
        # From R2
        ("R2", "KIA"): 0,
        ("R2", "RTD"): 0,
        ("R2", "R3"): 0,
        # From R3
        ("R3", "KIA"): 0,
        ("R3", "RTD"): 0,
        ("R3", "R4"): 0,
        # Note: R4 to KIA/RTD is handled differently in facility_stats
        # For Sankey, R4 is often a terminal point or leads to RTD.
        # If R4 can lead to KIA, add ("R4", "KIA"): 0
        # If R4 leads to RTD, add ("R4", "RTD"): 0. The current logic in facility_stats assumes R4 -> RTD.
    }

    # Function to analyze patient treatment history
    def analyze_patient_path(patient):
        # All patients start at POI
        # current_location = "POI" # Not strictly needed with path list
        path = ["POI"]

        # Get treatment locations in chronological order
        treatments = sorted(patient.treatment_history, key=lambda x: x.get("date", ""))

        # Extract just the facility sequence
        for treatment in treatments:
            facility = treatment.get("facility")
            # Ensure facility is one of the defined Sankey nodes and not POI if already added
            if facility and facility in node_map and (not path or path[-1] != facility):
                if facility == "POI" and len(path) > 0:  # Avoid POI -> POI if POI is in treatment history
                    continue
                path.append(facility)

        # Add final status if it's terminal and not already the last step
        if patient.current_status in ["RTD", "KIA"] and (not path or path[-1] != patient.current_status):
            path.append(patient.current_status)

        # Convert path to transitions between facilities
        for i in range(len(path) - 1):
            source = path[i]
            target = path[i + 1]

            # Only count transitions we're interested in for path_counters
            transition_key = (source, target)
            if transition_key in path_counters:
                path_counters[transition_key] += 1
            # Special handling for R4 to RTD if not in path_counters explicitly
            elif source == "R4" and target == "RTD":
                # This assumes R4 patients eventually RTD if not KIA before R4
                # For a more robust Sankey, ensure all terminal paths from R4 are in path_counters
                if ("R4", "RTD") not in path_counters:
                    path_counters[("R4", "RTD")] = 0
                path_counters[("R4", "RTD")] += 1

    # Process all patients to build flow statistics
    for patient in patients:
        analyze_patient_path(patient)

    # Convert path counters to Sankey links
    # Add R4 -> RTD if it was counted and not in initial path_counters
    if ("R4", "RTD") in path_counters and path_counters[("R4", "RTD")] > 0:
        # This ensures R4 to RTD link is created if patients reach R4 and then RTD
        pass  # It will be picked up by the loop below

    for (source, target), count in path_counters.items():
        if count > 0 and source in node_map and target in node_map:
            flow_links.append(
                {
                    "source": node_map[source],
                    "target": node_map[target],
                    "value": count,
                    "source_id": source,  # For tooltip or debugging
                    "target_id": target,  # For tooltip or debugging
                }
            )

    # Create summary statistics by facility
    # Initialize with all keys and correct default types
    facility_ids = ["POI", "R1", "R2", "R3", "R4"]
    facility_stats = {
        facility_id: {
            "total": 0,
            "to_kia": 0,
            "to_rtd": 0,
            "to_next": 0,
            "kia_percent": 0.0,
            "rtd_percent": 0.0,
            "next_percent": 0.0,
        }
        for facility_id in facility_ids
    }

    # Populate the counts
    facility_stats["POI"]["total"] = total_patients
    facility_stats["POI"]["to_kia"] = path_counters.get(("POI", "KIA"), 0)
    facility_stats["POI"]["to_rtd"] = path_counters.get(("POI", "RTD"), 0)
    facility_stats["POI"]["to_next"] = path_counters.get(("POI", "R1"), 0)

    facility_stats["R1"]["total"] = path_counters.get(("POI", "R1"), 0)
    facility_stats["R1"]["to_kia"] = path_counters.get(("R1", "KIA"), 0)
    facility_stats["R1"]["to_rtd"] = path_counters.get(("R1", "RTD"), 0)
    facility_stats["R1"]["to_next"] = path_counters.get(("R1", "R2"), 0)

    facility_stats["R2"]["total"] = path_counters.get(("R1", "R2"), 0)
    facility_stats["R2"]["to_kia"] = path_counters.get(("R2", "KIA"), 0)
    facility_stats["R2"]["to_rtd"] = path_counters.get(("R2", "RTD"), 0)
    facility_stats["R2"]["to_next"] = path_counters.get(("R2", "R3"), 0)

    facility_stats["R3"]["total"] = path_counters.get(("R2", "R3"), 0)
    facility_stats["R3"]["to_kia"] = path_counters.get(("R3", "KIA"), 0)
    facility_stats["R3"]["to_rtd"] = path_counters.get(("R3", "RTD"), 0)
    facility_stats["R3"]["to_next"] = path_counters.get(("R3", "R4"), 0)

    facility_stats["R4"]["total"] = path_counters.get(("R3", "R4"), 0)
    facility_stats["R4"]["to_kia"] = path_counters.get(("R4", "KIA"), 0)
    facility_stats["R4"]["to_rtd"] = path_counters.get(("R4", "RTD"), 0)
    facility_stats["R4"]["to_next"] = 0  # No next level after R4 in this model

    # Calculate percentages for each facility
    for _facility_id, stats_val in facility_stats.items():  # Renamed to avoid conflict
        total = stats_val["total"]
        if total > 0:
            stats_val["kia_percent"] = round((stats_val["to_kia"] / total) * 100, 1)
            stats_val["rtd_percent"] = round((stats_val["to_rtd"] / total) * 100, 1)
            stats_val["next_percent"] = round((stats_val["to_next"] / total) * 100, 1)
        else:
            stats_val["kia_percent"] = 0.0
            stats_val["rtd_percent"] = 0.0
            stats_val["next_percent"] = 0.0

    # Summary of total outcomes
    # Recalculate total_kia and total_rtd based on the sum of terminal events from path_counters
    # This avoids double counting if a patient is KIA/RTD at POI and also counted in facility_stats["POI"]["to_kia"]

    # Total KIA is sum of all transitions to KIA
    calculated_total_kia = sum(count for (src, tgt), count in path_counters.items() if tgt == "KIA")
    # Total RTD is sum of all transitions to RTD
    calculated_total_rtd = sum(count for (src, tgt), count in path_counters.items() if tgt == "RTD")

    # If no patients, return a default structure
    if not patients:
        empty_facility_stats = {
            key: {
                "total": 0,
                "to_kia": 0,
                "to_rtd": 0,
                "to_next": 0,
                "kia_percent": 0.0,
                "rtd_percent": 0.0,
                "next_percent": 0.0,
            }
            for key in ["POI", "R1", "R2", "R3", "R4"]
        }
        return {
            "summary": {"total_patients": 0, "total_kia": 0, "total_rtd": 0, "kia_percent": 0.0, "rtd_percent": 0.0},
            "patient_flow": {"nodes": sankey_nodes, "links": []},
            "facility_stats": empty_facility_stats,
        }

    return {
        "summary": {
            "total_patients": total_patients,
            "total_kia": calculated_total_kia,
            "total_rtd": calculated_total_rtd,
            "kia_percent": round((calculated_total_kia / total_patients) * 100, 1) if total_patients > 0 else 0.0,
            "rtd_percent": round((calculated_total_rtd / total_patients) * 100, 1) if total_patients > 0 else 0.0,
        },
        "patient_flow": {"nodes": sankey_nodes, "links": flow_links},
        "facility_stats": facility_stats,
    }
