import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, ZoomControl, useMap, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { es } from 'date-fns/locale/es';
import L from 'leaflet';
import { Menu, X, Wind, Zap, Car, AlertTriangle, ChevronDown, ChevronUp, Calendar, Database, ChevronLeft, Flame, BarChart2, Check, TrendingUp, Activity, RotateCw, MapPin, AlertCircle, Clock, Skull, CheckCircle } from 'lucide-react';
import IncidentsSummaryModal from './IncidentsSummaryModal';

// Fix for default Leaflet icons in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom Icon generator based on category type
const createCustomIcon = (type, isApproximate = false, isFatal = false, title = "Incidente") => {
    let color = '#002D62'; 
    
    // Iconos SVG Ultra-Simplificados (Blancos)
    const icons = {
        wind: 'M2 12h5m2 0h12m-2-4l2 4-2 4M3 8h12a2 2 0 0 0 2-2 2 2 0 0 0-2-2M3 16h10a2 2 0 0 1 2 2 2 2 0 0 1-2 2',
        car: 'M17 11l2 3v5c0 .6-.4 1-1 1h-1c-.6 0-1-.4-1-1v-1H6v1c0 .6-.4 1-1 1H4c-.6 0-1-.4-1-1v-5l2-3V6c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2v5z M6 13h12',
        fire: 'M12 2c0 0-2 4-2 6s1 3 3 3 2-2 2-3c4 5-1 11-1 11s-5-3-5-7c0-2 2-6 3-10z',
        skull: 'M9 10a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm8 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0zM12 2a8 8 0 0 0-8 8c0 2 1 4 3 6v2a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-2c2-2 3-4 3-6a8 8 0 0 0-8-8z'
    };

    let selectedIcon = icons.car;

    if (isFatal) {
        color = '#4B5563'; 
        selectedIcon = icons.skull;
    } else if (['arboles', 'corte', 'techo', 'viento', 'zonda'].some(k => type.toLowerCase().includes(k))) {
        color = '#EAB308'; 
        selectedIcon = icons.wind;
    } else if (['choque', 'vuelco', 'atropello', 'accidente', 'transito'].some(k => type.toLowerCase().includes(k))) {
        color = '#2563EB'; 
        selectedIcon = icons.car;
    } else if (type.toLowerCase().includes('incendio') || type.toLowerCase().includes('siniestro')) {
        color = '#DC2626'; 
        selectedIcon = icons.fire;
    }

    const svgIcon = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="40" height="40" role="img" aria-label="${title}">
            <!-- Sombra -->
            <path d="M12 22s7-7.75 7-13c0-3.87-3.13-7-7-7s-7 3.13-7 7c0 5.25 7 13 7 13z" fill="black" fill-opacity="0.2" transform="translate(1, 1)" />
            <!-- Pin Cuerpo -->
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="${color}" stroke="white" stroke-width="1.5" />
            <!-- Icono Blanco Centrado -->
            <g transform="translate(6, 4) scale(0.5)" fill="white">
                <path d="${selectedIcon}" stroke="white" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" />
            </g>
            ${isApproximate ? '<circle cx="12" cy="9" r="9" fill="none" stroke="${color}" stroke-width="2" stroke-dasharray="2,2" />' : ''}
        </svg>
    `;

    return L.divIcon({
        className: 'custom-leaflet-icon',
        html: svgIcon,
        iconSize: [40, 40],
        iconAnchor: [20, 40],
        popupAnchor: [0, -40],
        title: title
    });
};

// Helper component to control map view
const MapFocus = ({ incident }) => {
    const map = useMap();
    useEffect(() => {
        if (incident && incident.latitude && incident.longitude) {
            const lat = parseFloat(incident.latitude);
            const lon = parseFloat(incident.longitude);
            if (!isNaN(lat) && !isNaN(lon)) {
                map.flyTo([lat, lon], 14, {
                    duration: 1.5,
                    easeLinearity: 0.25
                });
            }
        }
    }, [incident, map]);
    return null;
};

// Helper function to render styled, premium geocoding precision badges
const renderPrecisionBadge = (incident) => {
    const locType = incident.location_type || 'GEOMETRIC_CENTER';
    const source = incident.source || 'nominatim';
    
    if (locType === 'ROOFTOP') {
        return (
            <span className="flex items-center gap-1 text-[10px] font-extrabold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/50 shadow-sm shadow-emerald-500/5" title="Ubicación exacta del domicilio o edificio">
                <MapPin size={10} className="stroke-[3px]" /> Dirección Exacta
            </span>
        );
    } else if (locType === 'RANGE_INTERPOLATED') {
        return (
            <span className="flex items-center gap-1 text-[10px] font-extrabold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/50 shadow-sm shadow-emerald-500/5" title="Calle y altura aproximada en la cuadra">
                <MapPin size={10} className="stroke-[3px]" /> Calle Precisa
            </span>
        );
    } else if (locType === 'GEOMETRIC_CENTER' && source !== 'fallback') {
        return (
            <span className="flex items-center gap-1 text-[10px] font-extrabold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200/50 shadow-sm shadow-amber-500/5" title="Ubicación a nivel de calle, barrio o intersección">
                <AlertTriangle size={10} className="stroke-[2.5px]" /> Ubicación Aproximada
            </span>
        );
    } else {
        // APPROXIMATE or fallback
        return (
            <span className="flex items-center gap-1 text-[10px] font-extrabold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200/60 shadow-sm" title="Ubicación referencial de la localidad o provincia (sin dirección precisa)">
                <AlertCircle size={10} className="stroke-[2.5px]" /> Ubicación Referencial
            </span>
        );
    }
};

const MapComponent = () => {
    const [incidents, setIncidents] = useState([]);
    // Abrir por defecto en escritorio, cerrado en móvil
    const [sidebarOpen, setSidebarOpen] = useState(() => {
        // Guard against SSR environments
        if (typeof window === 'undefined') return true;
        return window.innerWidth > 768;
    });
    
    // Estados para Filtros
    const [selectedDate, setSelectedDate] = useState(() => {
        const d = new Date();
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    });
    const [visibleTabs, setVisibleTabs] = useState(['wind', 'accident', 'fire']); // Por defecto todos activos
    const [loading, setLoading] = useState(false);
    const [premiumError, setPremiumError] = useState(false);
    const [lastSync, setLastSync] = useState(null);       
    const [selectedIncident, setSelectedIncident] = useState(null);
    const [, setTick] = useState(0);                      // forces re-render every minute for relative time
    const [isProcessingNew, setIsProcessingNew] = useState(false);
    const prevIncidentsCountRef = useRef(0);
    const [premiumModalOpen, setPremiumModalOpen] = useState(false);
    const [modalView, setModalView] = useState('pricing'); // 'pricing' or 'dashboard'
    const [activeDashboardSection, setActiveDashboardSection] = useState('general'); // 'general', 'traffic', 'fire', 'wind'
    const [provinceGeoJSON, setProvinceGeoJSON] = useState(null);
    const [departmentsGeoJSON, setDepartmentsGeoJSON] = useState(null);

    useEffect(() => {
        // Fetch geojson boundaries
        fetch('/geojson/san_juan.json')
            .then(res => res.json())
            .then(data => setProvinceGeoJSON(data))
            .catch(err => console.error("Error loading province geojson:", err));
            
        fetch('/geojson/departamentos-san_juan.json')
            .then(res => res.json())
            .then(data => setDepartmentsGeoJSON(data))
            .catch(err => console.error("Error loading departments geojson:", err));
    }, []);

    const toggleTab = (tab) => {
        setVisibleTabs(prev => {
            return prev.includes(tab) 
                ? prev.filter(t => t !== tab) 
                : [...prev, tab];
        });
    };

    // Filtrar incidentes según el estado de las pestañas
    const filteredIncidents = incidents.filter(incident => {
        const slug = incident.category?.slug;
        const isWind = ['arboles', 'corte', 'techo', 'viento', 'zonda'].some(k => slug?.includes(k));
        const isAccident = ['choque', 'vuelco', 'atropello', 'accidente', 'transito'].some(k => slug?.includes(k));
        const isFire = slug?.includes('incendio') || slug?.includes('siniestro');
        
        return (isWind && visibleTabs.includes('wind')) || 
               (isAccident && visibleTabs.includes('accident')) || 
               (isFire && visibleTabs.includes('fire'));
    });

    // Calcular conteos por pestaña
    const tabCounts = {
        wind: incidents.filter(i => ['arboles', 'corte', 'techo', 'viento', 'zonda'].some(k => i.category?.slug?.includes(k))).length,
        accident: incidents.filter(i => ['choque', 'vuelco', 'atropello', 'accidente', 'transito'].some(k => i.category?.slug?.includes(k))).length,
        fire: incidents.filter(i => i.category?.slug?.includes('incendio') || i.category?.slug?.includes('siniestro')).length
    };

    // Relative time helper — "hace X minutos"
    const relativeTime = (date) => {
        if (!date) return null;
        const diffMs = Date.now() - date.getTime();
        const diffMin = Math.floor(diffMs / 60000);
        if (diffMin < 1) return 'hace unos segundos';
        if (diffMin === 1) return 'hace 1 minuto';
        return `hace ${diffMin} minutos`;
    };

    // Center on entire San Juan Province
    const position = [-30.8654, -68.8895];

    const fetchIncidents = () => {
        // Show loading only on first load (if incidents list is empty)
        if (incidents.length === 0) setLoading(true);
        setPremiumError(false);
        const startTime = Date.now();
        const minDelay = 1000; // minimal visual feedback on first load

        fetch(`/api/incidents?date=${selectedDate}`)
            .then(res => {
                if (res.status === 402) {
                    setPremiumError(true);
                    throw new Error("Premium Required");
                }
                return res.json();
            })
            .then(data => {
                const items = data?.data ?? data;
                const newList = Array.isArray(items) ? items : [];
                const previous = prevIncidentsCountRef.current || 0;

                if (newList.length > previous) {
                    // New incident(s) detected – show processing state
                    setIsProcessingNew(true);
                    setTimeout(() => {
                        setIncidents(newList);
                        prevIncidentsCountRef.current = newList.length;
                        setLastSync(new Date());
                        setIsProcessingNew(false);
                        setLoading(false);
                    }, 3000);
                } else {
                    // No new incidents – just refresh sync time
                    const elapsed = Date.now() - startTime;
                    const remaining = Math.max(0, minDelay - elapsed);
                    setTimeout(() => {
                        setLastSync(new Date());
                        setLoading(false);
                    }, remaining);
                }
            })
            .catch(err => {
                console.error("Error fetching incidents:", err);
                const elapsed = Date.now() - startTime;
                const remaining = Math.max(0, minDelay - elapsed);
                setTimeout(() => {
                    if (!premiumError) setIncidents([]);
                    setLoading(false);
                }, remaining);
            });
    };

    useEffect(() => {
        // Reset counter on date change
        prevIncidentsCountRef.current = incidents.length;
        // Initial load (visible loading if list empty)
        fetchIncidents();
        // Poll every 30 minutes (1800000 ms) silently – UI only updates when new incident detected
        const interval = setInterval(fetchIncidents, 1800000);
        return () => clearInterval(interval);
    }, [selectedDate]);

    // Ticker: re-render every 60s so relative time stays fresh
    useEffect(() => {
        const ticker = setInterval(() => setTick(t => t + 1), 60000);
        return () => clearInterval(ticker);
    }, []);

    const markerRefs = useRef({});

    useEffect(() => {
        if (selectedIncident && markerRefs.current[selectedIncident.id]) {
            const timer = setTimeout(() => {
                if (markerRefs.current[selectedIncident.id]) {
                    markerRefs.current[selectedIncident.id].openPopup();
                }
            }, 200);
            return () => clearTimeout(timer);
        }
    }, [selectedIncident]);

    return (
        <div className="relative w-full h-screen overflow-hidden flex">
            
            {/* Sidebar Toggle Button — dark glass floating pill */}
            {!sidebarOpen && (
                <button
                    onClick={() => setSidebarOpen(true)}
                    className="absolute top-4 left-4 z-[1000] flex items-center gap-2 bg-[#070d19]/85 backdrop-blur-xl border border-white/10 px-3 py-2 rounded-xl shadow-2xl text-white hover:bg-[#0d1627]/90 hover:border-white/20 transition-all duration-200 active:scale-95"
                    style={{ zIndex: 1000 }}
                    aria-label="Abrir menú lateral"
                >
                    <Menu size={18} strokeWidth={2} />
                    <span className="text-[11px] font-bold uppercase tracking-widest text-white/70">Menú</span>
                </button>
            )}

            {/* Collapsible Sidebar — Dark Glassmorphic Operations Center */}
            <div
                className={`absolute top-0 left-0 h-full w-80 backdrop-blur-2xl bg-[#070d19]/90 border-r border-white/[0.07] shadow-[5px_0_40px_rgba(0,0,0,0.6)] transition-transform duration-300 ease-in-out z-[999] flex flex-col overflow-hidden ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
                style={{ zIndex: 999 }}
            >
                {/* ══ HEADER ══ Logo + Close */}
                <div className="relative px-4 pt-5 pb-4 flex items-center justify-between gap-3">
                    {/* Logo — mix-blend-mode:screen removes dark background */}
                    <div className="flex-1 flex items-center justify-start">
                        <img
                            src="/images/logo.png"
                            alt="ZonData Logo"
                            className="h-12 w-auto object-contain"
                            style={{ mixBlendMode: 'screen', filter: 'brightness(1.15) contrast(1.05)' }}
                        />
                    </div>
                    <button
                        onClick={() => setSidebarOpen(false)}
                        className="flex-shrink-0 p-2 rounded-xl bg-white/[0.04] border border-white/[0.07] text-white/40 hover:text-white hover:bg-white/[0.09] hover:border-white/20 transition-all duration-200 active:scale-90"
                        aria-label="Cerrar panel"
                    >
                        <X size={16} strokeWidth={2.5} />
                    </button>
                    {/* Brand accent line */}
                    <div className="absolute bottom-0 left-4 right-4 h-px bg-gradient-to-r from-[#F28C28]/30 via-white/[0.06] to-transparent" />
                </div>

                {/* ══ DATE PICKER ══ */}
                <div className="px-4 py-3 border-b border-white/[0.06]">
                    <div className="relative group">
                        <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none text-[#EAB308]/80 z-10">
                            <Calendar size={14} strokeWidth={2.5} />
                        </div>
                        <DatePicker
                            selected={selectedDate ? new Date(selectedDate + 'T12:00:00') : null}
                            onChange={(date) => {
                                if (date) {
                                    const year = date.getFullYear();
                                    const month = String(date.getMonth() + 1).padStart(2, '0');
                                    const day = String(date.getDate()).padStart(2, '0');
                                    setSelectedDate(`${year}-${month}-${day}`);
                                }
                            }}
                            locale={es}
                            dateFormat="dd/MM/yyyy"
                            maxDate={new Date()}
                            className="w-full bg-white/[0.05] border border-white/[0.10] hover:border-white/20 focus:border-[#EAB308]/40 focus:ring-2 focus:ring-[#EAB308]/10 rounded-xl py-2.5 pl-9 pr-3 text-sm font-bold text-white outline-none transition-all shadow-inner text-center tracking-wider cursor-pointer placeholder:text-white/30"
                            wrapperClassName="w-full"
                            aria-label="Seleccionar fecha de incidentes"
                            calendarClassName="premium-calendar"
                        />
                    </div>
                </div>

                {/* ══ CATEGORY FILTER PILLS ══ */}
                <div className="px-4 py-3 border-b border-white/[0.06]">
                    <div className="flex gap-2">
                        {/* Viento */}
                        <button
                            onClick={() => toggleTab('wind')}
                            className={`flex-1 flex flex-col items-center gap-1 py-2.5 px-1 rounded-xl border transition-all duration-200 active:scale-95 ${
                                visibleTabs.includes('wind')
                                    ? 'bg-[#EAB308]/10 border-[#EAB308]/40 text-[#EAB308] shadow-[0_0_12px_rgba(234,179,8,0.12)]'
                                    : 'bg-white/[0.03] border-white/[0.05] text-white/25 hover:text-white/50 hover:bg-white/[0.05] hover:border-white/10'
                            }`}
                        >
                            <Wind size={16} strokeWidth={2} />
                            <span className="text-[9px] font-black uppercase tracking-wide leading-none">Viento</span>
                            {tabCounts.wind > 0 && (
                                <span className={`text-[9px] font-black px-1.5 py-0.5 rounded-full leading-none ${
                                    visibleTabs.includes('wind') ? 'bg-[#EAB308]/20 text-[#EAB308]' : 'bg-white/10 text-white/30'
                                }`}>{tabCounts.wind}</span>
                            )}
                        </button>
                        {/* Tránsito */}
                        <button
                            onClick={() => toggleTab('accident')}
                            className={`flex-1 flex flex-col items-center gap-1 py-2.5 px-1 rounded-xl border transition-all duration-200 active:scale-95 ${
                                visibleTabs.includes('accident')
                                    ? 'bg-[#2563EB]/10 border-[#2563EB]/40 text-[#60A5FA] shadow-[0_0_12px_rgba(37,99,235,0.12)]'
                                    : 'bg-white/[0.03] border-white/[0.05] text-white/25 hover:text-white/50 hover:bg-white/[0.05] hover:border-white/10'
                            }`}
                        >
                            <Car size={16} strokeWidth={2} />
                            <span className="text-[9px] font-black uppercase tracking-wide leading-none">Tránsito</span>
                            {tabCounts.accident > 0 && (
                                <span className={`text-[9px] font-black px-1.5 py-0.5 rounded-full leading-none ${
                                    visibleTabs.includes('accident') ? 'bg-[#2563EB]/20 text-[#60A5FA]' : 'bg-white/10 text-white/30'
                                }`}>{tabCounts.accident}</span>
                            )}
                        </button>
                        {/* Incendios */}
                        <button
                            onClick={() => toggleTab('fire')}
                            className={`flex-1 flex flex-col items-center gap-1 py-2.5 px-1 rounded-xl border transition-all duration-200 active:scale-95 ${
                                visibleTabs.includes('fire')
                                    ? 'bg-[#DC2626]/10 border-[#DC2626]/40 text-[#F87171] shadow-[0_0_12px_rgba(220,38,38,0.12)]'
                                    : 'bg-white/[0.03] border-white/[0.05] text-white/25 hover:text-white/50 hover:bg-white/[0.05] hover:border-white/10'
                            }`}
                        >
                            <Flame size={16} strokeWidth={2} />
                            <span className="text-[9px] font-black uppercase tracking-wide leading-none">Incendios</span>
                            {tabCounts.fire > 0 && (
                                <span className={`text-[9px] font-black px-1.5 py-0.5 rounded-full leading-none ${
                                    visibleTabs.includes('fire') ? 'bg-[#DC2626]/20 text-[#F87171]' : 'bg-white/10 text-white/30'
                                }`}>{tabCounts.fire}</span>
                            )}
                        </button>
                    </div>
                </div>

                {/* ══ MAIN FEED ══ */}
                <div className="flex-1 min-h-0 flex flex-col">
                    <div className="flex-1 min-h-0 overflow-y-auto px-3 py-3 custom-scrollbar space-y-2">

                        {/* Premium Error Card */}
                        {premiumError && (
                            <div className="mb-2 bg-gradient-to-br from-[#0a1628] to-[#001D40]/80 p-4 rounded-2xl border border-[#F28C28]/20 text-white relative overflow-hidden shadow-xl shadow-black/40">
                                <div className="absolute -top-4 -right-4 text-[#F28C28]/5">
                                    <Database size={80} />
                                </div>
                                <div className="relative z-10">
                                    <div className="flex items-center gap-2 mb-2">
                                        <div className="bg-[#F28C28]/15 border border-[#F28C28]/30 p-1.5 rounded-lg">
                                            <Calendar className="text-[#F28C28]" size={14} />
                                        </div>
                                        <h4 className="font-black text-xs uppercase tracking-widest text-[#F28C28]">Acceso Histórico</h4>
                                    </div>
                                    <p className="text-[11px] text-white/50 leading-relaxed mb-3">
                                        La consulta de datos de más de 30 días requiere una suscripción <b className="text-white/70">ZonData Premium</b>.
                                    </p>
                                    <button
                                        onClick={() => { setModalView('pricing'); setPremiumModalOpen(true); }}
                                        className="w-full bg-gradient-to-r from-[#F28C28] to-[#d97a1d] text-white py-2 rounded-xl text-[11px] font-black uppercase tracking-widest shadow-lg shadow-[#F28C28]/20 hover:shadow-[#F28C28]/30 hover:scale-[1.02] transition-all"
                                    >
                                        Subscribirse ahora
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* LED Sync Status Pill */}
                        {!premiumError && (
                            <div className={`flex items-center justify-between px-3 py-2 rounded-xl border mb-1 transition-all ${
                                loading
                                    ? 'bg-amber-500/[0.07] border-amber-500/20'
                                    : incidents.length > 0
                                        ? 'bg-emerald-500/[0.07] border-emerald-500/20'
                                        : 'bg-white/[0.03] border-white/[0.06]'
                            }`}>
                                <div className="flex items-center gap-2 min-w-0">
                                    <span className="relative flex-shrink-0">
                                        {(isProcessingNew || loading || incidents.length > 0) && (
                                            <span className={`absolute inset-0 rounded-full animate-ping opacity-60 ${
                                                isProcessingNew ? 'bg-blue-400' : loading ? 'bg-amber-400' : 'bg-emerald-400'
                                            }`} />
                                        )}
                                        <span className={`relative flex w-2 h-2 rounded-full ${
                                            isProcessingNew ? 'bg-blue-400' : loading ? 'bg-amber-400' : incidents.length > 0 ? 'bg-emerald-400' : 'bg-white/20'
                                        }`} />
                                    </span>
                                    <div className="min-w-0">
                                        <p className={`text-[10px] font-bold leading-tight truncate ${
                                            isProcessingNew ? 'text-blue-400' : loading ? 'text-amber-400' : incidents.length > 0 ? 'text-emerald-400' : 'text-white/30'
                                        }`}>
                                            {isProcessingNew
                                                ? 'Procesando entrada nueva...'
                                                : loading
                                                    ? 'Buscando entradas...'
                                                    : incidents.length > 0
                                                        ? `${incidents.length} incidente${incidents.length > 1 ? 's' : ''} detectado${incidents.length > 1 ? 's' : ''}`
                                                        : 'Sin incidentes detectados'}
                                        </p>
                                        {(lastSync && !loading && !isProcessingNew) && (
                                            <p className="text-[9px] text-white/20 mt-0.5">Sync: {relativeTime(lastSync)}</p>
                                        )}
                                    </div>
                                </div>
                                <button
                                    onClick={fetchIncidents}
                                    disabled={loading}
                                    className={`p-1.5 rounded-lg transition-all flex-shrink-0 ${
                                        loading ? 'text-amber-400/50 cursor-not-allowed' : 'text-white/20 hover:text-white/60 hover:bg-white/[0.05] active:scale-90'
                                    }`}
                                    title="Recargar"
                                    aria-label="Buscar nuevas entradas"
                                >
                                    <RotateCw size={12} className={loading ? 'animate-spin' : ''} />
                                </button>
                            </div>
                        )}

                        {/* Events Header */}
                        <div className="flex items-center justify-between px-1 mb-1">
                            <h2 className="text-[10px] font-black uppercase tracking-[0.18em] text-white/30">Eventos Activos</h2>
                            <span className="bg-white/10 text-white/50 text-[9px] font-black py-0.5 px-2 rounded-full border border-white/10">
                                {filteredIncidents.length}
                            </span>
                        </div>

                        {/* Incident Cards — Dark Glass */}
                        <div className="space-y-2">
                            {filteredIncidents.map(incident => {
                                const slug = incident.category?.slug || '';
                                const isWind = ['arboles', 'corte', 'techo', 'viento', 'zonda'].some(k => slug.includes(k));
                                const isAccident = ['choque', 'vuelco', 'atropello', 'accidente', 'transito'].some(k => slug.includes(k));
                                const isFire = slug.includes('incendio') || slug.includes('siniestro');
                                const isFatal = incident.is_fatal;

                                let accentColor = 'rgba(255,255,255,0.12)';
                                let glowColor = 'transparent';
                                let accentText = 'text-white/40';
                                if (isFatal) {
                                    accentColor = 'rgba(239,68,68,0.25)';
                                    glowColor = '0 0 16px rgba(239,68,68,0.12)';
                                    accentText = 'text-red-400';
                                } else if (isWind) {
                                    accentColor = 'rgba(234,179,8,0.18)';
                                    glowColor = '0 0 14px rgba(234,179,8,0.08)';
                                    accentText = 'text-yellow-400';
                                } else if (isAccident) {
                                    accentColor = 'rgba(37,99,235,0.18)';
                                    glowColor = '0 0 14px rgba(37,99,235,0.08)';
                                    accentText = 'text-blue-400';
                                } else if (isFire) {
                                    accentColor = 'rgba(220,38,38,0.18)';
                                    glowColor = '0 0 14px rgba(220,38,38,0.08)';
                                    accentText = 'text-red-400';
                                }

                                const isSelected = selectedIncident?.id === incident.id;

                                // Format event time
                                let timeStr = '';
                                if (incident.event_date) {
                                    try {
                                        const d = new Date(incident.event_date);
                                        timeStr = d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
                                    } catch {}
                                }

                                const localityName = incident.locality?.name || incident.department?.name || '';

                                return (
                                    <div
                                        key={incident.id}
                                        onClick={() => setSelectedIncident(incident)}
                                        className={`relative rounded-2xl border cursor-pointer transition-all duration-200 p-3.5 ${
                                            isSelected
                                                ? 'border-white/25 bg-white/[0.09] scale-[1.01] shadow-lg'
                                                : 'border-white/[0.06] bg-white/[0.03] hover:bg-white/[0.07] hover:border-white/15 hover:-translate-y-0.5 active:scale-[0.98]'
                                        }`}
                                        style={{
                                            boxShadow: isSelected ? `0 0 0 1px ${accentColor}, ${glowColor}` : glowColor
                                        }}
                                    >
                                        {/* Top row: category accent bar + time + locality */}
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="flex items-center gap-1.5">
                                                {/* Color accent dot */}
                                                <span
                                                    className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                                                    style={{ background: accentColor.replace('0.18', '0.9').replace('0.25', '1') }}
                                                />
                                                <span className={`text-[9px] font-black uppercase tracking-widest ${accentText}`}>
                                                    {isFatal ? 'Fatal' : isWind ? 'Viento' : isAccident ? 'Tránsito' : isFire ? 'Incendio' : 'Evento'}
                                                </span>
                                                {isFatal && <Skull size={9} className="text-red-400" />}
                                            </div>
                                            <div className="flex items-center gap-1 text-white/25">
                                                {timeStr && (
                                                    <span className="flex items-center gap-0.5 text-[9px]">
                                                        <Clock size={9} />
                                                        {timeStr}
                                                    </span>
                                                )}
                                            </div>
                                        </div>

                                        {/* Title */}
                                        <h3 className="text-white/85 font-bold text-[12px] leading-tight mb-2">
                                            {incident.title}
                                        </h3>

                                        {/* Bottom row: locality + precision badge */}
                                        <div className="flex items-center justify-between gap-2">
                                            {localityName && (
                                                <span className="flex items-center gap-1 text-[9px] text-white/30 font-semibold truncate">
                                                    <MapPin size={9} className="flex-shrink-0" />
                                                    {localityName}
                                                </span>
                                            )}
                                            {incident.location_type === 'ROOFTOP' && (
                                                <span className="text-[8px] font-black text-emerald-400/80 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded-full whitespace-nowrap ml-auto">Exacto</span>
                                            )}
                                            {incident.location_type === 'RANGE_INTERPOLATED' && (
                                                <span className="text-[8px] font-black text-emerald-300/70 bg-emerald-500/[0.07] border border-emerald-500/15 px-1.5 py-0.5 rounded-full whitespace-nowrap ml-auto">Calle</span>
                                            )}
                                            {(incident.location_type === 'GEOMETRIC_CENTER' && incident.source !== 'fallback') && (
                                                <span className="text-[8px] font-black text-amber-400/70 bg-amber-500/[0.07] border border-amber-500/15 px-1.5 py-0.5 rounded-full whitespace-nowrap ml-auto">~Aprox</span>
                                            )}
                                            {(!incident.location_type || incident.source === 'fallback') && (
                                                <span className="text-[8px] font-black text-white/20 bg-white/[0.04] border border-white/10 px-1.5 py-0.5 rounded-full whitespace-nowrap ml-auto">Ref.</span>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Empty State */}
                        {filteredIncidents.length === 0 && !loading && !premiumError && (
                            <div className="text-center py-10">
                                <div className="w-10 h-10 rounded-full bg-white/[0.04] border border-white/[0.07] flex items-center justify-center mx-auto mb-3">
                                    <CheckCircle size={18} className="text-white/15" />
                                </div>
                                <p className="text-[11px] text-white/25 font-semibold">Sin incidentes</p>
                                <p className="text-[10px] text-white/15 mt-0.5">para la fecha seleccionada</p>
                            </div>
                        )}
                    </div>

                    {/* ══ BOTTOM CTAs ══ */}
                    <div className="px-3 py-3 border-t border-white/[0.06] flex flex-col gap-2">
                        {/* Premium CTA */}
                        <button
                            className="w-full group relative overflow-hidden bg-gradient-to-br from-[#002D62]/80 to-[#001228]/90 border border-[#F28C28]/20 hover:border-[#F28C28]/40 p-3 rounded-xl shadow-xl shadow-black/40 transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
                            onClick={() => { window.location.href = '/dashboard_premium'; }}
                        >
                            <div className="absolute inset-0 bg-gradient-to-r from-[#F28C28]/0 via-[#F28C28]/5 to-[#F28C28]/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                            <div className="absolute top-0 right-0 p-2 opacity-5 group-hover:opacity-10 transition-opacity">
                                <Database size={36} className="text-[#F28C28]" />
                            </div>
                            <div className="relative z-10 flex items-center justify-between w-full gap-2">
                                <div className="flex flex-col items-start text-left">
                                    <span className="text-[8px] font-black text-[#F28C28]/70 uppercase tracking-[0.18em] leading-none mb-1">Acceso Premium</span>
                                    <h4 className="text-white/80 font-bold text-[11px] leading-none">Dataset Completo</h4>
                                </div>
                                <div className="flex items-center text-white text-[9px] font-black uppercase tracking-wider bg-gradient-to-r from-[#F28C28] to-[#d97a1d] py-1.5 px-2.5 rounded-lg shadow-md shadow-[#F28C28]/20 shrink-0 whitespace-nowrap">
                                    Suscribirse
                                </div>
                            </div>
                        </button>

                        {/* Public Dashboard CTA */}
                        <button
                            onClick={() => { window.location.href = '/dashboard_public'; }}
                            className="w-full bg-white/[0.04] hover:bg-white/[0.08] text-white/50 hover:text-white/70 font-bold py-2 rounded-xl text-[10px] uppercase tracking-wider border border-white/[0.07] hover:border-white/15 transition-all duration-200 hover:scale-[1.01] active:scale-[0.99] flex items-center justify-center gap-1.5 cursor-pointer"
                        >
                            <BarChart2 size={12} className="text-[#F28C28]/60" />
                            Estadísticas Públicas
                        </button>
                    </div>
                </div>
            </div>

            {/* Map Area */}
            <div className="flex-1 h-full relative z-0">
                <MapContainer center={position} zoom={8} className="w-full h-full custom-map-cursor" zoomControl={false}>
                    <MapFocus incident={selectedIncident} />
                    {/* Position zoom control on the right to avoid sidebar overlap */}
                    <ZoomControl position="bottomright" />
                    
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                    />
                    
                    {/* Capas GeoJSON de San Juan */}
                    {provinceGeoJSON && (
                        <GeoJSON
                            data={provinceGeoJSON}
                            interactive={false}
                            style={{
                                color: '#002D62',
                                weight: 1.5,
                                opacity: 0.55,
                                fillOpacity: 0
                            }}
                        />
                    )}
                    {departmentsGeoJSON && (
                        <GeoJSON
                            data={departmentsGeoJSON}
                            interactive={false}
                            style={{
                                color: '#002D62',
                                weight: 0.8,
                                opacity: 0.3,
                                fillOpacity: 0,
                                dashArray: '6, 8'
                            }}
                        />
                    )}
                    
                    {filteredIncidents.map(incident => (
                        <Marker 
                            ref={(el) => {
                                if (el) {
                                    markerRefs.current[incident.id] = el;
                                } else {
                                    delete markerRefs.current[incident.id];
                                }
                            }}
                            key={incident.id} 
                            position={[incident.latitude, incident.longitude]}
                            icon={createCustomIcon(incident.category?.slug || '', incident.is_approximate, incident.is_fatal, incident.title)}
                        >
                            <Popup className="custom-popup">
                                <div className="p-1.5 min-w-[220px] max-w-[265px]">
                                    <div className="flex justify-between items-start mb-2 gap-2">
                                        <span className="inline-block px-2 py-0.5 bg-[#002D62] text-white text-[9px] font-black rounded uppercase tracking-wider">
                                            {incident.category?.name || 'Evento'}
                                        </span>
                                        {renderPrecisionBadge(incident)}
                                    </div>
                                    
                                    <h3 className="font-bold text-xs text-gray-800 leading-snug mb-2">{incident.title}</h3>
                                    
                                    {/* Etiquetas de Siniestro (Movilidades e Gravedad) */}
                                    <div className="flex flex-wrap gap-1 mb-2">
                                        {/* Severidad */}
                                        {incident.is_fatal ? (
                                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-red-50 text-red-700 border border-red-100 text-[9px] font-black uppercase tracking-wide">
                                                💀 Fatal
                                            </span>
                                        ) : (
                                            ['choque', 'vuelco', 'atropello', 'accidente'].includes(incident.category?.slug) && (
                                                <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-100 text-[9px] font-black uppercase tracking-wide">
                                                    🩹 Lesionados
                                                </span>
                                            )
                                        )}

                                        {/* Vehículos Involucrados */}
                                        {incident.has_car && (
                                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-100 text-[9px] font-bold">
                                                🚗 Auto
                                            </span>
                                        )}
                                        {incident.has_pickup && (
                                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-teal-50 text-teal-700 border border-teal-100 text-[9px] font-bold">
                                                🛻 Camioneta
                                            </span>
                                        )}
                                        {incident.has_utility && (
                                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-cyan-50 text-cyan-700 border border-cyan-100 text-[9px] font-bold">
                                                🚐 Utilitario
                                            </span>
                                        )}
                                        {incident.has_motorcycle && (
                                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-100 text-[9px] font-bold">
                                                🏍️ Moto
                                            </span>
                                        )}
                                        {incident.has_truck && (
                                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-orange-50 text-orange-700 border border-orange-100 text-[9px] font-bold">
                                                🚛 Camión
                                            </span>
                                        )}
                                        {incident.has_bus && (
                                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-100 text-[9px] font-bold">
                                                🚌 Colectivo
                                            </span>
                                        )}
                                        {incident.has_pedestrian && (
                                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-100 text-[9px] font-bold">
                                                🚶 Peatón
                                            </span>
                                        )}
                                        {incident.has_bicycle && (
                                            <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-100 text-[9px] font-bold">
                                                🚲 Bicicleta
                                            </span>
                                        )}
                                    </div>

                                    {incident.victim_names && (
                                        <div className="flex items-start gap-1 my-2 px-1.5 py-1 bg-gray-50 border border-gray-150 rounded text-[9px] text-gray-700 leading-normal">
                                            <svg className="w-3.5 h-3.5 flex-shrink-0 text-red-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                                            </svg>
                                            <div className="min-w-0">
                                                <span className="text-gray-400 block text-[8px] uppercase tracking-wider font-black leading-none mb-0.5">Personas</span>
                                                <strong className="text-gray-800 font-bold">{incident.victim_names}</strong>
                                            </div>
                                        </div>
                                    )}

                                    <div className="text-[10px] border-t pt-2 mt-2">
                                        Visto en: <a href={incident.source_url} target="_blank" rel="noreferrer" className="text-blue-500 font-bold hover:underline">{incident.source_name}</a>
                                        <br/>
                                        <span className="text-gray-400">{new Date(incident.event_date).toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' })}</span>
                                        <div className="flex justify-between items-center text-[9px] text-gray-400 mt-1.5 pt-1 bg-gray-50 px-1.5 py-0.5 rounded border border-gray-100">
                                            <span>Vía: <span className="font-semibold text-gray-500 uppercase">{incident.source || 'nominatim'}</span></span>
                                            <span>Precisión: <span className="font-semibold text-gray-500 uppercase">{incident.location_type || 'GEOMETRIC_CENTER'}</span></span>
                                        </div>
                                    </div>
                                </div>
                            </Popup>
                        </Marker>
                    ))}
                </MapContainer>
            </div>
            
            {/* Overlay for mobile when sidebar is open */}
            {sidebarOpen && (
                <div 
                    className="md:hidden fixed inset-0 bg-black/20 z-[998]"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Modal de Resumen y Notificaciones (Inferior Izquierda) */}
            <IncidentsSummaryModal onFocusIncident={(incident) => {
                if (incident.latitude && incident.longitude) {
                    setSelectedIncident(incident);
                }
            }} />

            {/* Modal Premium e Información */}
            {premiumModalOpen && (
                <div className="fixed inset-0 bg-black/70 backdrop-blur-md z-[9999] flex items-center justify-center p-4 md:p-6 select-none">
                    <div className="bg-[#0B1528] text-white rounded-3xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col border border-white/10 relative">
                        {/* Header decorativo con degradado */}
                        <div className="bg-[#002D62] p-6 relative border-b border-white/5">
                            <button 
                                onClick={() => setPremiumModalOpen(false)}
                                className="absolute top-4 right-4 text-gray-400 hover:text-white bg-white/5 hover:bg-white/10 p-2 rounded-full transition-all"
                            >
                                <X size={20} />
                            </button>
                            <span className="text-[10px] font-bold text-[#F28C28] uppercase tracking-[0.25em]">Acceso e Información</span>
                            <h2 className="text-2xl font-black mt-1">Portal de Datos ZonData</h2>
                            
                            {/* Selector de Pestañas */}
                            <div className="flex gap-2 mt-5 bg-[#090F1C] p-1.5 rounded-xl border border-white/10 max-w-md">
                                <button
                                    onClick={() => setModalView('pricing')}
                                    className={`flex-1 py-2 px-4 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${modalView === 'pricing' ? 'bg-[#F28C28] text-white shadow-lg' : 'text-gray-300 hover:text-white hover:bg-white/5'}`}
                                >
                                    <Database size={14} />
                                    Acceso Premium (Planes)
                                </button>
                                <button
                                    onClick={() => setModalView('dashboard')}
                                    className={`flex-1 py-2 px-4 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 ${modalView === 'dashboard' ? 'bg-[#F28C28] text-white shadow-lg' : 'text-gray-300 hover:text-white hover:bg-white/5'}`}
                                >
                                    <BarChart2 size={14} />
                                    Acceso Público (Dashboard)
                                </button>
                            </div>
                        </div>

                        {/* Contenido Dinámico */}
                        <div className="flex-1 overflow-y-auto p-6 md:p-8 bg-[#090F1C] custom-scrollbar">
                            {modalView === 'pricing' ? (
                                <div className="space-y-6">
                                    <div className="text-center max-w-xl mx-auto mb-8">
                                        <h3 className="text-lg font-bold text-white">Elige el plan ideal para tu análisis</h3>
                                        <p className="text-xs text-gray-400 mt-1">Accede al histórico ilimitado de incidentes en San Juan, herramientas de exportación avanzada y alertas automáticas.</p>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                        {/* Plan Básico */}
                                        <div className="bg-[#111A2E] border border-white/5 rounded-2xl p-6 flex flex-col justify-between hover:border-[#F28C28]/30 transition-all text-left">
                                            <div>
                                                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Mensual</span>
                                                <h4 className="text-lg font-black text-white mt-1">Plan Básico</h4>
                                                <div className="mt-4 flex items-baseline gap-1">
                                                    <span className="text-3xl font-black text-white">$1.900</span>
                                                    <span className="text-xs text-gray-400">/ mes</span>
                                                </div>
                                                <ul className="mt-6 space-y-3 text-xs text-gray-300">
                                                    <li className="flex items-center gap-2">
                                                        <Check size={14} className="text-emerald-500 shrink-0" />
                                                        Histórico de 90 días
                                                    </li>
                                                    <li className="flex items-center gap-2">
                                                        <Check size={14} className="text-emerald-500 shrink-0" />
                                                        Filtros de fechas avanzados
                                                    </li>
                                                    <li className="flex items-center gap-2">
                                                        <Check size={14} className="text-emerald-500 shrink-0" />
                                                        1 Alerta personalizada
                                                    </li>
                                                </ul>
                                            </div>
                                            <button className="w-full mt-8 bg-white/5 hover:bg-white/10 text-white font-bold py-2.5 rounded-xl text-xs transition-colors border border-white/10">
                                                Seleccionar Plan
                                            </button>
                                        </div>

                                        {/* Plan Pro */}
                                        <div className="bg-[#15223F] border-2 border-[#F28C28] rounded-2xl p-6 flex flex-col justify-between relative shadow-xl shadow-[#F28C28]/5 hover:scale-[1.02] transition-transform text-left">
                                            <span className="absolute top-0 right-6 -translate-y-1/2 bg-[#F28C28] text-white text-[9px] font-black uppercase tracking-widest py-1 px-3 rounded-full shadow-lg">
                                                Recomendado
                                            </span>
                                            <div>
                                                <span className="text-[10px] font-bold text-[#F28C28] uppercase tracking-widest">Anual</span>
                                                <h4 className="text-lg font-black text-white mt-1">Plan Profesional</h4>
                                                <div className="mt-4 flex items-baseline gap-1">
                                                    <span className="text-3xl font-black text-white">$14.900</span>
                                                    <span className="text-xs text-gray-400">/ año</span>
                                                </div>
                                                <ul className="mt-6 space-y-3 text-xs text-gray-300">
                                                    <li className="flex items-center gap-2">
                                                        <Check size={14} className="text-[#F28C28] shrink-0" />
                                                        Histórico completo (ilimitado)
                                                    </li>
                                                    <li className="flex items-center gap-2">
                                                        <Check size={14} className="text-[#F28C28] shrink-0" />
                                                        Exportación en CSV y JSON
                                                    </li>
                                                    <li className="flex items-center gap-2">
                                                        <Check size={14} className="text-[#F28C28] shrink-0" />
                                                        Alertas SMS y WhatsApp ilimitadas
                                                    </li>
                                                    <li className="flex items-center gap-2">
                                                        <Check size={14} className="text-[#F28C28] shrink-0" />
                                                        Acceso prioritario a nuevos datos
                                                    </li>
                                                </ul>
                                            </div>
                                            <button className="w-full mt-8 bg-[#F28C28] text-white font-bold py-2.5 rounded-xl text-xs transition-transform hover:brightness-110 shadow-lg shadow-[#F28C28]/20">
                                                Comenzar Pro
                                            </button>
                                        </div>

                                        {/* Plan Enterprise */}
                                        <div className="bg-[#111A2E] border border-white/5 rounded-2xl p-6 flex flex-col justify-between hover:border-[#F28C28]/30 transition-all text-left">
                                            <div>
                                                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Corporativo</span>
                                                <h4 className="text-lg font-black text-white mt-1">Institucional</h4>
                                                <div className="mt-4 flex items-baseline gap-1">
                                                    <span className="text-2xl font-black text-white">Consultar</span>
                                                </div>
                                                <ul className="mt-6 space-y-3 text-xs text-gray-300">
                                                    <li className="flex items-center gap-2">
                                                        <Check size={14} className="text-emerald-500 shrink-0" />
                                                        Integración vía API REST
                                                    </li>
                                                    <li className="flex items-center gap-2">
                                                        <Check size={14} className="text-emerald-500 shrink-0" />
                                                        Múltiples credenciales de acceso
                                                    </li>
                                                    <li className="flex items-center gap-2">
                                                        <Check size={14} className="text-emerald-500 shrink-0" />
                                                        Soporte técnico 24/7 dedicado
                                                    </li>
                                                </ul>
                                            </div>
                                            <button className="w-full mt-8 bg-white/5 hover:bg-white/10 text-white font-bold py-2.5 rounded-xl text-xs transition-colors border border-white/10">
                                                Contactar Soporte
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-6">
                                    {/* Cabecera del Dashboard */}
                                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#111A2E] p-5 rounded-2xl border border-white/5 text-left animate-fadeIn">
                                        <div>
                                            <span className="bg-[#2563EB]/20 text-blue-400 text-[10px] font-bold uppercase tracking-widest py-1 px-2.5 rounded-md">
                                                Dashboard Público
                                            </span>
                                            <h3 className="text-lg font-black mt-2">Estadísticas y Analíticas Generales (Últimos 30 días)</h3>
                                            <p className="text-xs text-gray-400 mt-1">Visualización interactiva de incidentes reportados en tiempo real en la provincia de San Juan.</p>
                                        </div>
                                        <div className="bg-[#F28C28]/10 text-[#F28C28] text-xs font-bold py-2 px-4 rounded-xl border border-[#F28C28]/20 flex items-center gap-2 shrink-0">
                                            <Activity size={14} className="animate-pulse" />
                                            Últimos 30 días
                                        </div>
                                    </div>

                                    {/* Selector de Categorías del Dashboard */}
                                    <div className="flex flex-wrap gap-2 bg-[#111A2E] p-2 rounded-2xl border border-white/5">
                                        <button
                                            onClick={() => setActiveDashboardSection('general')}
                                            className={`py-2 px-4 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${activeDashboardSection === 'general' ? 'bg-[#002D62] text-white border border-white/10 shadow-lg shadow-[#002D62]/40' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                                        >
                                            <Database size={13} />
                                            General (Todos)
                                        </button>
                                        <button
                                            onClick={() => setActiveDashboardSection('traffic')}
                                            className={`py-2 px-4 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${activeDashboardSection === 'traffic' ? 'bg-[#2563EB] text-white shadow-lg shadow-[#2563EB]/40' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                                        >
                                            <Car size={13} />
                                            Tránsito y Choques
                                        </button>
                                        <button
                                            onClick={() => setActiveDashboardSection('fire')}
                                            className={`py-2 px-4 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${activeDashboardSection === 'fire' ? 'bg-[#DC2626] text-white shadow-lg shadow-[#DC2626]/40' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                                        >
                                            <Flame size={13} />
                                            Incendios
                                        </button>
                                        <button
                                            onClick={() => setActiveDashboardSection('wind')}
                                            className={`py-2 px-4 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${activeDashboardSection === 'wind' ? 'bg-[#F28C28] text-white shadow-lg shadow-[#F28C28]/40' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                                        >
                                            <Wind size={13} />
                                            Viento y Clima
                                        </button>
                                    </div>

                                    {/* Contadores Dinámicos según Sección */}
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-fadeIn">
                                        {activeDashboardSection === 'general' && (
                                            <>
                                                <div className="bg-[#111A2E] p-4 rounded-xl border border-white/5 text-left">
                                                    <span className="text-[10px] text-gray-400 uppercase font-bold">Total Incidentes</span>
                                                    <h4 className="text-2xl font-black mt-1 text-[#F28C28]">45</h4>
                                                    <span className="text-[9px] text-emerald-500 flex items-center gap-1 mt-1 font-bold">
                                                        <TrendingUp size={10} /> +12% este mes
                                                    </span>
                                                </div>
                                                <div className="bg-[#111A2E] p-4 rounded-xl border border-white/5 text-left">
                                                    <span className="text-[10px] text-gray-400 uppercase font-bold">Mayor Incidencia</span>
                                                    <h4 className="text-xl font-black mt-2 text-white truncate">Incendios</h4>
                                                    <span className="text-[9px] text-red-400 font-bold block mt-1">58% de eventos totales</span>
                                                </div>
                                                <div className="bg-[#111A2E] p-4 rounded-xl border border-white/5 text-left">
                                                    <span className="text-[10px] text-gray-400 uppercase font-bold">Zona Crítica</span>
                                                    <h4 className="text-xl font-black mt-2 text-white truncate">Sarmiento</h4>
                                                    <span className="text-[9px] text-gray-400 block mt-1">Dpto. Sarmiento</span>
                                                </div>
                                                <div className="bg-[#111A2E] p-4 rounded-xl border border-white/5 text-left">
                                                    <span className="text-[10px] text-gray-400 uppercase font-bold">Prom. Respuesta</span>
                                                    <h4 className="text-2xl font-black mt-1 text-white">14 min</h4>
                                                    <span className="text-[9px] text-emerald-500 font-bold block mt-1">Óptimo provincial</span>
                                                </div>
                                            </>
                                        )}
                                        {activeDashboardSection === 'traffic' && (
                                            <>
                                                <div className="bg-[#111A2E] p-4 rounded-xl border border-[#2563EB]/20 text-left">
                                                    <span className="text-[10px] text-gray-400 uppercase font-bold">Total Accidentes</span>
                                                    <h4 className="text-2xl font-black mt-1 text-[#2563EB]">12</h4>
                                                    <span className="text-[9px] text-amber-500 font-bold block mt-1">Últimos 30 días</span>
                                                </div>
                                                <div className="bg-[#111A2E] p-4 rounded-xl border border-[#2563EB]/20 text-left">
                                                    <span className="text-[10px] text-gray-400 uppercase font-bold">Índice Fatalidad</span>
                                                    <h4 className="text-2xl font-black mt-1 text-white">0%</h4>
                                                    <span className="text-[9px] text-emerald-500 font-bold block mt-1">Sin fallecidos</span>
                                                </div>
                                                <div className="bg-[#111A2E] p-4 rounded-xl border border-[#2563EB]/20 text-left">
                                                    <span className="text-[10px] text-gray-400 uppercase font-bold">Horario Crítico</span>
                                                    <h4 className="text-xl font-black mt-2 text-white truncate">18-20 hs</h4>
                                                    <span className="text-[9px] text-gray-400 block mt-1">Retorno laboral</span>
                                                </div>
                                                <div className="bg-[#111A2E] p-4 rounded-xl border border-[#2563EB]/20 text-left">
                                                    <span className="text-[10px] text-gray-400 uppercase font-bold">Ruta Conflictiva</span>
                                                    <h4 className="text-xl font-black mt-2 text-white truncate">Ruta 40</h4>
                                                    <span className="text-[9px] text-amber-400 font-bold block mt-1">Acceso Sur</span>
                                                </div>
                                            </>
                                        )}
                                        {activeDashboardSection === 'fire' && (
                                            <>
                                                <div className="bg-[#111A2E] p-4 rounded-xl border border-[#DC2626]/20 text-left">
                                                    <span className="text-[10px] text-gray-400 uppercase font-bold">Total Incendios</span>
                                                    <h4 className="text-2xl font-black mt-1 text-[#DC2626]">26</h4>
                                                    <span className="text-[9px] text-red-500 font-bold block mt-1">Últimos 30 días</span>
                                                </div>
                                                <div className="bg-[#111A2E] p-4 rounded-xl border border-[#DC2626]/20 text-left">
                                                    <span className="text-[10px] text-gray-400 uppercase font-bold">Foco Común</span>
                                                    <h4 className="text-xl font-black mt-2 text-white truncate">Pastizales</h4>
                                                    <span className="text-[9px] text-red-400 font-bold block mt-1">75% de los focos</span>
                                                </div>
                                                <div className="bg-[#111A2E] p-4 rounded-xl border border-[#DC2626]/20 text-left">
                                                    <span className="text-[10px] text-gray-400 uppercase font-bold">Área Afectada</span>
                                                    <h4 className="text-xl font-black mt-2 text-white truncate">14.5 Ha</h4>
                                                    <span className="text-[9px] text-gray-400 block mt-1">Zonas rurales</span>
                                                </div>
                                                <div className="bg-[#111A2E] p-4 rounded-xl border border-[#DC2626]/20 text-left">
                                                    <span className="text-[10px] text-gray-400 uppercase font-bold">Resp. Bomberos</span>
                                                    <h4 className="text-2xl font-black mt-1 text-white">12 min</h4>
                                                    <span className="text-[9px] text-emerald-500 font-bold block mt-1">Despliegue rápido</span>
                                                </div>
                                            </>
                                        )}
                                        {activeDashboardSection === 'wind' && (
                                            <>
                                                <div className="bg-[#111A2E] p-4 rounded-xl border border-[#F28C28]/20 text-left">
                                                    <span className="text-[10px] text-gray-400 uppercase font-bold">Total Alertas</span>
                                                    <h4 className="text-2xl font-black mt-1 text-[#F28C28]">7</h4>
                                                    <span className="text-[9px] text-amber-500 font-bold block mt-1">Viento Zonda / Sur</span>
                                                </div>
                                                <div className="bg-[#111A2E] p-4 rounded-xl border border-[#F28C28]/20 text-left">
                                                    <span className="text-[10px] text-gray-400 uppercase font-bold">Ráfaga Máxima</span>
                                                    <h4 className="text-xl font-black mt-2 text-white truncate">92 km/h</h4>
                                                    <span className="text-[9px] text-[#F28C28] font-bold block mt-1">Viento Zonda</span>
                                                </div>
                                                <div className="bg-[#111A2E] p-4 rounded-xl border border-[#F28C28]/20 text-left">
                                                    <span className="text-[10px] text-gray-400 uppercase font-bold">Cortes de Luz</span>
                                                    <h4 className="text-xl font-black mt-2 text-white truncate">3 zonas</h4>
                                                    <span className="text-[9px] text-gray-400 block mt-1">Rivadavia / S. Lucía</span>
                                                </div>
                                                <div className="bg-[#111A2E] p-4 rounded-xl border border-[#F28C28]/20 text-left">
                                                    <span className="text-[10px] text-gray-400 uppercase font-bold">Clases Susp.</span>
                                                    <h4 className="text-2xl font-black mt-1 text-white">1 vez</h4>
                                                    <span className="text-[9px] text-red-400 font-bold block mt-1">Recomendación Civil</span>
                                                </div>
                                            </>
                                        )}
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fadeIn">
                                        {/* Detalle de Características de Datos Propios por Sección */}
                                        <div className="bg-[#111A2E] p-5 rounded-2xl border border-white/5 text-left md:col-span-1 flex flex-col justify-between">
                                            <div>
                                                <h4 className="text-xs font-black text-[#F28C28] uppercase tracking-wider mb-3">Detalle de Sección</h4>
                                                
                                                {activeDashboardSection === 'general' && (
                                                    <div className="space-y-4">
                                                        <h5 className="font-bold text-sm text-white">Análisis Agregado</h5>
                                                        <p className="text-xs text-gray-400 leading-relaxed">
                                                            El mes en curso presenta una alta actividad de focos de incendio en malezas debido a la baja humedad estacional. Los siniestros viales se mantienen en la media provincial.
                                                        </p>
                                                        <div className="p-3 bg-[#0B1528] rounded-xl border border-white/5 text-[10px] text-gray-400">
                                                            ⚡ <b>Dato Clave</b>: Dpto. Sarmiento concentra el 40% de los incidentes totales de este período.
                                                        </div>
                                                    </div>
                                                )}

                                                {activeDashboardSection === 'traffic' && (
                                                    <div className="space-y-4">
                                                        <h5 className="font-bold text-sm text-[#2563EB]">Siniestralidad Vial</h5>
                                                        <ul className="space-y-3 text-xs text-gray-300">
                                                            <li className="flex gap-2">
                                                                <span className="text-[#2563EB] font-bold">🏍️</span>
                                                                65% de los choques registrados involucran motociclistas.
                                                            </li>
                                                            <li className="flex gap-2">
                                                                <span className="text-[#2563EB] font-bold">🚦</span>
                                                                Esquinas sin semáforo son responsables de 8 de cada 10 colisiones urbanas.
                                                            </li>
                                                            <li className="flex gap-2">
                                                                <span className="text-[#2563EB] font-bold">🚨</span>
                                                                Colisiones por alcance representan la tipología dominante en avenidas de alto flujo.
                                                            </li>
                                                        </ul>
                                                    </div>
                                                )}

                                                {activeDashboardSection === 'fire' && (
                                                    <div className="space-y-4">
                                                        <h5 className="font-bold text-sm text-[#DC2626]">Focos de Fuego</h5>
                                                        <ul className="space-y-3 text-xs text-gray-300">
                                                            <li className="flex gap-2">
                                                                <span className="text-[#DC2626] font-bold">🌾</span>
                                                                La quema de pastizales y lotes baldíos es el disparador del 75% de las alarmas.
                                                            </li>
                                                            <li className="flex gap-2">
                                                                <span className="text-[#DC2626] font-bold">🚒</span>
                                                                Intervenciones rápidas de bomberos evitaron propagación en 92% de los focos.
                                                                </li>
                                                            <li className="flex gap-2">
                                                                <span className="text-[#DC2626] font-bold">🔥</span>
                                                                Los incendios vehiculares corresponden en su totalidad a fallas mecánicas previas.
                                                            </li>
                                                        </ul>
                                                    </div>
                                                )}

                                                {activeDashboardSection === 'wind' && (
                                                    <div className="space-y-4">
                                                        <h5 className="font-bold text-sm text-[#F28C28]">Fenómenos Climáticos</h5>
                                                        <ul className="space-y-3 text-xs text-gray-300">
                                                            <li className="flex gap-2">
                                                                <span className="text-[#F28C28] font-bold">🌳</span>
                                                                Se reportó la caída de 18 árboles/ramas de gran porte en áreas peatonales del microcentro.
                                                            </li>
                                                            <li className="flex gap-2">
                                                                <span className="text-[#F28C28] font-bold">⚡</span>
                                                                Transformadores dañados dejaron sin energía eléctrica a 2.300 usuarios en Rivadavia.
                                                            </li>
                                                            <li className="flex gap-2">
                                                                <span className="text-[#F28C28] font-bold">⚠️</span>
                                                                Ráfagas del Zonda superaron los 90 km/h en zonas del piedemonte sanjuanino.
                                                            </li>
                                                        </ul>
                                                    </div>
                                                )}
                                            </div>

                                            {/* Botón de Acción Tentador */}
                                            <button 
                                                onClick={() => setModalView('pricing')}
                                                className="w-full mt-6 bg-[#F28C28] text-white text-[10px] font-black uppercase tracking-wider py-2 rounded-xl shadow-lg shadow-[#F28C28]/20 hover:brightness-110 active:scale-95 transition-all cursor-pointer"
                                            >
                                                Desbloquear Historial ➜
                                            </button>
                                        </div>

                                        {/* Gráfico Dinámico */}
                                        <div className="bg-[#111A2E] p-5 rounded-2xl border border-white/5 text-left md:col-span-2">
                                            <h4 className="text-sm font-bold mb-4">
                                                {activeDashboardSection === 'general' && "Incidentes Totales por Semana (Últimos 30 días)"}
                                                {activeDashboardSection === 'traffic' && "Volumen Horario de Colisiones Viales (Últimos 30 días)"}
                                                {activeDashboardSection === 'fire' && "Focos Ígneos por Sub-categoría (Últimos 30 días)"}
                                                {activeDashboardSection === 'wind' && "Intensidad de Viento en Ráfagas Máximas (km/h)"}
                                            </h4>
                                            <div className="h-48 flex items-end gap-3 md:gap-6 pt-4 border-b border-gray-700/50">
                                                {activeDashboardSection === 'general' && [
                                                    { label: "Semana 1", val: "35%", color: "bg-[#002D62]" },
                                                    { label: "Semana 2", val: "55%", color: "bg-[#002D62]" },
                                                    { label: "Semana 3", val: "85%", color: "bg-[#F28C28]" },
                                                    { label: "Semana 4", val: "45%", color: "bg-[#002D62]" }
                                                ].map((d, i) => (
                                                    <div key={i} className="flex-1 flex flex-col items-center gap-2 group">
                                                        <div className={`w-full ${d.color} rounded-t-lg transition-all group-hover:brightness-110`} style={{ height: d.val }}></div>
                                                        <span className="text-[10px] text-gray-400 font-bold truncate max-w-full">{d.label}</span>
                                                    </div>
                                                ))}

                                                {activeDashboardSection === 'traffic' && [
                                                    { label: "Mañana", val: "25%", color: "bg-[#2563EB]" },
                                                    { label: "Mediodía", val: "40%", color: "bg-[#2563EB]" },
                                                    { label: "Tarde", val: "95%", color: "bg-[#2563EB]" },
                                                    { label: "Noche", val: "30%", color: "bg-[#2563EB]" }
                                                ].map((d, i) => (
                                                    <div key={i} className="flex-1 flex flex-col items-center gap-2 group">
                                                        <div className={`w-full ${d.color} rounded-t-lg transition-all group-hover:brightness-110`} style={{ height: d.val }}></div>
                                                        <span className="text-[10px] text-gray-400 font-bold truncate max-w-full">{d.label}</span>
                                                    </div>
                                                ))}

                                                {activeDashboardSection === 'fire' && [
                                                    { label: "Pastizales", val: "90%", color: "bg-[#DC2626]" },
                                                    { label: "Viviendas", val: "20%", color: "bg-[#DC2626]" },
                                                    { label: "Vehículos", val: "45%", color: "bg-[#DC2626]" },
                                                    { label: "Otros", val: "15%", color: "bg-[#DC2626]" }
                                                ].map((d, i) => (
                                                    <div key={i} className="flex-1 flex flex-col items-center gap-2 group">
                                                        <div className={`w-full ${d.color} rounded-t-lg transition-all group-hover:brightness-110`} style={{ height: d.val }}></div>
                                                        <span className="text-[10px] text-gray-400 font-bold truncate max-w-full">{d.label}</span>
                                                    </div>
                                                ))}

                                                {activeDashboardSection === 'wind' && [
                                                    { label: "Capital", val: "45%", color: "bg-[#F28C28]" },
                                                    { label: "Rivadavia", val: "85%", color: "bg-[#F28C28]" },
                                                    { label: "Chimbas", val: "30%", color: "bg-[#F28C28]" },
                                                    { label: "Zonda", val: "95%", color: "bg-[#F28C28]" }
                                                ].map((d, i) => (
                                                    <div key={i} className="flex-1 flex flex-col items-center gap-2 group">
                                                        <div className={`w-full ${d.color} rounded-t-lg transition-all group-hover:brightness-110`} style={{ height: d.val }}></div>
                                                        <span className="text-[10px] text-gray-400 font-bold truncate max-w-full">{d.label}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Banner CTA Final Tentador */}
                                    <div className="bg-gradient-to-r from-[#111A2E] to-[#15223F] p-4 rounded-xl border border-white/5 text-left flex flex-col sm:flex-row items-center justify-between gap-4">
                                        <div className="text-xs text-gray-300">
                                            📊 <b>¿Necesitas filtros cruzados de datos y descargas completas en formato Excel/CSV?</b>
                                            <p className="text-[10px] text-gray-400 mt-0.5">El acceso público está limitado a estadísticas agregadas de los últimos 30 días.</p>
                                        </div>
                                        <button 
                                            onClick={() => setModalView('pricing')}
                                            className="bg-white/5 hover:bg-white/10 text-white text-[10px] font-black uppercase tracking-wider py-2 px-4 rounded-lg border border-white/10 transition-colors shrink-0 cursor-pointer"
                                        >
                                            Ver Planes Premium
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MapComponent;
