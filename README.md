# Victoria House Photos Map

A web application that displays house listings from saved .mhtml files on an interactive map centered at Victoria, BC.

## Features

- **Interactive Map**: Leaflet-based map centered on Victoria, BC
- **Address Extraction**: Automatically extracts addresses from .mhtml filenames
- **Geocoding**: Converts addresses to map coordinates using OpenStreetMap Nominatim
- **Map Pins**: Displays a pin for each property location
- **Hover Tooltips**: Shows address and detail link when hovering over pins
- **Property Details**: Click "View Details" to see the saved house photos
- **Browser Navigation**: Use browser back button to return to map
- **Auto-Refresh**: Automatically detects new .mhtml files every 30 seconds

## Setup

1. Create and activate a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run the Flask server:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

**Note**: When you're done, you can deactivate the virtual environment with `deactivate`.

## File Naming Convention

The application expects .mhtml files with the following naming pattern:
```
For sale_ <address> - <number> _ REALTOR.ca.mhtml
```

Example:
```
For sale_ 1428 Fort St, Victoria, British Columbia V8S1Z1 - 995977 _ REALTOR.ca.mhtml
```

The address is extracted from between "For sale_" and the first "-".

## How It Works

1. The backend scans the directory for .mhtml files
2. Extracts addresses from filenames using regex pattern matching
3. Frontend geocodes addresses to get latitude/longitude coordinates
4. Displays pins on the map at the correct locations
5. Clicking "View Details" navigates to the mhtml file
6. Browser back button returns to the map view
7. System checks for new files every 30 seconds

## Notes

- Geocoding uses OpenStreetMap Nominatim (free, no API key required)
- Some addresses may not geocode correctly if they're incomplete or ambiguous
- The map automatically updates when new .mhtml files are added to the folder
- Browser back button works naturally when viewing property details

