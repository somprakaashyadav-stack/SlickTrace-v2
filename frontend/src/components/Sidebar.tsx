import React, { useState } from 'react';
import {
  LayoutDashboard, Satellite, Navigation2, Users, Shield,
  BarChart3, FlaskConical, ChevronDown, Radio, Layers,
  Circle
} from 'lucide-react';
import { PageType } from '../types/app';

interface SidebarProps {
  activePage: PageType;
  setActivePage: (page: PageType) => void;
}

interface NavItem {
  id: PageType;
  label: string;
  icon: React.ReactNode;
  badge?: string;
  badgeColor?: string;
}

const OPS_ITEMS: NavItem[] = [
  { id: 'dashboard', label: 'Command Dashboard', icon: <LayoutDashboard className="w-4 h-4" />, badge: '3', badgeColor: 'bg-rose-500' },
  { id: 'satellite-studio', label: 'Varuna Satellite Studio', icon: <Satellite className="w-4 h-4" />, badge: 'DRISHTI', badgeColor: 'bg-emerald-600' },
  { id: 'drift-backtracking', label: 'Drift Backtracking', icon: <Navigation2 className="w-4 h-4" /> },
  { id: 'vessel-attribution', label: 'Vessel Attribution', icon: <Users className="w-4 h-4" /> },
  { id: 'evidence-center', label: 'Evidence Center', icon: <Shield className="w-4 h-4" /> },
];

const ANALYTICS_ITEMS: NavItem[] = [
  { id: 'spill-analytics', label: 'Spill Analytics', icon: <BarChart3 className="w-4 h-4" />, badge: '14d', badgeColor: 'bg-slate-600' },
  { id: 'sar-detection-lab', label: 'SAR Detection Lab', icon: <FlaskConical className="w-4 h-4" />, badge: 'NEW', badgeColor: 'bg-cyan-600' },
];

const TELEMETRY_FEEDS = [
  { label: 'MSN / Virtual Earth', sub: 'Aerial Live', live: true },
  { label: 'Esri Hydrographic', sub: 'Nautical Topo', live: true },
  { label: 'OpenSeaMap Aids', sub: 'Seamarks', live: true },
  { label: 'CMEMS Currents', sub: '0.25° Mesh', live: true },
  { label: 'PostGIS / Celery', sub: '4/4 Healthy', live: true },
];

export const Sidebar: React.FC<SidebarProps> = ({ activePage, setActivePage }) => {
  const renderItem = (item: NavItem) => {
    const isActive = activePage === item.id;
    return (
      <button
        key={item.id}
        onClick={() => setActivePage(item.id)}
        className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left transition-all group ${
          isActive
            ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
        }`}
      >
        <span className={isActive ? 'text-cyan-400' : 'text-slate-500 group-hover:text-slate-300'}>
          {item.icon}
        </span>
        <span className="text-[11px] font-medium flex-1 leading-tight">{item.label}</span>
        {item.badge && (
          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${item.badgeColor} text-white`}>
            {item.badge}
          </span>
        )}
      </button>
    );
  };

  return (
    <div className="w-[148px] shrink-0 bg-[#070c16] border-r border-slate-800/60 flex flex-col h-full">
      {/* Logo */}
      <div className="px-3 py-4 border-b border-slate-800/60">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-cyan-500/20 rounded flex items-center justify-center">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div>
            <p className="text-[10px] font-black text-cyan-400 tracking-widest leading-none">SLICKTRACE</p>
            <p className="text-[8px] text-slate-500 tracking-wider leading-none mt-0.5">MARITIME C2</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-4">
        {/* Operations */}
        <div>
          <p className="text-[9px] font-bold text-slate-600 uppercase tracking-widest px-1 mb-2">Operations</p>
          <div className="space-y-0.5">
            {OPS_ITEMS.map(renderItem)}
          </div>
        </div>

        {/* Analytics */}
        <div>
          <p className="text-[9px] font-bold text-slate-600 uppercase tracking-widest px-1 mb-2">Analytics</p>
          <div className="space-y-0.5">
            {ANALYTICS_ITEMS.map(renderItem)}
          </div>
        </div>
      </div>

      {/* Telemetry Feed */}
      <div className="px-2 py-3 border-t border-slate-800/60">
        <p className="text-[9px] font-bold text-slate-600 uppercase tracking-widest px-1 mb-2">Telemetry Feed</p>
        <div className="space-y-1.5">
          {TELEMETRY_FEEDS.map((feed, i) => (
            <div key={i} className="flex items-center justify-between px-1">
              <div>
                <p className="text-[9px] text-slate-400 leading-none">{feed.label}</p>
                <p className="text-[8px] text-slate-600 leading-none mt-0.5">{feed.sub}</p>
              </div>
              <Circle className={`w-1.5 h-1.5 ${feed.live ? 'text-emerald-400 fill-emerald-400' : 'text-slate-600 fill-slate-600'}`} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
