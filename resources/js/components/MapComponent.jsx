import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, ZoomControl, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { es } from 'date-fns/locale/es';
import L from 'leaflet';
import { Menu, X, Wind, Zap, Car, AlertTriangle, ChevronDown, ChevronUp, Calendar, Database, ChevronLeft, Flame, BarChart2, Check, TrendingUp, Activity } from 'lucide-react';

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

const MapComponent = () => {
    const [incidents, setIncidents] = useState([]);
    // Abrir por defecto en escritorio, cerrado en móvil
    const [sidebarOpen, setSidebarOpen] = useState(() => {
        // Guard against SSR environments
        if (typeof window === 'undefined') return true;
        return window.innerWidth > 768;
    });
    
    // Estados para Filtros
    const [selectedDate, setSelectedDate] = useState(() => new Date().toISOString().split('T')[0]);
    const [visibleTabs, setVisibleTabs] = useState(['wind', 'accident', 'fire']); // Por defecto todos activos
    const [loading, setLoading] = useState(false);
    const [premiumError, setPremiumError] = useState(false);
    const [lastSync, setLastSync] = useState(null);       
    const [selectedIncident, setSelectedIncident] = useState(null);
    const [, setTick] = useState(0);                      // forces re-render every minute for relative time
    const [premiumModalOpen, setPremiumModalOpen] = useState(false);
    const [modalView, setModalView] = useState('pricing'); // 'pricing' or 'dashboard'
    const [activeDashboardSection, setActiveDashboardSection] = useState('general'); // 'general', 'traffic', 'fire', 'wind'

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

    useEffect(() => {
        const fetchIncidents = () => {
            setLoading(true);
            setPremiumError(false);
            
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
                    setIncidents(Array.isArray(items) ? items : []);
                    setLastSync(new Date()); 
                    setLoading(false);
                })
                .catch(err => {
                    console.error("Error fetching incidents:", err);
                    if (!premiumError) setIncidents([]);
                    setLoading(false);
                });
        };

        fetchIncidents();
        const interval = setInterval(fetchIncidents, 300000);
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
            
            {/* Sidebar Toggle Button (Floating, only visible when closed) */}
            {!sidebarOpen && (
                <button 
                    onClick={() => setSidebarOpen(true)}
                    className="absolute top-4 left-4 z-[1000] bg-white p-2 rounded shadow-md text-[#002D62] hover:bg-gray-100 transition-colors"
                    style={{ zIndex: 1000 }} // Ensure it's above the map
                    aria-label="Abrir menú lateral"
                >
                    <Menu size={24} />
                </button>
            )}

            {/* Collapsible Sidebar */}
            <div 
                className={`absolute top-0 left-0 h-full w-80 bg-white shadow-2xl transition-transform duration-300 ease-in-out z-[999] flex flex-col overflow-hidden ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
                style={{ zIndex: 999 }}
            >
                    {/* Cabecera Sidebar con Logo Original */}
                    <div className="bg-white border-b border-gray-100 pt-3 pb-1 flex justify-center">
                        <img src="/images/logo.jpeg" alt="ZonData Logo" className="w-[80%] h-auto object-contain" />
                    </div>

                    {/* Selector de Fecha Estilizado en Azul */}
                    <div className="pt-2 pb-4 px-4 border-b border-gray-100 bg-white">
                        <div className="flex items-center justify-end mb-2 md:hidden">
                            <button 
                                onClick={() => setSidebarOpen(false)} 
                                className="text-gray-400 hover:text-gray-600"
                                aria-label="Cerrar panel"
                            >
                                <X size={20} />
                            </button>
                        </div>
                                          <div className="relative group">
                            {/* Icono Izquierda (Oro) */}
                            <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none text-[#EAB308] z-10">
                                <Calendar size={15} strokeWidth={2.5} />
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
                                className="w-full bg-[#002552] border-none rounded-xl py-2.5 pl-9 pr-9 text-sm font-black text-white focus:ring-4 focus:ring-[#EAB308]/20 outline-none transition-all shadow-xl shadow-blue-950/40 text-center tracking-wider cursor-pointer"
                                wrapperClassName="w-full"
                                aria-label="Seleccionar fecha de incidentes"
                                calendarClassName="premium-calendar"
                            />

                            {/* Icono Derecha (Blanco) */}
                            <div className="absolute inset-y-0 right-3 flex items-center pointer-events-none text-white/60 z-10">
                                <Calendar size={13} />
                            </div>
                        </div>
                    </div>
                
                <div className="flex-1 min-h-0 flex flex-col bg-[#F4F4F4]">
                    {/* Navegación por Pestañas de Categoría */}
                    <div className="bg-white border-b border-gray-200 p-2">
                        <div className="flex gap-4 bg-gray-100 p-2 rounded-xl">
                            <button 
                                onClick={() => toggleTab('wind')}
                                className={`flex-1 flex flex-col items-center py-2 rounded-md transition-all relative ${visibleTabs.includes('wind') ? 'bg-white shadow-sm text-[#EAB308]' : 'text-gray-400 hover:text-gray-500 opacity-60'}`}
                            >
                                <Wind size={20} />
                                <span className="text-[10px] font-bold mt-1 uppercase">Viento</span>
                                {tabCounts.wind > 0 && (
                                    <span className="absolute -top-3 -right-3 bg-[#002D62] text-[#F28C28] text-sm font-black w-10 h-10 flex items-center justify-center rounded-full shadow-xl border-2 border-white ring-4 ring-[#002D62]/10">
                                        {tabCounts.wind}
                                    </span>
                                )}
                            </button>
                            <button 
                                onClick={() => toggleTab('accident')}
                                className={`flex-1 flex flex-col items-center py-2 rounded-md transition-all relative ${visibleTabs.includes('accident') ? 'bg-white shadow-sm text-[#2563EB]' : 'text-gray-400 hover:text-gray-500 opacity-60'}`}
                            >
                                <Car size={20} />
                                <span className="text-[10px] font-bold mt-1 uppercase">Tránsito</span>
                                {tabCounts.accident > 0 && (
                                    <span className="absolute -top-3 -right-3 bg-[#002D62] text-[#F28C28] text-sm font-black w-10 h-10 flex items-center justify-center rounded-full shadow-xl border-2 border-white ring-4 ring-[#002D62]/10">
                                        {tabCounts.accident}
                                    </span>
                                )}
                            </button>
                            <button 
                                onClick={() => toggleTab('fire')}
                                className={`flex-1 flex flex-col items-center py-2 rounded-md transition-all relative ${visibleTabs.includes('fire') ? 'bg-white shadow-sm text-[#DC2626]' : 'text-gray-400 hover:text-gray-500 opacity-60'}`}
                            >
                                <Flame size={20} />
                                <span className="text-[10px] font-bold mt-1 uppercase">Incendios</span>
                                {tabCounts.fire > 0 && (
                                    <span className="absolute -top-3 -right-3 bg-[#002D62] text-[#F28C28] text-sm font-black w-10 h-10 flex items-center justify-center rounded-full shadow-xl border-2 border-white ring-4 ring-[#002D62]/10">
                                        {tabCounts.fire}
                                    </span>
                                )}
                            </button>
                        </div>
                    </div>

                    <div className="flex-1 min-h-0 overflow-y-auto p-4 custom-scrollbar">
                        {/* Estado Premium / Error */}
                        {premiumError && (
                            <div className="mb-4 bg-gradient-to-br from-slate-900 to-[#002D62] p-5 rounded-2xl shadow-xl border border-white/10 text-white relative overflow-hidden">
                                <div className="absolute -top-4 -right-4 text-white/5">
                                    <Database size={80} />
                                </div>
                                <div className="relative z-10">
                                    <div className="flex items-center gap-2 mb-2">
                                        <div className="bg-[#F28C28] p-1.5 rounded-lg">
                                            <Calendar className="text-white" size={16} />
                                        </div>
                                        <h4 className="font-black text-sm uppercase tracking-tighter">Acceso Histórico</h4>
                                    </div>
                                    <p className="text-xs text-gray-300 leading-relaxed mb-4">
                                        La consulta de datos de más de 30 días requiere una suscripción <b>ZonData Premium</b>.
                                    </p>
                                    <button 
                                        onClick={() => {
                                            setModalView('pricing');
                                            setPremiumModalOpen(true);
                                        }}
                                        className="w-full bg-[#F28C28] text-white py-2.5 rounded-xl text-xs font-black uppercase tracking-widest shadow-lg shadow-[#F28C28]/20 hover:scale-[1.02] transition-transform"
                                    >
                                        Subscribirse ahora
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Barra de estado del sistema — prominente */}
                        {!premiumError && (
                            <div className={`mb-4 rounded-xl border-2 p-3 transition-all ${
                                loading
                                    ? 'bg-amber-50 border-amber-300'
                                    : incidents.length > 0
                                        ? 'bg-emerald-50 border-emerald-300'
                                        : 'bg-slate-50 border-slate-200'
                            }`}>
                            <div className="flex items-center gap-2.5">
                                {/* Punto de estado con anillo */}
                                <span className="relative flex-shrink-0 w-4 h-4">
                                    {(loading || incidents.length > 0) && (
                                        <span className={`absolute inline-flex h-full w-full rounded-full opacity-50 animate-ping ${
                                            loading ? 'bg-amber-400' : 'bg-emerald-500'
                                        }`} />
                                    )}
                                    <span className={`relative inline-flex w-4 h-4 rounded-full ${
                                        loading
                                            ? 'bg-amber-400'
                                            : incidents.length > 0
                                                ? 'bg-emerald-500'
                                                : 'bg-slate-400'
                                    }`} />
                                </span>

                                <div className="min-w-0">
                                    {/* Línea 1: estado principal */}
                                    <p className={`text-xs font-bold leading-tight ${
                                        loading
                                            ? 'text-amber-700'
                                            : incidents.length > 0
                                                ? 'text-emerald-700'
                                                : 'text-slate-600'
                                    }`}>
                                        {loading
                                            ? '⟳ Sincronizando RSS...'
                                            : incidents.length > 0
                                                ? `✓ ${incidents.length} incidente${incidents.length > 1 ? 's' : ''} detectado${incidents.length > 1 ? 's' : ''}`
                                                : '— Sin incidentes detectados'}
                                    </p>
                                    {/* Línea 2: tiempo de sincronización */}
                                    {lastSync && !loading && (
                                        <p className="text-[10px] text-slate-400 mt-0.5">
                                            Última sincronización: {relativeTime(lastSync)}
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>
                        )}

                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                                <h2 className="font-semibold text-gray-700 uppercase text-sm">Eventos Activos</h2>
                                {loading && (
                                    <div className="animate-spin text-[#F28C28]">
                                        <Zap size={14} />
                                    </div>
                                )}
                            </div>
                            <span className="bg-[#002D62] text-white text-xs py-1 px-2 rounded-full font-bold">
                                {filteredIncidents.length}
                            </span>
                        </div>
                        
                        <div className="space-y-3">
                            {filteredIncidents.map(incident => {
                                // Determinar color de la tarjeta según categoría
                                let borderColor = '#002D62'; // Por defecto
                                if (['arboles', 'corte', 'techo', 'viento', 'zonda'].includes(incident.category?.slug)) {
                                    borderColor = '#EAB308'; // Viento: Amarillo
                                } else if (['choque', 'vuelco', 'atropello'].includes(incident.category?.slug)) {
                                    borderColor = '#2563EB'; // Accidente: Azul
                                } else if (incident.category?.slug?.startsWith('incendio') || incident.category?.slug?.includes('siniestro')) {
                                    borderColor = '#DC2626'; // Incendio: Rojo
                                }
                                
                                return (
                                    <div 
                                        key={incident.id} 
                                        onClick={() => setSelectedIncident(incident)}
                                        className={`bg-white p-3 rounded shadow-sm border-l-4 relative cursor-pointer transition-all hover:bg-gray-50 active:scale-[0.98] ${selectedIncident?.id === incident.id ? 'ring-2 ring-[#002D62] ring-inset' : ''}`} 
                                        style={{ borderColor }}
                                    >
                                        <h3 className="font-bold text-[#002D62] text-sm leading-tight">{incident.title}</h3>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* CTA Dataset Completo */}
                    <div className="mt-2">
                        <button 
                            className="w-full group relative overflow-hidden bg-gradient-to-br from-[#002D62] to-[#001D40] p-3 rounded-xl shadow-lg border border-white/10 transition-all hover:scale-[1.02] active:scale-[0.98]"
                            onClick={() => {
                                setModalView('pricing');
                                setPremiumModalOpen(true);
                            }}
                        >
                            <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
                                <Database size={40} />
                            </div>
                            <div className="relative z-10 flex items-center justify-between w-full gap-2">
                                <div className="flex flex-col items-start text-left">
                                    <span className="text-[9px] font-black text-[#F28C28] uppercase tracking-[0.15em] leading-none mb-1">Acceso Premium</span>
                                    <h4 className="text-white font-bold text-xs leading-none">Dataset Completo</h4>
                                </div>
                                <div className="flex items-center text-white text-[10px] font-black uppercase tracking-wider bg-[#F28C28] py-2 px-2.5 rounded-lg shadow-md shrink-0">
                                    Suscribirse ahora
                                </div>
                            </div>
                        </button>
                    </div>
                </div>

                {/* Botón para ocultar en la parte inferior del navbar */}
                <div className="p-3 bg-white border-t border-gray-100 flex justify-center">
                    <button 
                        onClick={() => setSidebarOpen(false)}
                        className="p-2.5 bg-gray-100 hover:bg-gray-200 text-[#002D62] rounded-full transition-colors flex items-center justify-center shadow-sm"
                        aria-label="Plegar panel"
                        title="Plegar panel"
                    >
                        <ChevronLeft size={20} />
                    </button>
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
                                <div className="p-1">
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="inline-block px-2 py-1 bg-gray-100 text-xs font-bold rounded text-[#002D62]">
                                            {incident.category?.name || 'Evento'}
                                        </span>
                                        {incident.is_approximate && (
                                            <span className="flex items-center gap-1 text-[9px] font-bold text-gray-400 uppercase bg-gray-50 px-1 rounded border border-gray-100">
                                                <AlertTriangle size={10} /> Ubicación Aproximada
                                            </span>
                                        )}
                                    </div>
                                    <h3 className="font-bold text-sm mb-1">{incident.title}</h3>
                                    {incident.description && <p className="text-xs text-gray-600 mb-2">{incident.description}</p>}
                                    <div className="text-[10px] border-t pt-2 mt-2">
                                        Visto en: <a href={incident.source_url} target="_blank" rel="noreferrer" className="text-blue-500 font-medium">{incident.source_name}</a>
                                        <br/>
                                        <span className="text-gray-400">{new Date(incident.event_date).toLocaleString('es-AR')}</span>
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
