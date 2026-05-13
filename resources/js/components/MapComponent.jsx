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
const createCustomIcon = (type, isApproximate = false) => {
    // Determine color based on rules: Zonda (Wind/Fire) = Orange, Data (Tech/Services) = Blue, etc.
    let color = '#002D62'; // Tech Blue default
    if (['arboles', 'corte', 'incendio', 'techo'].includes(type.toLowerCase())) {
        color = '#F28C28'; // Viento: Orange
    } else if (['choque', 'vuelco', 'atropello'].includes(type.toLowerCase())) {
        color = '#DC2626'; // Accidente: Red Alert
    } else if (type.toLowerCase().startsWith('incendio')) {
        color = '#B91C1C'; // Incendio: Dark Red
    }

    // Si es aproximada, usamos un estilo diferente (ej. borde gris o menos opacidad)
    const stroke = isApproximate ? '#9CA3AF' : 'white';
    const strokeWidth = isApproximate ? '2' : '1';

    const svgIcon = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${color}" width="32" height="32" class="marker-icon">
            <circle cx="12" cy="9" r="7" fill="white" fill-opacity="0.2" />
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" stroke="${stroke}" stroke-width="${strokeWidth}"/>
        </svg>
    `;

    return L.divIcon({
        className: 'custom-leaflet-icon',
        html: svgIcon,
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
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
    const [timeRange, setTimeRange] = useState('today'); // 'today' or 'month'
    const [activeTab, setActiveTab] = useState('wind'); // 'wind', 'accident', 'fire'
    const [loading, setLoading] = useState(false);
    const [lastSync, setLastSync] = useState(null);       // timestamp of last successful fetch
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

    const filteredIncidents = incidents.filter(incident => {
        if (activeFilters.length === 0) return true;
        // Check if the incident's category slug matches any of the active filters
        return activeFilters.includes(incident.category?.slug);
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
            fetch(`/api/incidents?range=${timeRange}`)
                .then(res => res.json())
                .then(data => {
                    // Laravel paginate() returns { data: [...], ... }
                    // Plain get() returns [...] directly
                    // We must guarantee incidents is ALWAYS an array
                    const items = data?.data ?? data;
                    setIncidents(Array.isArray(items) ? items : []);
                    setLastSync(new Date()); // Record sync time
                    setLoading(false);
                })
                .catch(err => {
                    console.error("Error fetching incidents:", err);
                    setIncidents([]);
                    setLoading(false);
                });
        };

        fetchIncidents();

        // Auto-refresh cada 5 minutos (300000 ms)
        const interval = setInterval(fetchIncidents, 300000);

        return () => clearInterval(interval);
    }, [timeRange]);

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
                className={`absolute top-0 left-0 h-full w-80 bg-white shadow-2xl transition-transform duration-300 ease-in-out z-[999] flex flex-col ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
                style={{ zIndex: 999 }}
            >
                <div className="w-full bg-white border-b border-gray-200">
                    <img src="/images/logo.jpeg" alt="ZonData Logo" className="w-full h-auto object-contain" />
                </div>

                {/* Selector de Rango de Tiempo */}
                <div className="p-4 bg-[#002D62] text-white">
                    <div className="flex items-center gap-2 mb-3">
                        <Calendar size={18} className="text-[#F28C28]" />
                        <span className="text-sm font-bold uppercase tracking-wider">Rango de Tiempo</span>
                    </div>
                    <div className="flex bg-[#001D40] rounded-lg p-1">
                        <button 
                            onClick={() => setTimeRange('today')}
                            className={`flex-1 py-2 text-xs font-bold rounded-md transition-all ${timeRange === 'today' ? 'bg-[#F28C28] text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
                        >
                            HOY
                        </button>
                        <button 
                            onClick={() => setTimeRange('month')}
                            className={`flex-1 py-2 text-xs font-bold rounded-md transition-all ${timeRange === 'month' ? 'bg-[#F28C28] text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
                        >
                            ÚLTIMO MES
                        </button>
                    </div>
                </div>
                
                <div className="flex-1 overflow-y-auto bg-[#F4F4F4]">
                    {/* Navegación por Pestañas de Categoría */}
                    <div className="bg-white border-b border-gray-200 p-2">
                        <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
                            <button 
                                onClick={() => setActiveTab('wind')}
                                className={`flex-1 flex flex-col items-center py-2 rounded-md transition-all ${activeTab === 'wind' ? 'bg-white shadow-sm text-[#F28C28]' : 'text-gray-400 hover:text-gray-600'}`}
                            >
                                <Wind size={20} />
                                <span className="text-[10px] font-bold mt-1 uppercase">Viento</span>
                            </button>
                            <button 
                                onClick={() => setActiveTab('accident')}
                                className={`flex-1 flex flex-col items-center py-2 rounded-md transition-all ${activeTab === 'accident' ? 'bg-white shadow-sm text-[#DC2626]' : 'text-gray-400 hover:text-gray-600'}`}
                            >
                                <Car size={20} />
                                <span className="text-[10px] font-bold mt-1 uppercase">Tránsito</span>
                            </button>
                            <button 
                                onClick={() => setActiveTab('fire')}
                                className={`flex-1 flex flex-col items-center py-2 rounded-md transition-all ${activeTab === 'fire' ? 'bg-white shadow-sm text-red-700' : 'text-gray-400 hover:text-gray-600'}`}
                            >
                                <Zap size={20} />
                                <span className="text-[10px] font-bold mt-1 uppercase">Siniestros</span>
                            </button>
                        </div>
                    </div>

                    {/* Área de Filtros Dinámicos */}
                    <div className="bg-white border-b border-gray-200 px-4 py-3 min-h-[160px]">
                        <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-3">
                            {activeTab === 'wind' && "Opciones de Viento"}
                            {activeTab === 'accident' && "Opciones de Tránsito"}
                            {activeTab === 'fire' && "Opciones de Siniestros"}
                        </h3>
                        
                        <div className="space-y-1">
                            {activeTab === 'wind' && windCategories.map(cat => (
                                <label key={cat.id} className="flex items-center gap-3 p-1.5 hover:bg-gray-50 rounded cursor-pointer transition-colors group">
                                    <input 
                                        type="checkbox" 
                                        className="w-4 h-4 text-[#F28C28] rounded border-gray-300 focus:ring-[#F28C28]"
                                        checked={activeFilters.includes(cat.id)}
                                        onChange={() => toggleFilter(cat.id)}
                                    />
                                    <span className="text-xs font-medium text-gray-700 group-hover:text-black">{cat.name}</span>
                                </label>
                            ))}

                            {activeTab === 'accident' && accidentCategories.map(cat => (
                                <label key={cat.id} className="flex items-center gap-3 p-1.5 hover:bg-gray-50 rounded cursor-pointer transition-colors group">
                                    <input 
                                        type="checkbox" 
                                        className="w-4 h-4 text-red-600 rounded border-gray-300 focus:ring-red-600"
                                        checked={activeFilters.includes(cat.id)}
                                        onChange={() => toggleFilter(cat.id)}
                                    />
                                    <span className="text-xs font-medium text-gray-700 group-hover:text-black">{cat.name}</span>
                                </label>
                            ))}

                            {activeTab === 'fire' && fireCategories.map(cat => (
                                <label key={cat.id} className="flex items-center gap-3 p-1.5 hover:bg-gray-50 rounded cursor-pointer transition-colors group">
                                    <input 
                                        type="checkbox" 
                                        className="w-4 h-4 text-red-700 rounded border-gray-300 focus:ring-red-700"
                                        checked={activeFilters.includes(cat.id)}
                                        onChange={() => toggleFilter(cat.id)}
                                    />
                                    <span className="text-xs font-medium text-gray-700 group-hover:text-black">{cat.name}</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    <div className="p-4">
                        {/* Barra de estado del sistema — prominente */}
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
                        
                        {filteredIncidents.length === 0 ? (
                            <p className="text-sm text-gray-500 italic">No hay incidentes para los filtros seleccionados.</p>
                        ) : (
                            <div className="space-y-3">
                                {filteredIncidents.map(incident => {
                                    // Determinar color de la tarjeta según categoría
                                    let borderColor = '#002D62'; // Por defecto
                                    if (['arboles', 'corte', 'incendio', 'techo'].includes(incident.category?.slug)) {
                                        borderColor = '#F28C28'; // Viento: Naranja
                                    } else if (['choque', 'vuelco', 'atropello'].includes(incident.category?.slug)) {
                                        borderColor = '#DC2626'; // Accidente: Rojo
                                    } else if (incident.category?.slug?.startsWith('incendio')) {
                                        borderColor = '#B91C1C'; // Incendio: Rojo Oscuro
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
                        )}
                    </div>

                    {/* CTA Dataset Completo */}
                    <div className="p-4 mt-2">
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
                <MapContainer center={position} zoom={8} className="w-full h-full" zoomControl={false}>
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
                            icon={createCustomIcon(incident.category?.slug || '', incident.is_approximate)}
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
