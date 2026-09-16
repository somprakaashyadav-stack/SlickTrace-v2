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
    id: 'INC-01',
    name: 'Mumbai High Offshore Basin',
    oilType: 'Crude Oil',
    location: 'Arabian Sea',
    lat: 18.92,
    lon: 72.35,
    severity: 'HIGH',
    color: '#EF4444',
  },
  {
    id: 'INC-02',
    name: 'Chennai-Ennore Energy Corridor',
    oilType: 'Heavy Bunker Fuel',
    location: 'Bay of Bengal',
    lat: 13.23,
    lon: 80.33,
    severity: 'HIGH',
    color: '#F59E0B',
  },
  {
    id: 'INC-03',
    name: 'Andaman Sea SL-7 Shipping Lane',
    oilType: 'Bilge Waste',
    location: 'Andaman Sea',
    lat: 11.67,
    lon: 92.71,
    severity: 'MEDIUM',
    color: '#10B981',
  },
  {
    id: 'INC-04',
    name: 'Goa Coastal Waters',
    oilType: 'Marine Gas Oil',
    location: 'Arabian Sea',
    lat: 15.38,
    lon: 73.79,
    severity: 'MEDIUM',
    color: '#38BDF8',
  },
];

export const DEMO_METOCEAN: MetoceanData = {
  windSpeed: 4.2,
  windDir: 'WSW',
  currentSpeed: 0.34,
  currentDir: 'ESE',
  lat: 18.92,
  lon: 72.35,
};
