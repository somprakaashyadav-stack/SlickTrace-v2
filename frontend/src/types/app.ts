// App-level types for multi-page navigation and global state

export type PageType =
  | 'dashboard'
  | 'satellite-studio'
  | 'drift-backtracking'
  | 'vessel-attribution'
  | 'evidence-center'
  | 'spill-analytics'
  | 'sar-detection-lab';

export interface Incident {
  id: string;
  name: string;
  oilType: string;
  location: string;
  lat: number;
  lon: number;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  color: string;
}

export interface MetoceanData {
  windSpeed: number;
  windDir: string;
  currentSpeed: number;
  currentDir: string;
  lat: number;
  lon: number;
}

export const DEMO_INCIDENTS: Incident[] = [
  {
    id: 'INC-2026-001',
    name: 'Mumbai High Offshore Basin',
    oilType: 'Crude Oil',
    location: 'Arabian Sea',
    lat: 18.9,
    lon: 72.3,
    severity: 'HIGH',
    color: '#f43f5e',
  },
  {
    id: 'INC-2026-002',
    name: 'Chennai-Ennore Coastal Corridor',
    oilType: 'Heavy Bunker Fuel',
    location: 'Bay of Bengal',
    lat: 13.1,
    lon: 80.3,
    severity: 'HIGH',
    color: '#f59e0b',
  },
  {
    id: 'INC-2026-003',
    name: 'Andaman Sea Shipping Lane 7',
    oilType: 'Oil Bilge Water',
    location: 'Andaman Sea',
    lat: 12.5,
    lon: 93.5,
    severity: 'MEDIUM',
    color: '#38bdf8',
  },
  {
    id: 'INC-2026-004',
    name: 'Goa Coastal Waters',
    oilType: 'Diesel / Marine Gas Oil',
    location: 'Arabian Sea',
    lat: 15.5,
    lon: 73.5,
    severity: 'MEDIUM',
    color: '#a3e635',
  },
];

export const DEMO_METOCEAN: MetoceanData = {
  windSpeed: 4.2,
  windDir: 'WSW',
  currentSpeed: 0.34,
  currentDir: 'ESE',
  lat: 18.9180,
  lon: 72.3508,
};
