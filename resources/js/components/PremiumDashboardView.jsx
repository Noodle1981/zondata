import React, { useState, useEffect, useMemo } from 'react';
import { 
    Lock, 
    ArrowLeft, 
    Check, 
    TrendingUp, 
    Database, 
    Download,
    Filter,
    LineChart as ChartIcon,
    Sparkles,
    Shield,
    Activity,
    Wind,
    Flame,
    Droplets,
    CloudRain,
    Sun,
    MapPin,
    AlertTriangle,
    Navigation,
    Calendar,
    Thermometer,
    Compass,
    Bell,
    Mail,
    Phone,
    CheckCircle
} from 'lucide-react';

const MONTH_NAMES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

const DEPARTMENTS = [
    { id: 1, name: 'Capital' },
    { id: 2, name: 'Chimbas' },
    { id: 3, name: 'Rawson' },
    { id: 4, name: 'Rivadavia' },
    { id: 5, name: 'Santa Lucía' },
    { id: 6, name: 'Pocito' },
    { id: 7, name: 'Sarmiento' },
    { id: 8, name: 'Albardón' },
    { id: 9, name: 'Angaco' },
    { id: 10, name: 'Caucete' },
    { id: 11, name: 'San Martín' },
    { id: 12, name: '9 de Julio' },
    { id: 13, name: '25 de Mayo' },
    { id: 14, name: 'Ullum' },
    { id: 15, name: 'Zonda' },
    { id: 16, name: 'Jáchal' },
    { id: 17, name: 'Iglesia' },
    { id: 18, name: 'Calingasta' },
    { id: 19, name: 'Valle Fértil' }
];

const PHENOMENONS = [
    { value: 'zonda', label: 'Viento Zonda' },
    { value: 'viento_sur', label: 'Viento Sur' },
    { value: 'tormenta', label: 'Tormenta / Granizo' },
    { value: 'creciente', label: 'Creciente / Alud de Lodo' },
    { value: 'derrumbe', label: 'Derrumbe en Ruta' },
    { value: 'otro_climatico', label: 'Otro Climático' }
];

// MOCK DATA HISTÓRICA (San Juan 2016-2026)
const MOCK_MONTHLY_SUMMARY = [
    { month: '01', phenomenon_type: 'creciente', count: 18, avg_wind_speed: 15.4 },
    { month: '02', phenomenon_type: 'creciente', count: 22, avg_wind_speed: 12.1 },
    { month: '03', phenomenon_type: 'tormenta', count: 12, avg_wind_speed: 14.8 },
    { month: '04', phenomenon_type: 'zonda', count: 8, avg_wind_speed: 38.6 },
    { month: '05', phenomenon_type: 'zonda', count: 15, avg_wind_speed: 45.2 },
    { month: '06', phenomenon_type: 'viento_sur', count: 19, avg_wind_speed: 52.1 },
    { month: '07', phenomenon_type: 'viento_sur', count: 25, avg_wind_speed: 48.9 },
    { month: '08', phenomenon_type: 'zonda', count: 32, avg_wind_speed: 62.4 },
    { month: '09', phenomenon_type: 'zonda', count: 28, avg_wind_speed: 58.1 },
    { month: '10', phenomenon_type: 'zonda', count: 20, avg_wind_speed: 44.5 },
    { month: '11', phenomenon_type: 'viento_sur', count: 14, avg_wind_speed: 39.8 },
    { month: '12', phenomenon_type: 'creciente', count: 10, avg_wind_speed: 18.2 }
];

const MOCK_DEPT_RANKING = [
    { department_name: 'Capital', phenomenon_type: 'zonda', count: 48 },
    { department_name: 'Rawson', phenomenon_type: 'zonda', count: 39 },
    { department_name: 'Chimbas', phenomenon_type: 'viento_sur', count: 35 },
    { department_name: 'Pocito', phenomenon_type: 'tormenta', count: 32 },
    { department_name: 'Caucete', phenomenon_type: 'creciente', count: 28 },
    { department_name: 'Iglesia', phenomenon_type: 'derrumbe', count: 24 },
    { department_name: 'Calingasta', phenomenon_type: 'derrumbe', count: 22 },
    { department_name: 'Zonda', phenomenon_type: 'zonda', count: 21 },
    { department_name: 'Sarmiento', phenomenon_type: 'creciente', count: 19 },
    { department_name: 'Valle Fértil', phenomenon_type: 'tormenta', count: 18 }
];

const MOCK_ROUTES = [
    { road_name: 'Ruta Nacional 40 (Sarmiento/Mendoza)', phenomenon_type: 'creciente', count: 15 },
    { road_name: 'Ruta Nacional 150 (Paso de Agua Negra)', phenomenon_type: 'derrumbe', count: 28 },
    { road_name: 'Ruta Provincial 412 (Calingasta/Iglesia)', phenomenon_type: 'derrumbe', count: 12 },
    { road_name: 'Ruta Nacional 149 (Barreal)', phenomenon_type: 'creciente', count: 9 },
    { road_name: 'Ruta Nacional 20 (Caucete)', phenomenon_type: 'viento_sur', count: 14 }
];

const MOCK_ENSO = [
    { enso_phase: 'niño', count: 184 },
    { enso_phase: 'niña', count: 295 },
    { enso_phase: 'neutro', count: 142 }
];

const MOCK_ALERTS_EMITTED = [
    { datetime: 'Hace 3 horas', dept: 'Ullum', phen: 'Viento Zonda', details: 'Ráfagas detectadas de 64 km/h. Alerta extrema de incendio.' },
    { datetime: 'Ayer', dept: 'Iglesia (Ruta 150)', phen: 'Derrumbe en Ruta', details: 'Desprendimiento de rocas en km 82. Calzada obstruida parcialmente.' },
    { datetime: 'Hace 2 días', dept: 'Caucete', phen: 'Tormenta / Granizo', details: 'Precipitación acumulada de 14mm en 40 minutos. Crecientes de lodo.' }
];

// Generar Heatmap realista de 12 meses x 31 días
const MOCK_HEATMAP = [];
for (let m = 1; m <= 12; m++) {
    for (let d = 1; d <= 31; d++) {
        let intensity = 0;
        if (m === 8 || m === 9) { 
            intensity = Math.random() > 0.4 ? Math.floor(Math.random() * 4) : 0;
        } else if (m === 1 || m === 2) { 
            intensity = Math.random() > 0.6 ? Math.floor(Math.random() * 3) : 0;
        } else {
            intensity = Math.random() > 0.85 ? 1 : 0;
        }
        MOCK_HEATMAP.push({ month: String(m).padStart(2, '0'), day: String(d).padStart(2, '0'), count: intensity });
    }
}

const PremiumDashboardView = () => {
    const [useMock, setUseMock] = useState(true);
    const [activeTab, setActiveTab] = useState('summary');
    
    // Alert subscription form states
    const [email, setEmail] = useState('');
    const [phone, setPhone] = useState('');
    const [departmentId, setDepartmentId] = useState('');
    const [phenomenonType, setPhenomenonType] = useState('');
    const [formStatus, setFormStatus] = useState({ type: '', message: '' });

    // Live API states
    const [monthlyData, setMonthlyData] = useState([]);
    const [deptRanking, setDeptRanking] = useState([]);
    const [routeData, setRouteData] = useState([]);
    const [ensoData, setEnsoData] = useState([]);
    const [heatmapData, setHeatmapData] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!useMock) {
            setLoading(true);
            Promise.all([
                fetch('/api/analytics/monthly-summary').then(res => res.json()),
                fetch('/api/analytics/department-ranking').then(res => res.json()),
                fetch('/api/analytics/route-incidents').then(res => res.json()),
                fetch('/api/analytics/enso-comparison').then(res => res.json()),
                fetch('/api/analytics/seasonal-heatmap').then(res => res.json())
            ]).then(([monthly, depts, routes, enso, heatmap]) => {
                setMonthlyData(monthly);
                setDeptRanking(depts);
                setRouteData(routes);
                setEnsoData(enso);
                setHeatmapData(heatmap);
                setLoading(false);
            }).catch(err => {
                console.error("Error loading live analytics, falling back to demo mode:", err);
                setUseMock(true);
                setLoading(false);
            });
        }
    }, [useMock]);

    // Usar datos simulados o en vivo
    const currentMonthly = useMock ? MOCK_MONTHLY_SUMMARY : monthlyData;
    const currentDeptRanking = useMock ? MOCK_DEPT_RANKING : deptRanking;
    const currentRoutes = useMock ? MOCK_ROUTES : routeData;
    const currentEnso = useMock ? MOCK_ENSO : ensoData;
    const currentHeatmap = useMock ? MOCK_HEATMAP : heatmapData;

    // Calcular KPIs
    const totalEvents = useMemo(() => {
        return currentMonthly.reduce((acc, curr) => acc + curr.count, 0);
    }, [currentMonthly]);

    const maxWindSpeed = useMemo(() => {
        const speeds = currentMonthly.map(m => m.avg_wind_speed).filter(Boolean);
        return speeds.length ? Math.max(...speeds).toFixed(1) : '—';
    }, [currentMonthly]);

    const routeIncidentsCount = useMemo(() => {
        return currentRoutes.reduce((acc, curr) => acc + curr.count, 0);
    }, [currentRoutes]);

    const handleSubscribe = (e) => {
        e.preventDefault();
        setFormStatus({ type: 'loading', message: 'Registrando suscripción...' });

        fetch('/api/alerts/subscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                email,
                phone: phone || null,
                department_id: departmentId ? parseInt(departmentId) : null,
                phenomenon_type: phenomenonType || null
            })
        })
        .then(res => {
            if (!res.ok) throw new Error("Error en la solicitud.");
            return res.json();
        })
        .then(data => {
            setFormStatus({ type: 'success', message: '¡Te suscribiste con éxito! Las alertas comenzarán a llegar.' });
            setEmail('');
            setPhone('');
            setDepartmentId('');
            setPhenomenonType('');
        })
        .catch(err => {
            setFormStatus({ type: 'error', message: 'Error de conexión. Intente nuevamente.' });
        });
    };

    return (
        <div className="bg-[#0B1528] min-h-screen text-white font-sans antialiased relative overflow-hidden pb-12">
            
            {/* Header de ZonData Premium */}
            <header className="border-b border-white/5 bg-[#0F1C34]/80 backdrop-blur-md sticky top-0 z-40 px-6 py-4">
                <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <div className="bg-gradient-to-br from-[#F28C28] to-[#9E5A18] px-3 py-2 rounded-xl border border-[#F28C28]/20 shadow-lg">
                            <span className="text-white font-black text-xl tracking-tight">Zon</span>
                            <span className="text-[#0B1528] font-black text-xl tracking-tight">Data</span>
                        </div>
                        <div className="h-6 w-px bg-white/10 hidden sm:block" />
                        <span className="bg-[#F28C28]/20 text-[#F28C28] text-[10px] font-bold uppercase tracking-widest py-1 px-2.5 rounded-md flex items-center gap-1.5 border border-[#F28C28]/10 animate-pulse">
                            <Sparkles size={11} />
                            Inteligencia Premium Activa
                        </span>
                    </div>

                    <div className="flex items-center gap-4">
                        {/* Selector de modo Simulación vs Live */}
                        <div className="flex items-center bg-[#111A2E] px-3 py-1.5 rounded-xl border border-white/5 gap-2">
                            <span className="text-[10px] text-gray-400 font-bold uppercase">Base de Datos:</span>
                            <button
                                onClick={() => setUseMock(true)}
                                className={`px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all cursor-pointer ${useMock ? 'bg-[#F28C28] text-white' : 'text-gray-400 hover:text-white'}`}
                            >
                                Demo Histórica
                            </button>
                            <button
                                onClick={() => setUseMock(false)}
                                className={`px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all cursor-pointer ${!useMock ? 'bg-[#F28C28] text-white' : 'text-gray-400 hover:text-white'}`}
                            >
                                Servidor (Vivo)
                            </button>
                        </div>

                        <button
                            onClick={() => window.location.href = '/'}
                            className="bg-white/5 hover:bg-white/10 text-white font-bold py-2 px-4 rounded-xl text-xs transition-all border border-white/10 flex items-center gap-2 cursor-pointer"
                        >
                            <ArrowLeft size={14} /> Volver al Mapa
                        </button>
                    </div>
                </div>
            </header>

            {/* Contenido Principal */}
            <main className="max-w-7xl mx-auto px-6 mt-8 space-y-8 text-left">
                
                {/* Banner de Bienvenida Premium */}
                <div className="bg-gradient-to-r from-[#111A2E] to-[#1d2b4f] p-6 rounded-3xl border border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h2 className="text-2xl font-black">Monitoreo de Severidad y Variabilidad Climática</h2>
                        <p className="text-sm text-gray-400 mt-1">
                            Análisis multivariado de factores meteorológicos históricos de San Juan. Datos integrados de Open-Meteo y NOAA CPC.
                        </p>
                    </div>
                    {useMock && (
                        <div className="bg-amber-500/10 text-amber-400 text-xs px-4 py-2.5 rounded-xl border border-amber-500/20 flex items-center gap-2">
                            <AlertTriangle size={14} className="shrink-0" />
                            <span>Visualizando dataset histórico unificado de San Juan.</span>
                        </div>
                    )}
                </div>

                {/* Tarjetas KPI */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 flex items-center gap-4">
                        <div className="p-3 bg-[#F28C28]/10 text-[#F28C28] rounded-xl border border-[#F28C28]/20">
                            <Database size={24} />
                        </div>
                        <div>
                            <span className="text-[10px] text-gray-400 uppercase font-black tracking-wider">Historial Registrado</span>
                            <h4 className="text-3xl font-black mt-1 text-white">{totalEvents} <span className="text-xs text-gray-500">casos</span></h4>
                        </div>
                    </div>

                    <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 flex items-center gap-4">
                        <div className="p-3 bg-[#EF4444]/10 text-[#EF4444] rounded-xl border border-[#EF4444]/20">
                            <Wind size={24} />
                        </div>
                        <div>
                            <span className="text-[10px] text-gray-400 uppercase font-black tracking-wider">Ráfaga Máxima Promedio</span>
                            <h4 className="text-3xl font-black mt-1 text-white">{maxWindSpeed} <span className="text-xs text-gray-500">km/h</span></h4>
                        </div>
                    </div>

                    <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 flex items-center gap-4">
                        <div className="p-3 bg-red-400/10 text-red-400 rounded-xl border border-red-400/20">
                            <Navigation size={24} />
                        </div>
                        <div>
                            <span className="text-[10px] text-gray-400 uppercase font-black tracking-wider">Incidencias en Rutas</span>
                            <h4 className="text-3xl font-black mt-1 text-white">{routeIncidentsCount} <span className="text-xs text-gray-500">alertas</span></h4>
                        </div>
                    </div>

                    <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 flex items-center gap-4">
                        <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
                            <Activity size={24} />
                        </div>
                        <div>
                            <span className="text-[10px] text-gray-400 uppercase font-black tracking-wider">Monitoreo Minero (Ruta 150)</span>
                            <h4 className="text-xs font-black mt-2 bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded-md inline-block">Óptimo (Paso Abierto)</h4>
                        </div>
                    </div>
                </div>

                {/* Tabs de Filtro de Gráficos */}
                <div className="flex flex-wrap gap-2 border-b border-white/5 pb-1">
                    {[
                        { key: 'summary', label: 'Estacionalidad Mensual', icon: Calendar },
                        { key: 'heatmap', label: 'Heatmap de Actividad (Temporadas)', icon: Compass },
                        { key: 'enso', label: 'Influencia ENSO (El Niño/La Niña)', icon: Thermometer },
                        { key: 'routes', label: 'Rutas Mineras y Cordillera', icon: Navigation },
                        { key: 'alerts', label: 'Configurar Alertas SMS/Email', icon: Bell }
                    ].map(tab => (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key)}
                            className={`py-3 px-6 text-xs font-black uppercase tracking-wider flex items-center gap-2 cursor-pointer border-b-2 transition-all ${activeTab === tab.key ? 'border-[#F28C28] text-white bg-white/5 rounded-t-xl' : 'border-transparent text-gray-400 hover:text-white'}`}
                        >
                            <tab.icon size={13} />
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Grid de Gráficos y Tablas */}
                {loading ? (
                    <div className="py-20 flex flex-col items-center justify-center gap-4 text-gray-400">
                        <Activity className="animate-spin text-[#F28C28]" size={36} />
                        <span>Cargando datos climáticos del servidor...</span>
                    </div>
                ) : (
                    <div className="space-y-6">
                        
                        {/* TAB 1: ESTACIONALIDAD MENSUAL */}
                        {activeTab === 'summary' && (
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fadeIn">
                                <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 lg:col-span-2 flex flex-col justify-between">
                                    <div>
                                        <h3 className="text-sm font-black uppercase tracking-wider text-[#F28C28]">Línea de Tiempo de Frecuencia Mensual</h3>
                                        <p className="text-xs text-gray-400 mt-1">Número de incidentes registrados agrupados por mes calendario para detectar ciclos de vientos y crecientes.</p>
                                    </div>
                                    <div className="h-64 flex items-end gap-2 border-b border-gray-700/40 pb-2 mt-8">
                                        {currentMonthly.map((m, idx) => {
                                            const max = Math.max(...currentMonthly.map(x => x.count), 1);
                                            const pct = (m.count / max) * 100 + '%';
                                            return (
                                                <div key={idx} className="flex-1 flex flex-col items-center gap-1 group relative h-full justify-end">
                                                    <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute -top-8 bg-[#0B1528] border border-white/10 px-2 py-1 rounded text-[10px] font-bold z-10 whitespace-nowrap">
                                                        {m.count} incidentes
                                                    </div>
                                                    <div 
                                                        className="w-full bg-gradient-to-t from-[#F28C28]/40 to-[#F28C28] rounded-t-md hover:brightness-125 transition-all"
                                                        style={{ height: pct }}
                                                    />
                                                    <span className="text-[10px] text-gray-500 font-bold block mt-1">{MONTH_NAMES[parseInt(m.month) - 1]}</span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                    <div className="flex justify-between text-[10px] text-gray-600 mt-4">
                                        <span>Enero</span>
                                        <span>Diciembre</span>
                                    </div>
                                </div>

                                <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 flex flex-col justify-between">
                                    <div>
                                        <h3 className="text-sm font-black uppercase tracking-wider text-white">Velocidad Promedio de Viento (km/h)</h3>
                                        <p className="text-xs text-gray-400 mt-1">Velocidad media registrada durante los picos diarios del viento de cada mes.</p>
                                    </div>
                                    <div className="space-y-3 mt-6">
                                        {currentMonthly.map((m, idx) => {
                                            const maxSpeed = Math.max(...currentMonthly.map(x => x.avg_wind_speed), 1);
                                            const speedPct = (m.avg_wind_speed / maxSpeed) * 100 + '%';
                                            const barColor = m.avg_wind_speed > 40 ? '#EF4444' : '#F28C28';
                                            return (
                                                <div key={idx} className="flex items-center gap-3">
                                                    <span className="text-[10px] font-bold text-gray-400 w-8">{MONTH_NAMES[parseInt(m.month) - 1]}</span>
                                                    <div className="flex-1 h-3 bg-white/5 rounded-full overflow-hidden">
                                                        <div 
                                                            className="h-full rounded-full transition-all duration-500"
                                                            style={{ width: speedPct, backgroundColor: barColor }}
                                                        />
                                                    </div>
                                                    <span className="text-[10px] font-black text-white w-12 text-right">{m.avg_wind_speed.toFixed(1)} km/h</span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* TAB 2: HEATMAP ESTACIONAL */}
                        {activeTab === 'heatmap' && (
                            <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 animate-fadeIn">
                                <div>
                                    <h3 className="text-sm font-black uppercase tracking-wider text-[#F28C28]">Matriz Térmica Estacional (Mes vs Día)</h3>
                                    <p className="text-xs text-gray-400 mt-1">Muestra la densidad de incidentes por día del año. Permite identificar visualmente las temporadas críticas (viento Zonda invernal y crecientes veraniegas).</p>
                                </div>

                                <div className="mt-8 overflow-x-auto pb-4">
                                    <div className="min-w-[650px] space-y-[4px]">
                                        <div className="flex gap-[3px] items-center mb-1">
                                            <span className="w-10 text-[9px] font-black text-gray-500 uppercase">Mes</span>
                                            {Array.from({ length: 31 }, (_, i) => (
                                                <span key={i} className="flex-1 text-center text-[8px] font-bold text-gray-500">{i + 1}</span>
                                            ))}
                                        </div>

                                        {Array.from({ length: 12 }, (_, monthIdx) => {
                                            const mStr = String(monthIdx + 1).padStart(2, '0');
                                            return (
                                                <div key={monthIdx} className="flex gap-[3px] items-center">
                                                    <span className="w-10 text-[10px] font-bold text-gray-400">{MONTH_NAMES[monthIdx]}</span>
                                                    {Array.from({ length: 31 }, (_, dayIdx) => {
                                                        const dStr = String(dayIdx + 1).padStart(2, '0');
                                                        const entry = currentHeatmap.find(h => h.month === mStr && h.day === dStr);
                                                        const count = entry ? entry.count : 0;
                                                        
                                                        let bgClass = "bg-[#0B1528]";
                                                        if (count === 1) bgClass = "bg-[#F28C28]/30";
                                                        else if (count === 2) bgClass = "bg-[#F28C28]/60";
                                                        else if (count >= 3) bgClass = "bg-[#EF4444]";

                                                        return (
                                                            <div 
                                                                key={dayIdx} 
                                                                className={`flex-1 aspect-square rounded-sm transition-all hover:ring-1 hover:ring-white/50 cursor-pointer relative group ${bgClass}`}
                                                            >
                                                                <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute -top-8 left-1/2 -translate-x-1/2 bg-[#0B1528] border border-white/10 px-2 py-1 rounded text-[9px] font-bold z-10 whitespace-nowrap">
                                                                    {dayIdx + 1} {MONTH_NAMES[monthIdx]}: {count} incidentes
                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>

                                <div className="flex items-center justify-end gap-4 text-[10px] text-gray-500 mt-4 border-t border-white/5 pt-4">
                                    <div className="flex items-center gap-1.5">
                                        <div className="w-3 h-3 bg-[#0B1528] rounded-sm" />
                                        <span>Sin Incidentes</span>
                                    </div>
                                    <div className="flex items-center gap-1.5">
                                        <div className="w-3 h-3 bg-[#F28C28]/30 rounded-sm" />
                                        <span>Bajo</span>
                                    </div>
                                    <div className="flex items-center gap-1.5">
                                        <div className="w-3 h-3 bg-[#F28C28]/60 rounded-sm" />
                                        <span>Moderado</span>
                                    </div>
                                    <div className="flex items-center gap-1.5">
                                        <div className="w-3 h-3 bg-[#EF4444] rounded-sm" />
                                        <span>Severo</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* TAB 3: INFLUENCIA ENSO */}
                        {activeTab === 'enso' && (
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fadeIn">
                                {currentEnso.map((phase, idx) => {
                                    const colors = {
                                        'niño': { border: 'border-red-500/20', text: 'text-red-400', bg: 'from-red-500/5 to-transparent', label: 'El Niño (Cálido)', desc: 'Asociado a mayores nevadas cordilleranas y crecientes veraniegas extremas.' },
                                        'niña': { border: 'border-blue-500/20', text: 'text-blue-400', bg: 'from-blue-500/5 to-transparent', label: 'La Niña (Fría)', desc: 'Asociado a sequías severas e incrementos del 35% en incendios de pastizales.' },
                                        'neutro': { border: 'border-gray-500/20', text: 'text-gray-400', bg: 'from-gray-500/5 to-transparent', label: 'Fase Neutro', desc: 'Valores promedio históricos de eventos climáticos regionales.' }
                                    };
                                    
                                    const meta = colors[phase.enso_phase] || colors['neutro'];
                                    
                                    return (
                                        <div key={idx} className={`bg-gradient-to-b ${meta.bg} p-6 rounded-2xl border ${meta.border} text-left flex flex-col justify-between`}>
                                            <div>
                                                <span className={`text-[10px] uppercase font-black tracking-wider ${meta.text}`}>{meta.label}</span>
                                                <h4 className="text-4xl font-black mt-2 text-white">{phase.count} <span className="text-xs text-gray-500">incidentes</span></h4>
                                                <p className="text-xs text-gray-400 mt-4 leading-relaxed">{meta.desc}</p>
                                            </div>
                                            <div className="mt-8 border-t border-white/5 pt-4">
                                                <span className="text-[10px] text-gray-500 font-bold block">Frecuencia Relativa: {((phase.count / totalEvents) * 100).toFixed(1)}% del total</span>
                                            </div>
                                        </div>
                                    );
                                })}

                                <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 md:col-span-3 text-left">
                                    <h3 className="text-sm font-black uppercase tracking-wider text-white flex items-center gap-2">
                                        <Thermometer size={14} className="text-[#F28C28]" /> Correlación ONI (Oceanic Niño Index) y Zondata
                                    </h3>
                                    <p className="text-xs text-gray-400 mt-2 leading-relaxed">
                                        El fenómeno de El Niño-Oscilación del Sur (ENSO) altera dramáticamente el régimen de vientos Zonda e incendios en San Juan. Durante años <b>La Niña</b>, la extrema sequedad en la precordillera alimenta la susceptibilidad ante vientos secos, disparando incendios de pastizales y de viviendas. Por su parte, los períodos de <b>El Niño</b> tienden a generar mayor humedad relativa general en primavera pero desatan tormentas eléctricas inusualmente severas con crecientes de lodo en verano.
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* TAB 4: RUTAS MINERAS Y CORDILLERA */}
                        {activeTab === 'routes' && (
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fadeIn">
                                <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 lg:col-span-2 text-left">
                                    <div>
                                        <h3 className="text-sm font-black uppercase tracking-wider text-[#F28C28]">Corredores y Rutas Mineras Afectadas</h3>
                                        <p className="text-xs text-gray-400 mt-1">Muestra los tramos viales con mayores reportes de cortes de calzada por crecientes o bloqueos por derrumbes de rocas.</p>
                                    </div>

                                    <div className="mt-6 space-y-4">
                                        {currentRoutes.map((route, idx) => (
                                            <div key={idx} className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center justify-between gap-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2 bg-yellow-500/10 text-yellow-500 rounded-lg border border-yellow-500/20">
                                                        <Navigation size={16} />
                                                    </div>
                                                    <div>
                                                        <span className="text-xs font-black text-white">{route.road_name}</span>
                                                        <span className="text-[10px] text-gray-400 block mt-0.5">Predominio de: <b className="text-amber-400">{route.phenomenon_type}</b></span>
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <span className="text-lg font-black text-white">{route.count}</span>
                                                    <span className="text-[9px] text-gray-500 block">bloqueos</span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 text-left flex flex-col justify-between">
                                    <div>
                                        <h3 className="text-sm font-black uppercase tracking-wider text-white">Severidad por Departamento</h3>
                                        <p className="text-xs text-gray-400 mt-1">Ranking de jurisdicciones con mayor número de incidentes climáticos acumulados.</p>
                                    </div>
                                    <div className="space-y-3 mt-6">
                                        {currentDeptRanking.slice(0, 5).map((dept, idx) => {
                                            const max = Math.max(...currentDeptRanking.map(x => x.count), 1);
                                            const pct = (dept.count / max) * 100 + '%';
                                            return (
                                                <div key={idx} className="flex items-center justify-between gap-3 text-xs">
                                                    <span className="font-bold text-gray-300 w-24 truncate">{dept.department_name}</span>
                                                    <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                                                        <div 
                                                            className="h-full bg-[#F28C28] rounded-full" 
                                                            style={{ width: pct }}
                                                        />
                                                    </div>
                                                    <span className="font-black text-white w-6 text-right shrink-0">{dept.count}</span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* TAB 5: CONFIGURACIÓN DE ALERTAS */}
                        {activeTab === 'alerts' && (
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fadeIn">
                                <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 lg:col-span-2 text-left">
                                    <h3 className="text-sm font-black uppercase tracking-wider text-[#F28C28] flex items-center gap-2">
                                        <Bell size={16} /> Suscribirse a Alertas Climáticas
                                    </h3>
                                    <p className="text-xs text-gray-400 mt-1">Configura notificaciones inmediatas en tu e-mail o teléfono para anticipar riesgos meteorológicos.</p>

                                    <form onSubmit={handleSubscribe} className="mt-6 space-y-4">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div className="flex flex-col gap-1">
                                                <label className="text-[10px] text-gray-400 uppercase font-bold">Correo Electrónico *</label>
                                                <div className="relative">
                                                    <Mail size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                                                    <input 
                                                        type="email" 
                                                        required
                                                        placeholder="ejemplo@correo.com"
                                                        value={email}
                                                        onChange={(e) => setEmail(e.target.value)}
                                                        className="w-full bg-[#0B1528] border border-white/10 rounded-xl py-2 px-10 text-xs text-white focus:outline-none focus:border-[#F28C28]"
                                                    />
                                                </div>
                                            </div>

                                            <div className="flex flex-col gap-1">
                                                <label className="text-[10px] text-gray-400 uppercase font-bold">Teléfono (WhatsApp/SMS)</label>
                                                <div className="relative">
                                                    <Phone size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
                                                    <input 
                                                        type="tel" 
                                                        placeholder="+54 9 264 ..."
                                                        value={phone}
                                                        onChange={(e) => setPhone(e.target.value)}
                                                        className="w-full bg-[#0B1528] border border-white/10 rounded-xl py-2 px-10 text-xs text-white focus:outline-none focus:border-[#F28C28]"
                                                    />
                                                </div>
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div className="flex flex-col gap-1">
                                                <label className="text-[10px] text-gray-400 uppercase font-bold">Departamento de San Juan</label>
                                                <select 
                                                    value={departmentId}
                                                    onChange={(e) => setDepartmentId(e.target.value)}
                                                    className="w-full bg-[#0B1528] border border-white/10 rounded-xl py-2 px-3.5 text-xs text-white focus:outline-none focus:border-[#F28C28]"
                                                >
                                                    <option value="">Todos los departamentos</option>
                                                    {DEPARTMENTS.map(d => (
                                                        <option key={d.id} value={d.id}>{d.name}</option>
                                                    ))}
                                                </select>
                                            </div>

                                            <div className="flex flex-col gap-1">
                                                <label className="text-[10px] text-gray-400 uppercase font-bold">Fenómeno de Alerta</label>
                                                <select 
                                                    value={phenomenonType}
                                                    onChange={(e) => setPhenomenonType(e.target.value)}
                                                    className="w-full bg-[#0B1528] border border-white/10 rounded-xl py-2 px-3.5 text-xs text-white focus:outline-none focus:border-[#F28C28]"
                                                >
                                                    <option value="">Todos los fenómenos</option>
                                                    {PHENOMENONS.map(p => (
                                                        <option key={p.value} value={p.value}>{p.label}</option>
                                                    ))}
                                                </select>
                                            </div>
                                        </div>

                                        {formStatus.message && (
                                            <div className={`p-3 rounded-xl text-xs flex items-center gap-2 ${formStatus.type === 'success' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : formStatus.type === 'error' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-white/5 text-gray-300'}`}>
                                                {formStatus.type === 'success' && <CheckCircle size={14} />}
                                                <span>{formStatus.message}</span>
                                            </div>
                                        )}

                                        <button 
                                            type="submit"
                                            className="bg-[#F28C28] text-white hover:brightness-110 font-black text-xs uppercase tracking-wider py-3 px-6 rounded-xl transition-all cursor-pointer active:scale-95"
                                        >
                                            Suscribirse
                                        </button>
                                    </form>
                                </div>

                                <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 text-left flex flex-col justify-between">
                                    <div>
                                        <h3 className="text-sm font-black uppercase tracking-wider text-white">Alertas Emitidas</h3>
                                        <p className="text-xs text-gray-400 mt-1">Historial del sistema de notificaciones.</p>
                                    </div>
                                    <div className="space-y-4 mt-6">
                                        {MOCK_ALERTS_EMITTED.map((alert, idx) => (
                                            <div key={idx} className="bg-[#0B1528] p-3.5 rounded-xl border border-white/5">
                                                <div className="flex justify-between items-center mb-1">
                                                    <span className="text-[10px] text-gray-500 font-bold">{alert.datetime}</span>
                                                    <span className="text-[9px] uppercase font-black tracking-wider bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded">{alert.phen}</span>
                                                </div>
                                                <p className="text-xs font-bold text-white">{alert.dept}</p>
                                                <p className="text-[11px] text-gray-400 mt-1 leading-relaxed">{alert.details}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                    </div>
                )}

                {/* Reporte de Inteligencia y Descarga */}
                <div className="bg-gradient-to-r from-[#111A2E] to-[#122240] p-8 rounded-3xl border border-white/5 flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="space-y-2">
                        <h3 className="text-lg font-black flex items-center gap-2">
                            <Download size={18} className="text-[#F28C28]" /> Exportar Informes Climáticos Regionales
                        </h3>
                        <p className="text-xs text-gray-400 max-w-xl">
                            Descarga el dataset completo de incidentes climáticos enriquecidos en formato XLSX o CSV. Compatible con modelos de análisis GIS de minería y vialidad.
                        </p>
                    </div>
                    <button 
                        onClick={() => alert("Simulación Premium: Iniciando exportación de 917 filas de datos enriquecidos...")}
                        className="bg-[#F28C28] text-white hover:brightness-110 font-black text-xs uppercase tracking-wider py-3.5 px-6 rounded-xl shadow-lg shadow-[#F28C28]/25 transition-all shrink-0 cursor-pointer active:scale-95"
                    >
                        Exportar Dataset Completo (.CSV)
                    </button>
                </div>

            </main>
        </div>
    );
};

export default PremiumDashboardView;
