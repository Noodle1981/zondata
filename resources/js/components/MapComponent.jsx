import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, ZoomControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Menu, X, Wind, Zap, Car, AlertTriangle } from 'lucide-react';

// Fix for default Leaflet icons in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom Icon generator based on category type
const createCustomIcon = (type) => {
    // Determine color based on rules: Zonda (Wind/Fire) = Orange, Data (Tech/Services) = Blue, etc.
    let color = '#002D62'; // Tech Blue default
    if (['viento', 'clima', 'incendio', 'siniestro'].includes(type.toLowerCase())) {
        color = '#F28C28'; // Zonda Orange
    } else if (['accidente', 'corte'].includes(type.toLowerCase())) {
        color = '#E74C3C'; // Red Alert
    }

    const svgIcon = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${color}" width="32" height="32" class="marker-icon">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
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
    const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 768);

    // Center on entire San Juan Province
    const position = [-30.8654, -68.8895];

    useEffect(() => {
        // Fetch incidents from API
        fetch('/api/incidents')
            .then(res => res.json())
            .then(data => setIncidents(data))
            .catch(err => console.error("Error fetching incidents:", err));
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
                
                <div className="flex-1 overflow-y-auto p-4 bg-[#F4F4F4]">
                    <h2 className="font-semibold text-gray-700 mb-4 uppercase text-sm">Eventos Activos ({incidents.length})</h2>
                    
                    {incidents.length === 0 ? (
                        <p className="text-sm text-gray-500 italic">No hay incidentes reportados en este momento.</p>
                    ) : (
                        <div className="space-y-3">
                            {incidents.map(incident => (
                                <div key={incident.id} className="bg-white p-3 rounded shadow-sm border-l-4" style={{ borderColor: ['viento', 'clima', 'incendio', 'siniestro'].includes(incident.category?.slug) ? '#F28C28' : '#002D62' }}>
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
                            ))}
                        </div>
                    )}
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
                    
                    {incidents.map(incident => (
                        <Marker 
                            key={incident.id} 
                            position={[incident.latitude, incident.longitude]}
                            icon={createCustomIcon(incident.category?.slug || '')}
                        >
                            <Popup className="custom-popup">
                                <div className="p-1">
                                    <span className="inline-block px-2 py-1 bg-gray-100 text-xs font-bold rounded mb-2 text-[#002D62]">
                                        {incident.category?.name || 'Evento'}
                                    </span>
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
