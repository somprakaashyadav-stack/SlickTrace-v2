import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Satellite, Navigation2, Users, Shield,
  BarChart3, FlaskConical, Layers, Circle
} from 'lucide-react';

interface SidebarProps {
  darkMode: boolean;
}

interface NavItem {
  id: string;
  path: string;
  label: string;
  icon: React.ReactNode;
  badge?: string;
  badgeColor?: string;
}

const OPS_ITEMS: NavItem[] = [
  { id: 'dashboard', path: '/dashboard', label: 'Tactical GIS Command', icon: <LayoutDashboard className="w-4 h-4" />, badge: '3', badgeColor: 'bg-rose-500' },
  { id: 'sar-studio', path: '/sar-studio', label: 'SAR Studio', icon: <Satellite className="w-4 h-4" /> },
  { id: 'drift-engine', path: '/drift-engine', label: 'Lagrangian Drift Engine', icon: <Navigation2 className="w-4 h-4" /> },
  { id: 'attribution', path: '/attribution', label: '4D Attribution Verifier', icon: <Users className="w-4 h-4" /> },
  { id: 'evidence', path: '/evidence', label: 'Statutory Evidence Vault', icon: <Shield className="w-4 h-4" /> },
];

const ANALYTICS_ITEMS: NavItem[] = [
  { id: 'analytics', path: '/analytics', label: 'Surveillance Analytics', icon: <BarChart3 className="w-4 h-4" />, badge: '14d', badgeColor: 'bg-slate-600' },
  { id: 'edge-lab', path: '/edge-lab', label: 'Edge Inference Lab', icon: <FlaskConical className="w-4 h-4" />, badge: 'WASM', badgeColor: 'bg-cyan-600' },
];

const TELEMETRY_FEEDS = [
  { label: 'PostGIS Cluster', sub: 'Healthy', live: true },
  { label: 'OpenDrift Celery', sub: 'Idle (0 jobs)', live: true },
  { label: 'CMEMS Ocean Mesh', sub: 'Active (0.25°)', live: true },
];

export const Sidebar: React.FC<SidebarProps> = ({ darkMode }) => {
  const location = useLocation();

  const renderItem = (item: NavItem) => {
    const isActive = location.pathname.startsWith(item.path);
    return (
      <Link
        key={item.id}
        to={item.path}
        className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left transition-all group ${
          isActive
            ? (darkMode ? 'bg-[#0284C7]/20 text-[#0284C7] border border-[#0284C7]/30' : 'bg-[#0369A1]/10 text-[#0369A1] border border-[#0369A1]/20')
            : (darkMode ? 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#0F172A]/50' : 'text-[#64748B] hover:text-[#0F172A] hover:bg-[#F1F5F9]/50')
        }`}
      >
        <span className={isActive ? (darkMode ? 'text-[#0284C7]' : 'text-[#0369A1]') : (darkMode ? 'text-[#64748B] group-hover:text-[#94A3B8]' : 'text-[#94A3B8] group-hover:text-[#64748B]')}>
          {item.icon}
        </span>
        <span className="text-[11px] font-medium flex-1 leading-tight">{item.label}</span>
        {item.badge && (
          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${item.badgeColor} text-white`}>
            {item.badge}
          </span>
        )}
      </Link>
    );
  };

  return (
    <div className={`w-[240px] shrink-0 border-r flex flex-col h-full ${darkMode ? 'bg-[#070B12] border-[#1E293B]' : 'bg-[#F8FAFC] border-[#E2E8F0]'}`}>
      {/* Navigation */}
      <div className="flex-1 overflow-y-auto px-2 py-4 space-y-6 mt-14 custom-scrollbar">
        {/* Operations */}
        <div>
          <p className={`text-[10px] font-bold uppercase tracking-widest px-2 mb-3 ${darkMode ? 'text-[#64748B]' : 'text-[#94A3B8]'}`}>Operations</p>
          <div className="space-y-1">
            {OPS_ITEMS.map(renderItem)}
          </div>
        </div>

        {/* Analytics */}
        <div>
          <p className={`text-[10px] font-bold uppercase tracking-widest px-2 mb-3 ${darkMode ? 'text-[#64748B]' : 'text-[#94A3B8]'}`}>Analysis</p>
          <div className="space-y-1">
            {ANALYTICS_ITEMS.map(renderItem)}
          </div>
        </div>
      </div>

      {/* Telemetry Feed / System Microservices Dock */}
      <div className={`px-4 py-4 border-t ${darkMode ? 'border-[#1E293B]' : 'border-[#E2E8F0]'}`}>
        <p className={`text-[10px] font-bold uppercase tracking-widest mb-3 ${darkMode ? 'text-[#64748B]' : 'text-[#94A3B8]'}`}>System Health</p>
        <div className="space-y-2.5">
          {TELEMETRY_FEEDS.map((feed, i) => (
            <div key={i} className="flex items-center gap-2">
              <Circle className={`w-2 h-2 ${feed.live ? 'text-[#10B981] fill-[#10B981]' : 'text-[#64748B] fill-[#64748B]'}`} />
              <div className="flex flex-col">
                <p className={`text-[10px] font-medium leading-tight ${darkMode ? 'text-[#F8FAFC]' : 'text-[#0F172A]'}`}>{feed.label}</p>
                <p className={`text-[9px] leading-tight mt-0.5 ${darkMode ? 'text-[#94A3B8]' : 'text-[#64748B]'}`}>{feed.sub}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
