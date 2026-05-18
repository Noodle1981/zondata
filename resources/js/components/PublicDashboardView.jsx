import React, { useState, useEffect } from 'react';
import { 
    Database, 
    Car, 
    Flame, 
    Wind, 
    Activity, 
    TrendingUp, 
    ArrowLeft, 
    Check,
    BarChart2,
    Calendar,
    MapPin,
    Clock
} from 'lucide-react';

const PublicDashboardView = () => {
    const [activeSection, setActiveSection] = useState('general');
    const [incidents, setIncidents] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Fetch real incidents from backend API
        fetch('/api/incidents')
            .then(res => res.json())
            .then(data => {
                setIncidents(data || []);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error fetching dashboard incidents:", err);
                setLoading(false);
            });
    }, []);

    // Filter incidents of the last 30 days based on their type
    const getFilteredIncidents = (type) => {
        if (type === 'general') return incidents;
        if (type === 'traffic') return incidents.filter(i => i.category === 'transito');
        if (type === 'fire') return incidents.filter(i => i.category === 'incendio');
        if (type === 'wind') return incidents.filter(i => i.category === 'viento');
        return incidents;
    };

    const displayIncidents = getFilteredIncidents(activeSection);

    return (
        <div className="bg-[#0B1528] min-h-screen text-white font-sans antialiased pb-16">
            {/* Header Superior */}
            <header className="border-b border-white/5 bg-[#0F1C34]/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4">
                <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <div className="bg-gradient-to-br from-[#002D62] to-[#001D40] p-2.5 rounded-xl border border-white/10 shadow-lg">
                            <span className="text-[#F28C28] font-black text-xl tracking-tight">Zon</span>
                            <span className="text-white font-black text-xl tracking-tight">Data</span>
                        </div>
                        <div className="h-6 w-px bg-white/10 hidden sm:block"></div>
                        <span className="bg-[#2563EB]/20 text-blue-400 text-[10px] font-bold uppercase tracking-widest py-1 px-2.5 rounded-md">
                            Dashboard Público
                        </span>
                    </div>

                    <div className="flex items-center gap-3">
                        <button 
                            onClick={() => window.location.href = '/'}
                            className="bg-white/5 hover:bg-white/10 text-white font-bold py-2 px-4 rounded-xl text-xs transition-all border border-white/10 flex items-center gap-2 cursor-pointer active:scale-95"
                        >
                            <ArrowLeft size={14} />
                            Volver al Mapa Interactivo
                        </button>
                        <button 
                            onClick={() => window.location.href = '/dashboard_premium'}
                            className="bg-[#F28C28] hover:brightness-110 text-white font-black py-2 px-4 rounded-xl text-xs transition-all flex items-center gap-2 cursor-pointer shadow-lg shadow-[#F28C28]/25 active:scale-95"
                        >
                            Ver Premium
                        </button>
                    </div>
                </div>
            </header>

            {/* Contenido Principal */}
            <main className="max-w-7xl mx-auto px-6 mt-8">
                {/* Banner de Presentación */}
                <div className="bg-gradient-to-br from-[#111A2E] to-[#15223F] p-6 rounded-2xl border border-white/5 text-left mb-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div>
                        <h2 className="text-2xl font-black">Estadísticas de Incidentes (Últimos 30 días)</h2>
                        <p className="text-sm text-gray-400 mt-1">Monitoreo histórico agregado y análisis preliminar para la toma de decisiones en San Juan.</p>
                    </div>
                    <div className="flex items-center gap-2 bg-[#F28C28]/10 text-[#F28C28] text-xs font-bold py-2.5 px-4 rounded-xl border border-[#F28C28]/20 shrink-0">
                        <Activity size={14} className="animate-pulse" />
                        Actualizado en Tiempo Real
                    </div>
                </div>

                {/* Selector de Categorías */}
                <div className="flex flex-wrap gap-2 bg-[#111A2E] p-2 rounded-2xl border border-white/5 mb-8">
                    <button
                        onClick={() => setActiveSection('general')}
                        className={`py-2.5 px-5 rounded-xl text-xs font-black transition-all flex items-center gap-2 cursor-pointer ${activeSection === 'general' ? 'bg-[#002D62] text-white border border-white/10 shadow-lg shadow-[#002D62]/40' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                    >
                        <Database size={13} />
                        General (Todos)
                    </button>
                    <button
                        onClick={() => setActiveSection('traffic')}
                        className={`py-2.5 px-5 rounded-xl text-xs font-black transition-all flex items-center gap-2 cursor-pointer ${activeSection === 'traffic' ? 'bg-[#2563EB] text-white shadow-lg shadow-[#2563EB]/40' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                    >
                        <Car size={13} />
                        Tránsito y Choques
                    </button>
                    <button
                        onClick={() => setActiveSection('fire')}
                        className={`py-2.5 px-5 rounded-xl text-xs font-black transition-all flex items-center gap-2 cursor-pointer ${activeSection === 'fire' ? 'bg-[#DC2626] text-white shadow-lg shadow-[#DC2626]/40' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                    >
                        <Flame size={13} />
                        Incendios
                    </button>
                    <button
                        onClick={() => setActiveSection('wind')}
                        className={`py-2.5 px-5 rounded-xl text-xs font-black transition-all flex items-center gap-2 cursor-pointer ${activeSection === 'wind' ? 'bg-[#F28C28] text-white shadow-lg shadow-[#F28C28]/40' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
                    >
                        <Wind size={13} />
                        Viento y Clima
                    </button>
                </div>

                {/* Contadores Dinámicos */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    {activeSection === 'general' && (
                        <>
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-white/5 text-left">
                                <span className="text-xs text-gray-400 uppercase font-bold">Total Incidentes</span>
                                <h4 className="text-3xl font-black mt-1.5 text-[#F28C28]">{incidents.length}</h4>
                                <span className="text-[10px] text-emerald-500 flex items-center gap-1 mt-1.5 font-bold">
                                    <TrendingUp size={12} /> +12% este mes
                                </span>
                            </div>
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-white/5 text-left">
                                <span className="text-xs text-gray-400 uppercase font-bold">Mayor Incidencia</span>
                                <h4 className="text-xl font-black mt-3 text-white truncate">Incendios</h4>
                                <span className="text-[10px] text-red-400 font-bold block mt-1.5">58% de eventos totales</span>
                            </div>
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-white/5 text-left">
                                <span className="text-xs text-gray-400 uppercase font-bold">Zona Crítica</span>
                                <h4 className="text-xl font-black mt-3 text-white truncate">Sarmiento</h4>
                                <span className="text-[10px] text-gray-400 block mt-1.5">Dpto. Sarmiento</span>
                            </div>
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-white/5 text-left">
                                <span className="text-xs text-gray-400 uppercase font-bold">Prom. Respuesta</span>
                                <h4 className="text-3xl font-black mt-1.5 text-white">14 min</h4>
                                <span className="text-[10px] text-emerald-500 font-bold block mt-1.5">Óptimo provincial</span>
                            </div>
                        </>
                    )}
                    {activeSection === 'traffic' && (
                        <>
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-[#2563EB]/20 text-left">
                                <span className="text-xs text-gray-400 uppercase font-bold">Total Accidentes</span>
                                <h4 className="text-3xl font-black mt-1.5 text-[#2563EB]">{getFilteredIncidents('traffic').length}</h4>
                                <span className="text-[10px] text-amber-500 font-bold block mt-1.5">Últimos 30 días</span>
                            </div>
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-[#2563EB]/20 text-left">
                                <span className="text-xs text-gray-400 uppercase font-bold">Índice Fatalidad</span>
                                <h4 className="text-3xl font-black mt-1.5 text-white">0%</h4>
                                <span className="text-[10px] text-emerald-500 font-bold block mt-1.5">Sin fallecidos</span>
                            </div>
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-[#2563EB]/20 text-left">
                                <span className="text-xs text-gray-400 uppercase font-bold">Horario Crítico</span>
                                <h4 className="text-xl font-black mt-3 text-white truncate">18-20 hs</h4>
                                <span className="text-[10px] text-gray-400 block mt-1.5">Retorno laboral</span>
                            </div>
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-[#2563EB]/20 text-left">
                                <span className="text-xs text-gray-400 uppercase font-bold">Ruta Conflictiva</span>
                                <h4 className="text-xl font-black mt-3 text-white truncate">Ruta 40</h4>
                                <span className="text-[10px] text-amber-400 font-bold block mt-1.5">Acceso Sur</span>
                            </div>
                        </>
                    )}
                    {activeSection === 'fire' && (
                        <>
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-[#DC2626]/20 text-left">
                                <span className="text-xs text-gray-400 uppercase font-bold">Total Incendios</span>
                                <h4 className="text-3xl font-black mt-1.5 text-[#DC2626]">{getFilteredIncidents('fire').length}</h4>
                                <span className="text-[10px] text-red-500 font-bold block mt-1.5">Últimos 30 días</span>
                            </div>
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-[#DC2626]/20 text-left">
                                <span className="text-xs text-gray-400 uppercase font-bold">Foco Común</span>
                                <h4 className="text-xl font-black mt-3 text-white truncate">Pastizales</h4>
                                <span className="text-[10px] text-red-400 font-bold block mt-1.5">75% de los focos</span>
                            </div>
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-[#DC2626]/20 text-left">
                                <span className="text-xs text-gray-400 uppercase font-bold">Área Afectada</span>
                                <h4 className="text-xl font-black mt-3 text-white truncate">14.5 Ha</h4>
                                <span className="text-[10px] text-gray-400 block mt-1.5">Zonas rurales</span>
                            </div>
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-[#DC2626]/20 text-left">
                                <span className="text-xs text-gray-400 uppercase font-bold">Resp. Bomberos</span>
                                <h4 className="text-3xl font-black mt-1.5 text-white">12 min</h4>
                                <span className="text-[10px] text-emerald-500 font-bold block mt-1.5">Despliegue rápido</span>
                            </div>
                        </>
                    )}
                    {activeSection === 'wind' && (
                        <>
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-[#F28C28]/20 text-left">
                                <span className="text-xs text-gray-400 uppercase font-bold">Total Alertas</span>
                                <h4 className="text-3xl font-black mt-1.5 text-[#F28C28]">{getFilteredIncidents('wind').length}</h4>
                                <span className="text-[10px] text-amber-500 font-bold block mt-1.5">Zonda / Sur</span>
                            </div>
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-[#F28C28]/20 text-left">
                                <span className="text-xs text-gray-400 uppercase font-bold">Ráfaga Máxima</span>
                                <h4 className="text-xl font-black mt-3 text-white truncate">92 km/h</h4>
                                <span className="text-[10px] text-[#F28C28] font-bold block mt-1.5">Viento Zonda</span>
                            </div>
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-[#F28C28]/20 text-left">
                                <span className="text-xs text-gray-400 uppercase font-bold">Cortes de Luz</span>
                                <h4 className="text-xl font-black mt-3 text-white truncate">3 zonas</h4>
                                <span className="text-[10px] text-gray-400 block mt-1.5">Rivadavia / S. Lucía</span>
                            </div>
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-[#F28C28]/20 text-left">
                                <span className="text-xs text-gray-400 uppercase font-bold">Clases Susp.</span>
                                <h4 className="text-3xl font-black mt-1.5 text-white">1 vez</h4>
                                <span className="text-[10px] text-red-400 font-bold block mt-1.5">Recomendación Civil</span>
                            </div>
                        </>
                    )}
                </div>

                {/* Dashboard Grid Principal */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                    {/* Insights & Bulletins */}
                    <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 text-left flex flex-col justify-between h-fit lg:min-h-[350px]">
                        <div>
                            <h4 className="text-xs font-black text-[#F28C28] uppercase tracking-wider mb-4">Detalle de Sección</h4>
                            
                            {activeSection === 'general' && (
                                <div className="space-y-4">
                                    <h5 className="font-bold text-base text-white">Análisis Agregado</h5>
                                    <p className="text-xs text-gray-400 leading-relaxed">
                                        El mes en curso presenta una alta actividad de focos de incendio en malezas debido a la baja humedad estacional. Los siniestros viales se mantienen en la media provincial.
                                    </p>
                                    <div className="p-4 bg-[#0B1528] rounded-xl border border-white/5 text-xs text-gray-300">
                                        ⚡ <b>Dato Clave</b>: Dpto. Sarmiento concentra el 40% de los incidentes totales de este período.
                                    </div>
                                </div>
                            )}

                            {activeSection === 'traffic' && (
                                <div className="space-y-4">
                                    <h5 className="font-bold text-base text-[#2563EB]">Siniestralidad Vial</h5>
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

                            {activeSection === 'fire' && (
                                <div className="space-y-4">
                                    <h5 className="font-bold text-base text-[#DC2626]">Focos de Fuego</h5>
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

                            {activeSection === 'wind' && (
                                <div className="space-y-4">
                                    <h5 className="font-bold text-base text-[#F28C28]">Fenómenos Climáticos</h5>
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

                        {/* Botón de conversión */}
                        <button 
                            onClick={() => window.location.href = '/dashboard_premium'}
                            className="w-full mt-6 bg-[#F28C28] text-white text-xs font-black uppercase tracking-wider py-3 rounded-xl shadow-lg shadow-[#F28C28]/25 hover:brightness-110 active:scale-95 transition-all cursor-pointer"
                        >
                            Desbloquear Histórico Completo ➜
                        </button>
                    </div>

                    {/* Gráfico Analítico */}
                    <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 text-left lg:col-span-2 flex flex-col justify-between">
                        <div>
                            <h4 className="text-sm font-bold mb-4">
                                {activeSection === 'general' && "Incidentes Totales por Semana (Últimos 30 días)"}
                                {activeSection === 'traffic' && "Volumen Horario de Colisiones Viales (Últimos 30 días)"}
                                {activeSection === 'fire' && "Focos Ígneos por Sub-categoría (Últimos 30 días)"}
                                {activeSection === 'wind' && "Intensidad de Viento en Ráfagas Máximas (km/h)"}
                            </h4>
                            <div className="h-60 flex items-end gap-4 md:gap-8 pt-6 border-b border-gray-700/50">
                                {activeSection === 'general' && [
                                    { label: "Semana 1", val: "35%", color: "bg-[#002D62]" },
                                    { label: "Semana 2", val: "55%", color: "bg-[#002D62]" },
                                    { label: "Semana 3", val: "85%", color: "bg-[#F28C28]" },
                                    { label: "Semana 4", val: "45%", color: "bg-[#002D62]" }
                                ].map((d, i) => (
                                    <div key={i} className="flex-1 flex flex-col items-center gap-2 group">
                                        <div className={`w-full ${d.color} rounded-t-lg transition-all group-hover:brightness-110`} style={{ height: d.val }}></div>
                                        <span className="text-xs text-gray-400 font-bold truncate max-w-full">{d.label}</span>
                                    </div>
                                ))}

                                {activeSection === 'traffic' && [
                                    { label: "Mañana", val: "25%", color: "bg-[#2563EB]" },
                                    { label: "Mediodía", val: "40%", color: "bg-[#2563EB]" },
                                    { label: "Tarde", val: "95%", color: "bg-[#2563EB]" },
                                    { label: "Noche", val: "30%", color: "bg-[#2563EB]" }
                                ].map((d, i) => (
                                    <div key={i} className="flex-1 flex flex-col items-center gap-2 group">
                                        <div className={`w-full ${d.color} rounded-t-lg transition-all group-hover:brightness-110`} style={{ height: d.val }}></div>
                                        <span className="text-xs text-gray-400 font-bold truncate max-w-full">{d.label}</span>
                                    </div>
                                ))}

                                {activeSection === 'fire' && [
                                    { label: "Pastizales", val: "90%", color: "bg-[#DC2626]" },
                                    { label: "Viviendas", val: "20%", color: "bg-[#DC2626]" },
                                    { label: "Vehículos", val: "45%", color: "bg-[#DC2626]" },
                                    { label: "Otros", val: "15%", color: "bg-[#DC2626]" }
                                ].map((d, i) => (
                                    <div key={i} className="flex-1 flex flex-col items-center gap-2 group">
                                        <div className={`w-full ${d.color} rounded-t-lg transition-all group-hover:brightness-110`} style={{ height: d.val }}></div>
                                        <span className="text-xs text-gray-400 font-bold truncate max-w-full">{d.label}</span>
                                    </div>
                                ))}

                                {activeSection === 'wind' && [
                                    { label: "Capital", val: "45%", color: "bg-[#F28C28]" },
                                    { label: "Rivadavia", val: "85%", color: "bg-[#F28C28]" },
                                    { label: "Chimbas", val: "30%", color: "bg-[#F28C28]" },
                                    { label: "Zonda", val: "95%", color: "bg-[#F28C28]" }
                                ].map((d, i) => (
                                    <div key={i} className="flex-1 flex flex-col items-center gap-2 group">
                                        <div className={`w-full ${d.color} rounded-t-lg transition-all group-hover:brightness-110`} style={{ height: d.val }}></div>
                                        <span className="text-xs text-gray-400 font-bold truncate max-w-full">{d.label}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="flex items-center justify-between text-xs text-gray-400 mt-4">
                            <span>* Datos agregados preliminares</span>
                            <span className="text-[#F28C28] font-bold">ZonData Public Analytics</span>
                        </div>
                    </div>
                </div>

                {/* Listado de Ocurrencias Recientes del Dataset */}
                <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 text-left mb-8">
                    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mb-6">
                        <div>
                            <h3 className="text-lg font-black">Historial de Ocurrencias (Últimos 30 días)</h3>
                            <p className="text-xs text-gray-400 mt-1">Registros capturados y clasificados automáticamente por la inteligencia de ZonData.</p>
                        </div>
                        <span className="bg-[#002D62] text-white text-[10px] font-bold py-1.5 px-3 rounded-lg border border-white/5">
                            Mostrando {displayIncidents.length} de {incidents.length} totales
                        </span>
                    </div>

                    {loading ? (
                        <div className="py-12 text-center text-gray-400 flex flex-col items-center gap-3">
                            <Activity size={24} className="animate-spin text-[#F28C28]" />
                            <span>Cargando eventos...</span>
                        </div>
                    ) : displayIncidents.length === 0 ? (
                        <div className="py-12 text-center text-gray-500">
                            Ningún evento registrado en esta categoría en los últimos 30 días.
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {displayIncidents.map(inc => {
                                let borderColor = 'border-l-gray-500';
                                let catLabel = 'Otro';
                                let badgeColor = 'bg-gray-500/20 text-gray-400';

                                if (inc.category === 'viento') {
                                    borderColor = 'border-l-[#F28C28]';
                                    catLabel = 'Clima';
                                    badgeColor = 'bg-[#F28C28]/20 text-[#F28C28]';
                                } else if (inc.category === 'transito') {
                                    borderColor = 'border-l-[#2563EB]';
                                    catLabel = 'Tránsito';
                                    badgeColor = 'bg-[#2563EB]/20 text-[#2563EB]';
                                } else if (inc.category === 'incendio') {
                                    borderColor = 'border-l-[#DC2626]';
                                    catLabel = 'Incendio';
                                    badgeColor = 'bg-[#DC2626]/20 text-red-500';
                                }

                                return (
                                    <div 
                                        key={inc.id}
                                        className={`bg-[#0B1528] p-4 rounded-xl border border-white/5 border-l-4 ${borderColor} hover:border-white/10 transition-all flex flex-col justify-between gap-3`}
                                    >
                                        <div>
                                            <div className="flex items-center justify-between gap-2 mb-2">
                                                <span className={`text-[9px] font-black uppercase tracking-wider py-0.5 px-2 rounded-md ${badgeColor}`}>
                                                    {catLabel}
                                                </span>
                                                <span className="text-[10px] text-gray-400 flex items-center gap-1">
                                                    <Clock size={10} />
                                                    {inc.relative_time || 'Hace poco'}
                                                </span>
                                            </div>
                                            <h4 className="font-bold text-sm text-white line-clamp-2 leading-snug">{inc.title}</h4>
                                        </div>

                                        <div className="border-t border-white/5 pt-2 flex items-center justify-between text-[10px] text-gray-400">
                                            <span className="flex items-center gap-1">
                                                <MapPin size={10} />
                                                {inc.locality || 'San Juan'}
                                            </span>
                                            <span className="flex items-center gap-1">
                                                <Calendar size={10} />
                                                {inc.date ? new Date(inc.date).toLocaleDateString() : 'Reciente'}
                                            </span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* Banner CTA Conversión */}
                <div className="bg-gradient-to-r from-[#111A2E] to-[#15223F] p-8 rounded-2xl border border-white/5 text-left flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="space-y-1">
                        <h3 className="text-lg font-black">¿Quieres descargar toda la base de datos de San Juan?</h3>
                        <p className="text-xs text-gray-400 max-w-xl">El acceso premium desbloquea el dataset completo en formatos Excel, CSV y JSON con filtros avanzados por departamento y localidad.</p>
                    </div>
                    <button 
                        onClick={() => window.location.href = '/dashboard_premium'}
                        className="bg-[#F28C28] text-white hover:brightness-110 font-black text-xs uppercase tracking-wider py-3 px-6 rounded-xl shadow-lg shadow-[#F28C28]/25 transition-all shrink-0 cursor-pointer active:scale-95"
                    >
                        Adquirir Acceso Premium
                    </button>
                </div>
            </main>
        </div>
    );
};

export default PublicDashboardView;
