# Patient Timeline Viewer

A React-based visualizer for military medical evacuation patient flow. This application loads patient data from JSON files and provides an animated timeline showing patient movement through medical facilities (POI → Role1 → Role2 → Role3 → Role4).

## Features

- **Interactive Timeline**: Play, pause, and control playback speed of patient movement
- **Real-time Visualization**: Watch patients move between facilities with smooth animations
- **Patient Status Tracking**: Visual indicators for KIA, RTD, and active patients
- **Facility Overview**: 5-column layout showing all medical evacuation levels
- **File Upload**: Drag-and-drop interface for loading patients.json files
- **Statistics Dashboard**: Real-time counts and status summaries
- **Patient Names**: Displays patient names in "FirstInitial. LastName, Nationality" format
- **Front Information**: Shows battlefield front assignments alongside patient activities
- **Cumulative KIA/RTD Tracking**: Smart tallying system with POI capturing pre-Role1 deaths
- **Fixed Column Headers**: Consistent header heights with always-visible counters
- **Compact Design**: 50% more patients visible with tighter, efficient layout
- **Viewport Indicators**: Shows count of patients below visible area with scroll hints
- **Auto-Hide Terminal Cases**: KIA/RTD patients disappear after 15 minutes to reduce clutter

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Framer Motion** for smooth animations
- **Modern ES6+** with full type safety

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Navigate to the project directory
cd patient-timeline-viewer

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:5174`

### Building for Production

```bash
npm run build
npm run preview
```

## Usage

1. **Load Patient Data**: 
   - Generate patient data from the main medical patients generator
   - Download the resulting `patients.json` file
   - Upload it using the drag-and-drop interface

2. **Timeline Controls**:
   - **Play/Pause**: Start and stop the timeline animation
   - **Speed Control**: Adjust playback speed (0.5x to 60x)
   - **Reset**: Return to the beginning of the timeline
   - **Seek**: Click on the progress bar to jump to specific times

3. **Patient Visualization**:
   - Patients appear as compact cards showing name, nationality, and front
   - Color coding indicates triage category (T1=Red, T2=Yellow, T3=Green)
   - Status indicators show KIA (red), RTD (green), or active (blue)
   - Animations show transit between facilities
   - Cards automatically hide after 15 minutes for KIA/RTD to reduce clutter

4. **KIA/RTD Tallying System**:
   - **POI Column**: Tracks all deaths that occur before reaching Role1 medical care
   - **Role1-4 Columns**: Track facility-specific deaths and RTDs during treatment
   - **Fixed Headers**: Counters always visible with consistent layout
   - **Real-time Updates**: Cumulative counts update as timeline progresses

## Patient Data Format

The application expects JSON files with the following structure:

```json
[
  {
    "patient": {
      "id": "string | number",
      "nationality": "string",
      "triage_category": "T1" | "T2" | "T3",
      "final_status": "KIA" | "RTD" | "Remains_Role4",
      "injury_timestamp": "ISO 8601 datetime",
      "front": "string",
      "demographics": {
        "given_name": "string",
        "family_name": "string",
        "nationality": "string"
      },
      "movement_timeline": [
        {
          "event_type": "arrival" | "evacuation_start" | "transit_start" | "kia" | "rtd",
          "facility": "POI" | "Role1" | "Role2" | "Role3" | "Role4",
          "timestamp": "ISO 8601 datetime",
          "hours_since_injury": number,
          "evacuation_duration_hours": number,
          "transit_duration_hours": number
        }
      ]
    }
  }
]
```

**Note**: The application supports both wrapped format (with `patient` key) and direct patient objects. Names can be in `demographics` or at the top level.

## Project Structure

```
patient-timeline-viewer/
├── src/
│   ├── components/
│   │   ├── PatientCard.tsx       # Individual patient display
│   │   ├── FacilityColumn.tsx    # Medical facility container
│   │   ├── TimelineControls.tsx  # Playback controls
│   │   └── FileUploader.tsx      # File upload interface
│   ├── types/
│   │   └── patient.types.ts      # TypeScript definitions
│   ├── utils/
│   │   └── timelineEngine.ts     # Timeline calculation logic
│   ├── App.tsx                   # Main application
│   └── main.tsx                  # Application entry point
├── public/
│   └── sample-patients.json      # Example data file
└── README.md
```

## Key Components

### TimelineEngine
Calculates patient locations at any given time based on their movement timeline. Handles complex scenarios like evacuation periods, transit times, and terminal events (KIA/RTD).

### PatientCard
Compact animated patient representation with:
- Patient name display (FirstInitial. LastName, Nationality)
- Triage category color coding with smaller badges
- Status indicators and animations
- Activity status and battlefield front information
- Auto-hide functionality for KIA/RTD after 15 minutes
- Smooth layout transitions with optimized spacing

### FacilityColumn
Medical facility representation with fixed-height headers showing:
- Facility metadata and descriptions in compact layout
- Cumulative KIA/RTD counters (POI shows pre-Role1 deaths, others show facility-specific)
- Current patient counts and status summaries
- Scroll indicators for patients below viewport
- Organized patient display with optimized spacing

## Sample Data

A sample `patients.json` file is included in the `public/` directory demonstrating:
- Multiple triage categories (T1, T2, T3)
- Various patient outcomes (KIA, RTD, Remains)
- Complex movement timelines
- Different injury types and nationalities

## Integration

This visualizer is designed to work with patient data generated by the main Medical Patients Generator application. It serves as a separate, standalone tool for visualizing patient flow without affecting the main application's functionality.

## Development

The application follows React best practices with:
- TypeScript for type safety
- Component-based architecture
- Custom hooks for state management
- Efficient re-rendering with useMemo
- Smooth animations with Framer Motion

## Browser Support

Modern browsers supporting ES6+ features:
- Chrome 80+
- Firefox 72+
- Safari 13+
- Edge 80+