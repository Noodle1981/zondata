import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, ZoomControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Menu, X, Wind, Zap, Car, AlertTriangle, ChevronDown, ChevronUp, Calendar, Database } from 'lucide-react';

// Fix for default Leaflet icons in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom Icon generator based on category type
const createCustomIcon = (type, isApproximate = false, isFatal = false) => {
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
        color = '#DC2626'; 
        selectedIcon = icons.car;
    } else if (type.toLowerCase().includes('incendio') || type.toLowerCase().includes('siniestro')) {
        color = '#2563EB'; 
        selectedIcon = icons.fire;
    }

    const svgIcon = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="40" height="40">
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
        popupAnchor: [0, -40]
    });
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
    const [activeFilters, setActiveFilters] = useState([]);
    const [selectedDate, setSelectedDate] = useState(() => new Date().toISOString().split('T')[0]);
    const [activeTab, setActiveTab] = useState('wind'); // 'wind', 'accident', 'fire'
    const [loading, setLoading] = useState(false);
    const [premiumError, setPremiumError] = useState(false);
    const [filtersExpanded, setFiltersExpanded] = useState(false);
    const [lastSync, setLastSync] = useState(null);       
    const [, setTick] = useState(0);                      // forces re-render every minute for relative time

    // Definir las categorías
    const windCategories = [
        { id: 'arboles', name: '🌳 Caída de Árboles / Ramas' },
        { id: 'corte', name: '⚡ Cortes de Luz' },
        { id: 'incendio', name: '🔥 Incendios' },
        { id: 'techo', name: '💨 Voladuras / Otros' }
    ];

    const accidentCategories = [
        { id: 'choque', name: '💥 Choque / Colisión' },
        { id: 'vuelco', name: '🔄 Vuelco' },
        { id: 'atropello', name: '🚶 Atropello / Peatón' }
    ];

    const fireCategories = [
        { id: 'incendio', name: '🔥 Incendio General' },
        { id: 'incendio-vivienda', name: '🏠 Incendio Vivienda' },
        { id: 'incendio-pastizales', name: '🌿 Pastizales / Campo' },
        { id: 'incendio-vehiculo', name: '🚗 Incendio Vehículo' }
    ];

    const toggleFilter = (categoryId) => {
        setActiveFilters(prev => 
            prev.includes(categoryId) 
                ? prev.filter(f => f !== categoryId) 
                : [...prev, categoryId]
        );
    };

    // Calcular contadores por slug
    const counts = incidents.reduce((acc, inc) => {
        const slug = inc.category?.slug;
        if (slug) acc[slug] = (acc[slug] || 0) + 1;
        return acc;
    }, {});

    const filteredIncidents = incidents.filter(incident => {
        const slug = incident.category?.slug;
        
        // 1. Determinar a qué grupo pertenece el incidente
        const isWind = ['arboles', 'corte', 'techo', 'viento', 'zonda'].some(k => slug?.includes(k));
        const isAccident = ['choque', 'vuelco', 'atropello', 'accidente', 'transito'].some(k => slug?.includes(k));
        const isFire = slug?.includes('incendio') || slug?.includes('siniestro');

        // 2. Filtrar primero por la pestaña activa
        if (activeTab === 'wind' && !isWind) return false;
        if (activeTab === 'accident' && !isAccident) return false;
        if (activeTab === 'fire' && !isFire) return false;

        // 3. Si hay filtros específicos (checkboxes), filtrar por ellos
        if (activeFilters.length > 0) {
            return activeFilters.includes(slug);
        }

        return true;
    });

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

    return (
        <div className="relative w-full h-screen overflow-hidden flex">
            
            {/* Sidebar Toggle Button (Floating, only visible when closed) */}
            {!sidebarOpen && (
                <button 
                    onClick={() => setSidebarOpen(true)}
                    className="absolute top-4 left-4 z-[1000] bg-white p-2 rounded shadow-md text-[#002D62] hover:bg-gray-100 transition-colors"
                    style={{ zIndex: 1000 }} // Ensure it's above the map
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
                    <div className="bg-white border-b border-gray-100">
                        <img src="/images/logo.jpeg" alt="ZonData Logo" className="w-full h-auto object-contain" />
                    </div>

                    {/* Selector de Fecha Estilizado en Azul */}
                    <div className="p-4 border-b border-gray-100 bg-white">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400">Consultar Fecha</h3>
                            <button onClick={() => setSidebarOpen(false)} className="md:hidden text-gray-400 hover:text-gray-600">
                                <X size={20} />
                            </button>
                        </div>
                        
                        <div className="relative group">
                            <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none text-[#EAB308] z-10">
                                <Calendar size={16} />
                            </div>
                            <input 
                                type="date" 
                                value={selectedDate}
                                onChange={(e) => setSelectedDate(e.target.value)}
                                max={new Date().toISOString().split('T')[0]}
                                className="w-full bg-[#002552] border-2 border-[#001d40] rounded-xl py-2.5 pl-10 pr-4 text-sm font-black text-white focus:ring-2 focus:ring-[#EAB308] focus:border-transparent outline-none transition-all shadow-lg shadow-blue-900/20 appearance-none"
                                style={{ colorScheme: 'dark' }} // Asegura que el icono del calendario nativo sea visible en oscuro
                            />
                        </div>
                    </div>
                
                <div className="flex-1 min-h-0 flex flex-col bg-[#F4F4F4]">
                    {/* Navegación por Pestañas de Categoría */}
                    <div className="bg-white border-b border-gray-200 p-2">
                        <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
                            <button 
                                onClick={() => { setActiveTab('wind'); setActiveFilters([]); }}
                                className={`flex-1 flex flex-col items-center py-2 rounded-md transition-all ${activeTab === 'wind' ? 'bg-white shadow-sm text-[#EAB308]' : 'text-gray-400 hover:text-gray-600'}`}
                            >
                                <Wind size={20} />
                                <span className="text-[10px] font-bold mt-1 uppercase">Viento</span>
                            </button>
                            <button 
                                onClick={() => { setActiveTab('accident'); setActiveFilters([]); }}
                                className={`flex-1 flex flex-col items-center py-2 rounded-md transition-all ${activeTab === 'accident' ? 'bg-white shadow-sm text-[#DC2626]' : 'text-gray-400 hover:text-gray-600'}`}
                            >
                                <Car size={20} />
                                <span className="text-[10px] font-bold mt-1 uppercase">Tránsito</span>
                            </button>
                            <button 
                                onClick={() => { setActiveTab('fire'); setActiveFilters([]); }}
                                className={`flex-1 flex flex-col items-center py-2 rounded-md transition-all ${activeTab === 'fire' ? 'bg-white shadow-sm text-[#2563EB]' : 'text-gray-400 hover:text-gray-600'}`}
                            >
                                <Zap size={20} />
                                <span className="text-[10px] font-bold mt-1 uppercase">Siniestros</span>
                            </button>
                        </div>
                    </div>

                    {/* Área de Filtros Dinámicos Plegable */}
                    <div className="bg-white border-b border-gray-100 shadow-inner">
                        <button 
                            onClick={() => setFiltersExpanded(!filtersExpanded)}
                            className="w-full px-4 py-3 flex items-center justify-between text-[#002D62] hover:bg-gray-50 transition-colors"
                        >
                            <div className="flex items-center gap-2">
                                <h3 className="text-[10px] font-black uppercase tracking-widest text-gray-400">
                                    {activeTab === 'wind' && "Opciones de Viento"}
                                    {activeTab === 'accident' && "Opciones de Tránsito"}
                                    {activeTab === 'fire' && "Opciones de Siniestros"}
                                </h3>
                                {!filtersExpanded && activeFilters.length > 0 && (
                                    <span className="bg-[#002D62] text-white text-[8px] px-1.5 py-0.5 rounded-full font-bold">
                                        {activeFilters.length}
                                    </span>
                                )}
                            </div>
                            {filtersExpanded ? <ChevronUp size={16} className="text-gray-400" /> : <ChevronDown size={16} className="text-gray-400" />}
                        </button>
                        
                        {filtersExpanded && (
                            <div className="px-4 pb-4 space-y-1 animate-in slide-in-from-top-1 duration-200">
                                {(activeTab === 'wind' ? windCategories : activeTab === 'accident' ? accidentCategories : fireCategories).map(cat => {
                                    const count = counts[cat.id] || 0;
                                    const isSelected = activeFilters.includes(cat.id);
                                    let activeColor = activeTab === 'wind' ? '#EAB308' : activeTab === 'accident' ? '#DC2626' : '#2563EB';

                                    return (
                                        <label key={cat.id} className={`flex items-center justify-between p-2 rounded-xl cursor-pointer transition-all group ${isSelected ? 'bg-gray-50 shadow-sm' : 'hover:bg-gray-50/50'}`}>
                                            <div className="flex items-center gap-3">
                                                <div className="relative flex items-center">
                                                    <input 
                                                        type="checkbox" 
                                                        className="peer appearance-none w-5 h-5 rounded-lg border-2 border-gray-200 checked:border-transparent transition-all"
                                                        style={{ backgroundColor: isSelected ? activeColor : 'transparent' }}
                                                        checked={isSelected}
                                                        onChange={() => toggleFilter(cat.id)}
                                                    />
                                                    {isSelected && <Zap size={10} className="absolute left-1.25 text-white pointer-events-none" fill="white" />}
                                                </div>
                                                <span className={`text-xs font-bold transition-colors ${isSelected ? 'text-[#002D62]' : 'text-gray-500 group-hover:text-gray-700'}`}>
                                                    {cat.name}
                                                </span>
                                            </div>
                                            <span className={`text-[10px] font-black px-2 py-0.5 rounded-full ${count > 0 ? 'bg-white border border-gray-100 text-gray-400 shadow-sm' : 'text-gray-300'}`}>
                                                {count}
                                            </span>
                                        </label>
                                    );
                                })}
                            </div>
                        )}
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
                                    <button className="w-full bg-[#F28C28] text-white py-2.5 rounded-xl text-xs font-black uppercase tracking-widest shadow-lg shadow-[#F28C28]/20 hover:scale-[1.02] transition-transform">
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
                                    borderColor = '#DC2626'; // Accidente: Rojo
                                } else if (incident.category?.slug?.startsWith('incendio') || incident.category?.slug?.includes('siniestro')) {
                                    borderColor = '#2563EB'; // Siniestro: Azul
                                }
                                
                                return (
                                    <div key={incident.id} className="bg-white p-3 rounded shadow-sm border-l-4 relative overflow-hidden" style={{ borderColor }}>
                                        {incident.is_approximate && (
                                            <div className="absolute top-0 right-0 px-2 py-0.5 bg-gray-100 text-[8px] text-gray-500 rounded-bl font-bold uppercase tracking-wider">
                                                Aproximado
                                            </div>
                                        )}
                                        <h3 className="font-bold text-[#002D62] text-sm">{incident.title}</h3>
                                        <p className="text-xs text-gray-600 mt-1 line-clamp-2">{incident.description}</p>
                                        <div className="mt-2 flex items-center justify-between">
                                            <span className="text-[10px] bg-gray-100 px-2 py-1 rounded text-gray-600 font-medium">
                                                {incident.category?.name || 'Evento'}
                                            </span>
                                            <a href={incident.source_url} target="_blank" rel="noreferrer" className="text-[10px] text-blue-500 hover:underline">
                                                Fuente: {incident.source_name}
                                            </a>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* CTA Dataset Completo */}
                    <div className="mt-2">
                        <button 
                            className="w-full group relative overflow-hidden bg-gradient-to-br from-[#002D62] to-[#001D40] p-4 rounded-xl shadow-lg border border-white/10 transition-all hover:scale-[1.02] active:scale-[0.98]"
                            onClick={() => alert("Próximamente: Suscríbete para acceder al dataset histórico completo y herramientas de análisis avanzado.")}
                        >
                            <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
                                <Database size={40} />
                            </div>
                            <div className="relative z-10 flex flex-col items-start gap-1">
                                <span className="text-[10px] font-bold text-[#F28C28] uppercase tracking-[0.2em]">Acceso Premium</span>
                                <h4 className="text-white font-bold text-sm">Dataset Completo</h4>
                                <p className="text-gray-400 text-[10px] text-left leading-tight mt-1">
                                    Histórico total, exportación CSV/JSON y alertas personalizadas.
                                </p>
                                <div className="mt-3 flex items-center gap-2 text-white text-xs font-bold bg-[#F28C28] py-1.5 px-3 rounded-lg">
                                    Suscribirse ahora
                                </div>
                            </div>
                        </button>
                    </div>
                </div>

                {/* Botón para ocultar en la parte inferior del navbar */}
                <div className="p-4 bg-white border-t border-gray-200">
                    <button 
                        onClick={() => setSidebarOpen(false)}
                        className="w-full flex justify-center items-center gap-2 py-2 bg-gray-100 hover:bg-gray-200 text-[#002D62] rounded font-medium transition-colors"
                    >
                        <X size={20} />
                        Plegar panel
                    </button>
                </div>
            </div>

            {/* Map Area */}
            <div className="flex-1 h-full relative z-0">
                <MapContainer center={position} zoom={8} className="w-full h-full custom-map-cursor" zoomControl={false}>
                    {/* Position zoom control on the right to avoid sidebar overlap */}
                    <ZoomControl position="bottomright" />
                    
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                    />
                    
                    {filteredIncidents.map(incident => (
                        <Marker 
                            key={incident.id} 
                            position={[incident.latitude, incident.longitude]}
                            icon={createCustomIcon(incident.category?.slug || '', incident.is_approximate, incident.is_fatal)}
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
        </div>
    );
};

export default MapComponent;
