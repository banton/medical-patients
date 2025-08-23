#!/usr/bin/env python3
"""
QA MILESTONE 1: Interactive Health Deterioration Demo
Shows realistic patient health decline and treatment effects
"""

import os
import sys
import time
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from medical_simulation.deterioration_calculator import DeteriorationCalculator
from medical_simulation.health_score_engine import HealthScoreEngine
from medical_simulation.treatment_modifiers import TreatmentModifiers


def print_health_bar(health: int, max_width: int = 50) -> str:
    """Create visual health bar"""
    filled = int((health / 100) * max_width)
    bar = "█" * filled + "░" * (max_width - filled)

    # Color coding
    if health >= 70:
        color = "\033[92m"  # Green
    elif health >= 40:
        color = "\033[93m"  # Yellow
    elif health >= 20:
        color = "\033[91m"  # Red
    else:
        color = "\033[95m"  # Purple (critical)

    return f"{color}{bar}\033[0m {health:3d}%"


def print_timeline_point(hour: float, health: int, status: str, event: Optional[str] = None):
    """Print a timeline entry with formatting"""
    time_str = f"T+{hour:4.1f}h"
    health_bar = print_health_bar(health)

    if event:
        print(f"{time_str} │ {health_bar} │ {status:12s} │ ⚡ {event}")
    else:
        print(f"{time_str} │ {health_bar} │ {status:12s} │")


def demo_scenario_1():
    """Scenario 1: Severe battle injury without treatment - Patient dies"""
    print("\n" + "=" * 80)
    print("SCENARIO 1: Severe Battle Injury - No Treatment")
    print("=" * 80)
    print("\nPatient: 22-year-old soldier")
    print("Injury: IED blast with multiple fragment wounds and arterial bleeding")
    print("Location: Remote patrol base, 2 hours from Role 2 facility")
    print("-" * 80)

    engine = HealthScoreEngine()
    calc = DeteriorationCalculator()

    # Calculate deterioration rate
    base_rate = calc.calculate_base_deterioration(
        "Battle Injury", "Severe", injuries=[{"condition": "Arterial bleeding from femoral artery"}]
    )

    print("\nInitial Assessment:")
    print(f"  Deterioration Rate: {base_rate:.1f} health/hour")
    print("  Expected survival: <2 hours without intervention")

    # Generate timeline
    timeline = engine.calculate_health_timeline(
        injury_type="Battle Injury",
        severity="Severe",
        duration_hours=3,
        deterioration_rate=base_rate,
        modifiers=None,  # No treatment!
    )

    print("\nHealth Timeline:")
    print("Time  │ Health                                              │ Status       │ Event")
    print("─" * 80)

    for point in timeline:
        print_timeline_point(point["hour"], point["health"], point["status"], point.get("event"))
        time.sleep(0.3)  # Dramatic effect

    print("\n⚰️  OUTCOME: KIA (Killed in Action) - Preventable death")
    print("   Analysis: Immediate tourniquet could have saved this soldier")


def demo_scenario_2():
    """Scenario 2: Same injury with tourniquet at 15 minutes - Patient survives"""
    print("\n" + "=" * 80)
    print("SCENARIO 2: Severe Battle Injury - Tourniquet Applied")
    print("=" * 80)
    print("\nPatient: 24-year-old soldier")
    print("Injury: IED blast with multiple fragment wounds and arterial bleeding")
    print("Location: Squad medic applies tourniquet at T+15 minutes")
    print("-" * 80)

    engine = HealthScoreEngine()
    calc = DeteriorationCalculator()
    TreatmentModifiers()

    base_rate = calc.calculate_base_deterioration(
        "Battle Injury", "Severe", injuries=[{"condition": "Arterial bleeding from femoral artery"}]
    )

    # Treatment timeline
    treatments = [
        {"hour": 0.25, "type": "treatment", "modifier": 0.2},  # Tourniquet at 15 min
        {"hour": 0.5, "type": "treatment", "modifier": 0.7},  # IV fluids at 30 min
        {"hour": 2.0, "type": "treatment", "modifier": 0.1},  # Surgery at Role 2
    ]

    # Generate more granular timeline (every 15 minutes)
    detailed_timeline = []
    current_health = engine.get_initial_health("Battle Injury", "Severe")
    current_deterioration = base_rate
    active_treatments = []

    for quarter_hour in range(33):  # 0 to 8 hours in 15-min increments
        hour = quarter_hour * 0.25

        # Apply treatments at the right time
        for treatment in treatments:
            if abs(treatment["hour"] - hour) < 0.01:
                current_deterioration *= treatment["modifier"]
                active_treatments.append(treatment)
                if treatment["hour"] == 0.25:
                    current_health += 5  # Tourniquet health boost
                elif treatment["hour"] == 0.5:
                    current_health += 10  # IV fluids boost
                elif treatment["hour"] == 2.0:
                    current_health += 25  # Surgery boost

        # Apply deterioration
        if hour > 0:
            current_health -= current_deterioration * 0.25

        current_health = max(0, min(100, current_health))

        detailed_timeline.append(
            {
                "hour": hour,
                "health": int(current_health),
                "status": "stable" if current_health > 40 else "unstable" if current_health > 10 else "critical",
            }
        )

        if current_health <= 0:
            break

    timeline = detailed_timeline

    print("\nHealth Timeline with Interventions:")
    print("Time  │ Health                                              │ Status       │ Event")
    print("─" * 80)

    for i, point in enumerate(timeline):
        event = point.get("event")

        # Add treatment markers
        if point["hour"] == 0.25:
            event = "🩹 TOURNIQUET APPLIED - Bleeding controlled!"
        elif point["hour"] == 0.5:
            event = "💉 IV FLUIDS STARTED - Shock prevention"
        elif point["hour"] == 2.0:
            event = "🏥 SURGERY at Role 2 - Definitive care"

        print_timeline_point(point["hour"], point["health"], point["status"], event)

        if i < len(timeline) - 1:
            time.sleep(0.2)

    final_health = timeline[-1]["health"]
    print(f"\n✅ OUTCOME: SURVIVED - Final health: {final_health}%")
    print("   Analysis: Rapid tourniquet application saved this soldier's life")


def demo_scenario_3():
    """Scenario 3: Golden Hour demonstration"""
    print("\n" + "=" * 80)
    print("SCENARIO 3: Golden Hour Effect Demonstration")
    print("=" * 80)
    print("\nComparing treatment timing impact on survival")
    print("-" * 80)

    engine = HealthScoreEngine()
    DeteriorationCalculator()

    scenarios = [
        ("Immediate (5 min)", 0.083),
        ("Within Golden Hour (45 min)", 0.75),
        ("After Golden Hour (90 min)", 1.5),
        ("Delayed (3 hours)", 3.0),
    ]

    print("\nTreatment Timing Comparison:")
    print("─" * 50)

    for desc, treatment_hour in scenarios:
        timeline = engine.calculate_health_timeline(
            injury_type="Battle Injury",
            severity="Moderate to severe",
            duration_hours=6,
            deterioration_rate=20,
            modifiers=[{"hour": treatment_hour, "type": "treatment", "modifier": 0.3}],
        )

        final_health = timeline[-1]["health"]
        survived = "SURVIVED ✅" if final_health > 0 else "DIED ❌"

        print(f"{desc:30s}: Final health = {final_health:3.0f}% - {survived}")
        time.sleep(0.5)

    print("\n📊 Key Insight: Every minute counts in the Golden Hour!")


def interactive_demo():
    """Interactive demo where user can apply treatments"""
    print("\n" + "=" * 80)
    print("INTERACTIVE DEMO: You're the Combat Medic!")
    print("=" * 80)

    engine = HealthScoreEngine()
    DeteriorationCalculator()
    tm = TreatmentModifiers()

    print("\n🚨 CASUALTY ALERT!")
    print("Soldier hit by sniper fire - chest wound with suspected pneumothorax")
    print("You have limited supplies at this forward position (Role 1)")
    print("-" * 80)

    initial_health = engine.get_initial_health("Battle Injury", "Severe")
    current_health = initial_health
    current_hour = 0
    deterioration = 25.0
    applied_treatments = []

    # Get appropriate treatments for chest wound (no tourniquet!)
    available = tm.get_available_treatments("role1", "chest wound with pneumothorax")

    while current_health > 0 and current_hour < 6:
        print(f"\n⏰ Time: T+{current_hour:.1f} hours")
        print(f"Patient Status: {print_health_bar(int(current_health))}")
        print(f"Deterioration Rate: {deterioration:.1f} health/hour")

        if current_hour == 0:
            print("\nAvailable treatments:")
            for i, treatment in enumerate(available, 1):
                t_data = tm.treatments[treatment]
                print(
                    f"  {i}. {treatment:20s} (+{t_data['health_boost']} health, "
                    f"{t_data['deterioration_modifier']:.1f}x deterioration)"
                )
            print("  0. Wait and observe (advance 30 minutes)")

            try:
                choice = input("\nYour action (number): ").strip()
                if choice == "0":
                    pass
                else:
                    idx = int(choice) - 1
                    if 0 <= idx < len(available):
                        treatment = available[idx]
                        new_h, new_d, info = tm.apply_treatment(treatment, current_health, deterioration)
                        print(f"\n✅ Applied {treatment}!")
                        print(f"   Health: {current_health:.0f} → {new_h:.0f}")
                        print(f"   Deterioration: {deterioration:.1f} → {new_d:.1f}")
                        current_health = new_h
                        deterioration = new_d
                        applied_treatments.append(treatment)
                        available.remove(treatment)
            except (ValueError, IndexError):
                print("Invalid choice, waiting...")

        # Advance time
        current_hour += 0.5
        current_health -= deterioration * 0.5
        current_health = max(0, current_health)

    print("\n" + "=" * 80)
    if current_health > 0:
        print(f"✅ PATIENT SURVIVED! Final health: {current_health:.0f}%")
        print(f"Treatments applied: {', '.join(applied_treatments)}")
    else:
        print("❌ PATIENT DIED")
        print("Consider different treatment timing or priorities")


def main():
    """Run the demo suite"""
    print("\n" + "=" * 80)
    print(" MEDICAL SIMULATION - HEALTH DETERIORATION DEMONSTRATION")
    print("=" * 80)
    print("\nThis demo shows realistic combat casualty health modeling:")
    print("• Deterioration rates based on injury severity")
    print("• Golden Hour effects on survival")
    print("• Treatment impact on patient outcomes")
    print("• Critical decision points for medical personnel")

    while True:
        print("\n" + "-" * 50)
        print("Select Demo:")
        print("1. Scenario 1: No Treatment (KIA)")
        print("2. Scenario 2: Tourniquet Success")
        print("3. Scenario 3: Golden Hour Demonstration")
        print("4. Interactive: You're the Medic!")
        print("5. Run All Demos")
        print("Q. Quit")

        choice = input("\nChoice: ").strip().upper()

        if choice == "1":
            demo_scenario_1()
        elif choice == "2":
            demo_scenario_2()
        elif choice == "3":
            demo_scenario_3()
        elif choice == "4":
            interactive_demo()
        elif choice == "5":
            demo_scenario_1()
            input("\nPress Enter to continue...")
            demo_scenario_2()
            input("\nPress Enter to continue...")
            demo_scenario_3()
        elif choice == "Q":
            print("\nExiting demo...")
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
