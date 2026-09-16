import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Satellite, Navigation2, Users, Shield,
  BarChart3, FlaskConical
} from 'lucide-react';

interface HorizontalNavProps {
  darkMode: boolean;
}

interface NavItem {
  id: string;
  path: string;
  label: string;
  icon: React.ReactNode;
}

const TABS: NavItem[] = [
  { id: 'dashboard', path: '/dashboard', label: 'Command Map (GIS)', icon: <LayoutDashboard className="w-3.5 h-3.5" /> },
  { id: 'sar-studio', path: '/sar-studio', label: 'Sensor Analysis & Look-Alike Filter', icon: <Satellite className="w-3.5 h-3.5" /> },
  { id: 'drift-engine', path: '/drift-engine', label: 'Lagrangian Drift Simulator', icon: <Navigation2 className="w-3.5 h-3.5" /> },
  { id: 'attribution', path: '/attribution', label: '4D AIS Attribution & Physics Sweeps', icon: <Users className="w-3.5 h-3.5" /> },
  { id: 'evidence', path: '/evidence', label: 'Legal Evidence Vault', icon: <Shield className="w-3.5 h-3.5" /> },
  { id: 'analytics', path: '/analytics', label: 'EEZ Analytics', icon: <BarChart3 className="w-3.5 h-3.5" /> },
  { id: 'edge-lab', path: '/edge-lab', label: 'Edge Inference Lab', icon: <FlaskConical className="w-3.5 h-3.5" /> },
];

export const HorizontalNav: React.FC<HorizontalNavProps> = ({ darkMode }) => {
  const location = useLocation();

  return (
    <div className={`h-10 border-b flex items-center px-4 overflow-x-auto custom-scrollbar shrink-0 ${darkMode ? 'bg-[#0F172A] border-[#1E293B]' : 'bg-[#FFFFFF] border-[#E2E8F0]'}`}>
      <div className="flex items-center gap-1">
        {TABS.map(tab => {
          const isActive = location.pathname.startsWith(tab.path);
          return (
            <Link
              key={tab.id}
              to={tab.path}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-t-lg transition-colors whitespace-nowrap border-b-2 ${
                isActive
                  ? (darkMode 
                      ? 'text-[#0284C7] bg-[#0284C7]/10 border-[#0284C7]' 
                      : 'text-[#0369A1] bg-[#0369A1]/10 border-[#0369A1]')
                  : (darkMode
                      ? 'text-[#94A3B8] border-transparent hover:text-[#F8FAFC] hover:bg-[#1E293B]'
                      : 'text-[#64748B] border-transparent hover:text-[#0F172A] hover:bg-[#F1F5F9]')
              }`}
            >
              {tab.icon}
              <span className="text-[11px] font-bold tracking-wide">{tab.label}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
};
