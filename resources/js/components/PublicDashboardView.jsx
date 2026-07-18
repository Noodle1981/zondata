import React, { useState, useEffect, useMemo } from 'react';
import {
    Database, Car, Flame, Wind, Activity, TrendingUp, ArrowLeft,
    BarChart2, MapPin, AlertTriangle, ShieldAlert, Route, RotateCw,
    Building2, Trees, Bike, Truck, Bus, Footprints, Layers, User,
    Gauge, CarFront, Home, Wheat, Store, Factory, Leaf, Zap, ZapOff,
    Flag, Skull, Briefcase, AlertCircle, Calendar, ChevronDown, RefreshCw,
    TrendingDown, Minus, Heart, Clock, Info, Droplets, CloudRain, Snowflake
} from 'lucide-react';

// ─── Helpers ────────────────────────────────────────────────────────────────

const normalize = (text = '') =>
    text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

const matchesWords = (incident, words) => {
    const text = normalize((incident.title || '') + ' ' + (incident.description || ''));
    return words.some(w => text.includes(normalize(w)));
};

const getCategoryType = (incident) => {
    const slug = incident.category?.slug || '';
    if (['choque', 'vuelco', 'atropello', 'accidente', 'transito'].some(k => slug.includes(k))) return 'traffic';
    if (slug.includes('incendio') || slug.includes('siniestro')) return 'fire';
    return 'wind'; // Todo lo demás es climático
};

const MONTH_NAMES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];

const SAN_JUAN_DEPARTMENTS = [
    'Capital','Chimbas','Rawson','Rivadavia','Santa Lucía',
    'Pocito','Sarmiento','Albardón','Angaco','Caucete',
    'San Martín','9 de Julio','25 de Mayo','Ullum','Zonda',
    'Jáchal','Iglesia','Calingasta','Valle Fértil'
];

// ─── Sub-components ──────────────────────────────────────────────────────────

const KpiCard = ({ label, value, subtext, color = 'white', icon: Icon, pulse = false, border }) => (
    <div className={`bg-[#111A2E] p-5 rounded-2xl border ${border || 'border-white/8'} text-left flex flex-col gap-1`}>
        <div className="flex items-center justify-between">
            <span className="text-[10px] text-gray-400 uppercase font-black tracking-wider">{label}</span>
            {Icon && <Icon size={14} className="text-gray-500" />}
        </div>
        <div className="flex items-end gap-2 mt-1">
            <h4 className={`text-3xl font-black leading-none`} style={{ color }}>{value}</h4>
            {pulse && <span className="mb-1 w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />}
        </div>
        <span className="text-[10px] text-gray-500 font-medium">{subtext}</span>
    </div>
);

const SectionCard = ({ title, children, accent }) => (
    <div className={`bg-[#111A2E] p-6 rounded-2xl border border-white/5 text-left`}>
        {title && (
            <h3 className="text-sm font-black uppercase tracking-wider mb-5" style={{ color: accent || 'white' }}>
                {title}
            </h3>
        )}
        {children}
    </div>
);

const TypeCard = ({ icon: Icon, label, count, accent }) => (
    <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
        <div className="p-2.5 rounded-xl shrink-0"
            style={{ background: accent + '18', border: `1px solid ${accent}30`, color: accent }}>
            <Icon size={22} />
        </div>
        <div>
            <p className="text-[11px] text-gray-400 font-bold">{label}</p>
            <p className="text-2xl font-black text-white">{count}</p>
        </div>
    </div>
);

// Horizontal bar chart row
const BarRow = ({ label, count, pct, accent, maxCount }) => (
    <div className="flex items-center gap-3 group">
        <span className="text-[11px] text-gray-400 font-bold w-28 shrink-0 truncate">{label}</span>
        <div className="flex-1 h-5 bg-white/5 rounded-full overflow-hidden">
            <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: count === 0 ? '2px' : pct, backgroundColor: accent || '#002D62' }}
            />
        </div>
        <span className="text-[11px] font-black text-white w-6 text-right shrink-0">{count}</span>
    </div>
);

// Vertical bar chart column
const DayBar = ({ label, count, pct, accent, isToday }) => (
    <div className="flex-1 min-w-[9px] sm:min-w-[14px] flex flex-col items-center gap-1 h-full justify-end relative group">
        <div className="text-[9px] font-bold text-white opacity-0 group-hover:opacity-100 transition-opacity absolute -top-5 z-10 bg-[#0B1528] px-1.5 py-0.5 rounded border border-white/10 whitespace-nowrap">
            {count}
        </div>
        <div
            className={`w-full rounded-t-sm transition-all group-hover:brightness-125 ${isToday ? 'ring-1 ring-white/30' : ''}`}
            style={{ height: count === 0 ? '2px' : pct, backgroundColor: accent || '#002D62', minHeight: count > 0 ? '4px' : '2px' }}
        />
        <span className={`text-[7px] sm:text-[9px] font-bold block mt-0.5 ${isToday ? 'text-white' : 'text-gray-500'}`}>
            {label}
        </span>
    </div>
);

// ─── Main Component ──────────────────────────────────────────────────────────

const PublicDashboardView = () => {
    const [activeSection, setActiveSection] = useState('general');
    const [incidents, setIncidents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [periodDays, setPeriodDays] = useState(30);
    const [lastUpdated, setLastUpdated] = useState(null);

    const fetchData = () => {
        setLoading(true);
        const range = periodDays === 7 ? 'week' : 'month';
        fetch(`/api/incidents?range=${range}`)
            .then(res => res.json())
            .then(data => {
                const items = data?.data ?? data;
                setIncidents(Array.isArray(items) ? items : []);
                setLastUpdated(new Date());
                setLoading(false);
            })
            .catch(() => { setIncidents([]); setLoading(false); });
    };

    useEffect(() => { fetchData(); }, [periodDays]);

    // ── Derived Data ─────────────────────────────────────────────────────────

    const today = new Date();
    const todayStr = today.toISOString().slice(0, 10);
    const currentYear = today.getFullYear();
    const currentMonth = today.getMonth();

    // Filter by current month
    const monthlyIncidents = useMemo(() => incidents.filter(i => {
        if (!i.event_date) return false;
        const parts = i.event_date.split('-');
        return parseInt(parts[0]) === currentYear && parseInt(parts[1]) - 1 === currentMonth;
    }), [incidents, currentYear, currentMonth]);

    const allIncidents = periodDays === 7 ? incidents : monthlyIncidents;

    const trafficIncidents = useMemo(() => allIncidents.filter(i => getCategoryType(i) === 'traffic'), [allIncidents]);
    const fireIncidents    = useMemo(() => allIncidents.filter(i => getCategoryType(i) === 'fire'), [allIncidents]);
    const windIncidents    = useMemo(() => allIncidents.filter(i => getCategoryType(i) === 'wind'), [allIncidents]);

    const currentFilterIncidents = useMemo(() => {
        if (activeSection === 'traffic') return trafficIncidents;
        if (activeSection === 'fire') return fireIncidents;
        if (activeSection === 'wind') return windIncidents;
        return allIncidents;
    }, [activeSection, allIncidents, trafficIncidents, fireIncidents, windIncidents]);

    // KPI: Today's count
    const todayCount = useMemo(() =>
        allIncidents.filter(i => i.event_date?.slice(0, 10) === todayStr).length,
        [allIncidents, todayStr]
    );

    // KPI: Fatales
    const totalFatales = useMemo(() => allIncidents.filter(i => i.is_fatal).length, [allIncidents]);

    // KPI: Heridos (keyword-based from descriptions — labeled as "estimado")
    const totalHeridos = useMemo(() =>
        allIncidents.filter(i => !i.is_fatal && matchesWords(i, ['herido','herida','heridos','heridas','lesionado','lesionada','hospitalizado','trasladado','golpes','politraumatismo'])).length,
        [allIncidents]
    );

    // ── Traffic metrics ───────────────────────────────────────────────────────

    const fatalTrafficCount = useMemo(() => trafficIncidents.filter(i => i.is_fatal).length, [trafficIncidents]);
    const fatalityIndex = trafficIncidents.length > 0 ? Math.round((fatalTrafficCount / trafficIncidents.length) * 100) : 0;

    const criticalHour = useMemo(() => {
        if (trafficIncidents.length === 0) return '—';
        const bins = {
            '06–12 hs (Mañana)':   0,
            '12–18 hs (Mediodía)': 0,
            '18–21 hs (Retorno)':  0,
            '21–06 hs (Noche)':    0,
        };
        trafficIncidents.forEach(i => {
            const h = new Date(i.event_date).getHours();
            if (h >= 6  && h < 12) bins['06–12 hs (Mañana)']++;
            else if (h >= 12 && h < 18) bins['12–18 hs (Mediodía)']++;
            else if (h >= 18 && h < 21) bins['18–21 hs (Retorno)']++;
            else bins['21–06 hs (Noche)']++;
        });
        return Object.entries(bins).sort((a, b) => b[1] - a[1])[0][0];
    }, [trafficIncidents]);

    const roadCounts = useMemo(() => ({
        rutas:          trafficIncidents.filter(i => i.road_type === 'Ruta').length,
        circunvalacion: trafficIncidents.filter(i => i.road_type === 'Circunvalación').length,
        urbana:         trafficIncidents.filter(i => i.road_type === 'Urbana').length,
        alejada:        trafficIncidents.filter(i => i.road_type === 'Alejada').length,
        otro:           trafficIncidents.filter(i => !i.road_type || i.road_type === 'Otro').length,
    }), [trafficIncidents]);

    const vehicleCounts = useMemo(() => ({
        autos:      trafficIncidents.filter(i => i.has_car).length,
        camionetas: trafficIncidents.filter(i => i.has_pickup).length,
        motos:      trafficIncidents.filter(i => i.has_motorcycle).length,
        camiones:   trafficIncidents.filter(i => i.has_truck).length,
        colectivos: trafficIncidents.filter(i => i.has_bus).length,
        peatones:   trafficIncidents.filter(i => i.has_pedestrian).length,
        bicicletas: trafficIncidents.filter(i => i.has_bicycle).length,
        utilitarios:trafficIncidents.filter(i => i.has_utility).length,
    }), [trafficIncidents]);

    // ── Fire metrics ──────────────────────────────────────────────────────────

    const fireCounts = useMemo(() => {
        const c = {
            pastizales: fireIncidents.filter(i => matchesWords(i, ['pastizal','maleza','baldío','baldio','campo','yuyos','pasto','matorral'])).length,
            viviendas:  fireIncidents.filter(i => matchesWords(i, ['casa','vivienda','hogar','departamento','habitación','domicilio','casilla','edificio','residencia'])).length,
            vehiculos:  fireIncidents.filter(i => matchesWords(i, ['vehículo','vehiculo','auto','camión','camion','moto','colectivo','furgón','utilitario'])).length,
            comercios:  fireIncidents.filter(i => matchesWords(i, ['comercio','local','depósito','deposito','taller','negocio','empresa','almacén'])).length,
            industrias: fireIncidents.filter(i => matchesWords(i, ['fábrica','fabrica','galpón','galpon','industrial','planta','parque industrial'])).length,
            forestales: fireIncidents.filter(i => matchesWords(i, ['bosque','árbol','arbol','reserva','cerro','montaña','sierra'])).length,
            rurales:    fireIncidents.filter(i => matchesWords(i, ['finca','parral','cultivo','chacra','viñedo'])).length,
        };
        c.otros = Math.max(0, fireIncidents.length - Object.values(c).reduce((a, b) => a + b, 0));
        return c;
    }, [fireIncidents]);

    const topFireType = useMemo(() => {
        if (fireIncidents.length === 0) return '—';
        const labels = { pastizales:'Pastizales', viviendas:'Viviendas', vehiculos:'Vehículos', comercios:'Comercios', industrias:'Industrias', forestales:'Forestales', rurales:'Rurales', otros:'Otros' };
        const top = Object.entries(fireCounts).sort((a,b) => b[1]-a[1])[0];
        return labels[top[0]] || '—';
    }, [fireCounts, fireIncidents.length]);

    // ── Wind metrics ──────────────────────────────────────────────────────────

    const windCounts = useMemo(() => {
        const c = {
            arboles:    windIncidents.filter(i => i.category?.slug === 'arboles-caidos' || matchesWords(i, ['árbol caído','árbol cayó','arboles caidos','caída de árbol','caida de arbol'])).length,
            techos:     windIncidents.filter(i => i.category?.slug === 'techo-volado' || matchesWords(i, ['techo','chapa','voladura','voló el techo','volaron techos'])).length,
            cortes:     windIncidents.filter(i => i.category?.slug === 'corte-energia' || matchesWords(i, ['corte de luz','sin luz','apagón','apagon','sin servicio eléctrico'])).length,
            crecientes: windIncidents.filter(i => ['creciente-rio', 'creciente-quebrada', 'corte-ruta-por-agua'].includes(i.category?.slug) || matchesWords(i, ['creciente','crecida','desborde','río','rio','quebrada'])).length,
            derrumbes:  windIncidents.filter(i => ['derrumbe-ruta', 'desprendimiento-rocas', 'alud'].includes(i.category?.slug) || matchesWords(i, ['derrumbe','desprendimiento','alud','caída de rocas','caida de rocas','ruta cortada por piedras'])).length,
            tormentas:  windIncidents.filter(i => ['tormenta-electrica', 'granizo'].includes(i.category?.slug) || matchesWords(i, ['tormenta','granizo','rayo','lluvia torrencial'])).length,
            nevadas:    windIncidents.filter(i => ['nevada', 'helada'].includes(i.category?.slug) || matchesWords(i, ['nieve','nevada','nevó','nevo','helada','escarcha'])).length,
        };
        c.otros = Math.max(0, windIncidents.length - Object.values(c).reduce((a,b) => a+b, 0));
        return c;
    }, [windIncidents]);

    const topWindDamage = useMemo(() => {
        if (windIncidents.length === 0) return '—';
        const labels = { 
            arboles: 'Árboles Caídos', 
            techos: 'Techos Volados', 
            cortes: 'Cortes de Luz', 
            crecientes: 'Crecientes de Ríos', 
            derrumbes: 'Derrumbes en Rutas', 
            tormentas: 'Tormentas/Granizo', 
            nevadas: 'Nevadas/Heladas', 
            otros: 'Otros Daños' 
        };
        const top = Object.entries(windCounts).sort((a,b) => b[1]-a[1])[0];
        return labels[top[0]] || '—';
    }, [windCounts, windIncidents.length]);

    // ── Department chart ──────────────────────────────────────────────────────

    const departmentChartData = useMemo(() => {
        const counts = {};
        SAN_JUAN_DEPARTMENTS.forEach(d => { counts[d] = 0; });
        currentFilterIncidents.forEach(i => {
            const name = i.department?.name;
            if (!name) return;
            const n = normalize(name);
            const match = SAN_JUAN_DEPARTMENTS.find(d => normalize(d) === n);
            if (match) counts[match]++;
        });
        const sorted = SAN_JUAN_DEPARTMENTS
            .map(d => ({ label: d, count: counts[d] }))
            .sort((a, b) => b.count - a.count);
        const max = Math.max(...sorted.map(d => d.count), 1);
        return sorted.map(d => ({ ...d, pct: Math.round((d.count / max) * 100) + '%' }));
    }, [currentFilterIncidents]);

    // ── Daily chart ───────────────────────────────────────────────────────────

    const dailyChartData = useMemo(() => {
        const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
        const days = Array.from({ length: daysInMonth }, (_, i) => {
            const d = i + 1;
            const key = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            return { label: String(d), key, count: 0 };
        });
        currentFilterIncidents.forEach(i => {
            if (!i.event_date) return;
            const key = i.event_date.slice(0, 10);
            const found = days.find(d => d.key === key);
            if (found) found.count++;
        });
        const max = Math.max(...days.map(d => d.count), 1);
        return days.map(d => ({ ...d, pct: Math.round((d.count / max) * 100) + '%', isToday: d.key === todayStr }));
    }, [currentFilterIncidents, currentYear, currentMonth, todayStr]);

    // ── Accent color per section ──────────────────────────────────────────────

    const ACCENTS = { general: '#002D62', traffic: '#2563EB', fire: '#DC2626', wind: '#F28C28' };
    const accent = ACCENTS[activeSection];

    const SECTION_META = {
        general: { label: 'General (Todos)', icon: Database },
        traffic: { label: 'Tránsito y Choques', icon: Car },
        fire:    { label: 'Incendios', icon: Flame },
        wind:    { label: 'Viento y Clima', icon: Wind },
    };

    // ── Render ────────────────────────────────────────────────────────────────

    return (
        <div className="bg-[#0B1528] min-h-screen text-white font-sans antialiased pb-16">

            {/* ── Header ── */}
            <header className="border-b border-white/5 bg-[#0F1C34]/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4">
                <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <div className="bg-gradient-to-br from-[#002D62] to-[#001D40] px-3 py-2 rounded-xl border border-white/10 shadow-lg">
                            <span className="text-[#F28C28] font-black text-xl tracking-tight">Zon</span>
                            <span className="text-white font-black text-xl tracking-tight">Data</span>
                        </div>
                        <div className="h-6 w-px bg-white/10 hidden sm:block" />
                        <span className="bg-[#2563EB]/20 text-blue-400 text-[10px] font-bold uppercase tracking-widest py-1 px-2.5 rounded-md">
                            Dashboard Público
                        </span>
                    </div>
                    <div className="flex items-center gap-3">
                        {lastUpdated && (
                            <span className="text-[10px] text-gray-500 hidden sm:flex items-center gap-1.5">
                                <RefreshCw size={10} />
                                {lastUpdated.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })}
                            </span>
                        )}
                        <button
                            onClick={() => window.location.href = '/'}
                            className="bg-white/5 hover:bg-white/10 text-white font-bold py-2 px-4 rounded-xl text-xs transition-all border border-white/10 flex items-center gap-2 cursor-pointer active:scale-95"
                        >
                            <ArrowLeft size={14} /> Volver al Mapa
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

            <main className="max-w-7xl mx-auto px-4 sm:px-6 mt-8 space-y-6">

                {/* ── Hero Banner ── */}
                <div className="bg-gradient-to-br from-[#111A2E] to-[#15223F] p-5 sm:p-6 rounded-2xl border border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-xl sm:text-2xl font-black">
                            Estadísticas de Incidentes — San Juan
                        </h1>
                        <p className="text-sm text-gray-400 mt-1">
                            Datos en tiempo real recopilados por scraping de {' '}
                            <span className="text-white font-bold">12 medios locales</span>.
                        </p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                        {/* Period toggle */}
                        <div className="flex items-center bg-white/5 rounded-xl border border-white/10 overflow-hidden">
                            {[7, 30].map(d => (
                                <button
                                    key={d}
                                    onClick={() => setPeriodDays(d)}
                                    className={`px-3 py-2 text-xs font-black transition-all cursor-pointer ${periodDays === d ? 'bg-[#002D62] text-white' : 'text-gray-400 hover:text-white'}`}
                                >
                                    {d === 7 ? '7 días' : '30 días'}
                                </button>
                            ))}
                        </div>
                        <div className="flex items-center gap-2 bg-emerald-500/10 text-emerald-400 text-[10px] font-bold py-2 px-3 rounded-xl border border-emerald-500/20">
                            <Activity size={12} className="animate-pulse" /> En vivo
                        </div>
                    </div>
                </div>

                {/* ── Global KPI Bar ── */}
                {loading ? (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                        {[1,2,3,4].map(i => (
                            <div key={i} className="bg-[#111A2E] p-5 rounded-2xl border border-white/5 animate-pulse h-28" />
                        ))}
                    </div>
                ) : (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                        <KpiCard
                            label="Total Incidentes"
                            value={allIncidents.length}
                            subtext={periodDays === 7 ? 'Últimos 7 días' : `${MONTH_NAMES[currentMonth]} ${currentYear}`}
                            color="white"
                            icon={Database}
                            border="border-white/8"
                        />
                        <KpiCard
                            label="Fallecidos"
                            value={totalFatales}
                            subtext={totalFatales === 0 ? 'Sin fallecidos en el período' : `${totalFatales === 1 ? '1 víctima fatal' : `${totalFatales} víctimas fatales`}`}
                            color={totalFatales > 0 ? '#EF4444' : '#6B7280'}
                            icon={Skull}
                            border={totalFatales > 0 ? 'border-red-500/20' : 'border-white/5'}
                        />
                        <KpiCard
                            label="Heridos (estimado)"
                            value={totalHeridos}
                            subtext="Detectados por menciones en noticias"
                            color="#F28C28"
                            icon={Heart}
                            border="border-orange-500/15"
                        />
                        <KpiCard
                            label="Incidentes Hoy"
                            value={todayCount}
                            subtext={`${today.toLocaleDateString('es-AR', { day:'numeric', month:'short' })}`}
                            color={todayCount > 0 ? '#34D399' : '#6B7280'}
                            icon={Clock}
                            pulse={todayCount > 0}
                            border={todayCount > 0 ? 'border-emerald-500/20' : 'border-white/5'}
                        />
                    </div>
                )}

                {/* ── Category Tabs ── */}
                <div className="flex flex-wrap gap-2 bg-[#111A2E] p-2 rounded-2xl border border-white/5">
                    {Object.entries(SECTION_META).map(([key, { label, icon: Icon }]) => (
                        <button
                            key={key}
                            onClick={() => setActiveSection(key)}
                            className={`py-2.5 px-5 rounded-xl text-xs font-black transition-all flex items-center gap-2 cursor-pointer ${
                                activeSection === key
                                    ? 'text-white border border-white/10 shadow-lg'
                                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                            }`}
                            style={activeSection === key ? { backgroundColor: ACCENTS[key], boxShadow: `0 4px 20px ${ACCENTS[key]}40` } : {}}
                        >
                            <Icon size={13} /> {label}
                        </button>
                    ))}
                </div>

                {loading && (
                    <div className="flex items-center justify-center py-20 text-gray-500">
                        <RefreshCw size={20} className="animate-spin mr-3" /> Cargando datos...
                    </div>
                )}

                {!loading && (
                    <>
                        {/* ── GENERAL SECTION ── */}
                        {activeSection === 'general' && (
                            <div className="space-y-6">
                                {/* Category summary cards */}
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                    {[
                                        { key:'traffic', label:'Tránsito y Choques', count: trafficIncidents.length, icon: Car, color:'#2563EB', fatal: trafficIncidents.filter(i=>i.is_fatal).length },
                                        { key:'fire',    label:'Incendios',           count: fireIncidents.length,    icon: Flame, color:'#DC2626', fatal: fireIncidents.filter(i=>i.is_fatal).length },
                                        { key:'wind',    label:'Viento y Clima',      count: windIncidents.length,    icon: Wind,  color:'#F28C28', fatal: windIncidents.filter(i=>i.is_fatal).length },
                                    ].map(cat => (
                                        <button
                                            key={cat.key}
                                            onClick={() => setActiveSection(cat.key)}
                                            className="bg-[#111A2E] p-5 rounded-2xl border border-white/5 text-left hover:border-white/10 transition-all cursor-pointer group"
                                        >
                                            <div className="flex items-start justify-between mb-3">
                                                <div className="p-2 rounded-lg" style={{ background: cat.color + '20', color: cat.color }}>
                                                    <cat.icon size={18} />
                                                </div>
                                                <span className="text-[10px] text-gray-500 font-bold group-hover:text-gray-300 transition-colors">Ver detalle →</span>
                                            </div>
                                            <p className="text-[10px] text-gray-400 uppercase font-black tracking-wider">{cat.label}</p>
                                            <h4 className="text-3xl font-black mt-1" style={{ color: cat.color }}>{cat.count}</h4>
                                            {cat.fatal > 0 && (
                                                <span className="text-[10px] text-red-400 font-bold flex items-center gap-1 mt-1">
                                                    <Skull size={9} /> {cat.fatal} {cat.fatal === 1 ? 'fatal' : 'fatales'}
                                                </span>
                                            )}
                                            {cat.fatal === 0 && (
                                                <span className="text-[10px] text-gray-600 font-bold mt-1 block">Sin fallecidos</span>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* ── TRAFFIC SECTION ── */}
                        {activeSection === 'traffic' && (
                            <div className="space-y-5">
                                {/* KPIs */}
                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                                    <KpiCard label="Total Accidentes" value={trafficIncidents.length} subtext={periodDays === 7 ? 'Últimos 7 días' : 'Últimos 30 días'} color="#2563EB" icon={Car} border="border-blue-500/20" />
                                    <KpiCard label="Con Fallecidos"   value={fatalTrafficCount} subtext={fatalTrafficCount === 0 ? 'Sin accidentes fatales' : `Índice: ${fatalityIndex}% de siniestros`} color={fatalTrafficCount > 0 ? '#EF4444' : '#6B7280'} icon={Skull} border={fatalTrafficCount > 0 ? 'border-red-500/20' : 'border-white/5'} />
                                    <div className="bg-[#111A2E] p-5 rounded-2xl border border-blue-500/20 text-left">
                                        <span className="text-[10px] text-gray-400 uppercase font-black tracking-wider flex items-center gap-1"><Clock size={10}/> Hora Crítica</span>
                                        <h4 className="text-sm font-black mt-3 text-white leading-tight">{criticalHour}</h4>
                                        <span className="text-[10px] text-gray-500 mt-1 block">Franja con más siniestros</span>
                                    </div>
                                    <KpiCard label="Choques en Ruta"  value={roadCounts.rutas} subtext="Rutas nacionales y provinciales" color="#EAB308" icon={Route} border="border-yellow-500/15" />
                                </div>

                                {/* Road types */}
                                <SectionCard title="Accidentes por Tipo de Vía" accent="#2563EB">
                                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                                        {[
                                            { icon: Route,        label: 'Rutas Nac./Prov.',    count: roadCounts.rutas },
                                            { icon: RotateCw,     label: 'Av. Circunvalación',  count: roadCounts.circunvalacion },
                                            { icon: Building2,    label: 'Zonas Urbanas',        count: roadCounts.urbana },
                                            { icon: Trees,        label: 'Zonas Alejadas',       count: roadCounts.alejada },
                                            { icon: MapPin,       label: 'Sin Clasificar',       count: roadCounts.otro },
                                        ].map(r => <TypeCard key={r.label} {...r} accent="#2563EB" />)}
                                    </div>
                                </SectionCard>

                                {/* Vehicle types */}
                                <SectionCard title="Participación por Tipo de Vehículo / Actor" accent="#2563EB">
                                    <p className="text-[11px] text-gray-500 -mt-3 mb-4">Detectados a partir de los campos extraídos por IA en cada noticia.</p>
                                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                                        {[
                                            { icon: Car,       label: 'Autos',       count: vehicleCounts.autos },
                                            { icon: CarFront,  label: 'Camionetas',  count: vehicleCounts.camionetas },
                                            { icon: Gauge,     label: 'Motos',       count: vehicleCounts.motos },
                                            { icon: Truck,     label: 'Camiones',    count: vehicleCounts.camiones },
                                            { icon: Bus,       label: 'Colectivos',  count: vehicleCounts.colectivos },
                                            { icon: Footprints,label: 'Peatones',    count: vehicleCounts.peatones },
                                            { icon: Bike,      label: 'Bicicletas',  count: vehicleCounts.bicicletas },
                                            { icon: Briefcase, label: 'Utilitarios', count: vehicleCounts.utilitarios },
                                        ].map(v => <TypeCard key={v.label} {...v} accent="#2563EB" />)}
                                    </div>
                                </SectionCard>
                            </div>
                        )}

                        {/* ── FIRE SECTION ── */}
                        {activeSection === 'fire' && (
                            <div className="space-y-5">
                                {/* KPIs */}
                                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                                    <KpiCard label="Total Incendios" value={fireIncidents.length} subtext={periodDays === 7 ? 'Últimos 7 días' : 'Últimos 30 días'} color="#DC2626" icon={Flame} border="border-red-500/20" />
                                    <div className="bg-[#111A2E] p-5 rounded-2xl border border-red-500/20 text-left">
                                        <span className="text-[10px] text-gray-400 uppercase font-black tracking-wider">Tipo Más Frecuente</span>
                                        <h4 className="text-xl font-black mt-3 text-white truncate">{topFireType}</h4>
                                        <span className="text-[10px] text-red-400 font-bold block mt-1">Según tipo de fuente detectado</span>
                                    </div>
                                    <KpiCard label="Con Fallecidos" value={fireIncidents.filter(i=>i.is_fatal).length} subtext={fireIncidents.filter(i=>i.is_fatal).length === 0 ? 'Sin fallecidos en el período' : 'Víctimas fatales confirmadas'} color={fireIncidents.filter(i=>i.is_fatal).length > 0 ? '#EF4444' : '#6B7280'} icon={Skull} border={fireIncidents.filter(i=>i.is_fatal).length > 0 ? 'border-red-500/20' : 'border-white/5'} />
                                </div>

                                {/* Fire types */}
                                <SectionCard title="Clasificación por Tipo de Incendio" accent="#DC2626">
                                    <p className="text-[11px] text-gray-500 -mt-3 mb-4">Clasificación automática por análisis de palabras clave en el texto de cada noticia.</p>
                                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                                        {[
                                            { icon: Trees,   label: 'Pastizales / Malezas', count: fireCounts.pastizales },
                                            { icon: Home,    label: 'Casas / Viviendas',    count: fireCounts.viviendas },
                                            { icon: Car,     label: 'Vehículos',             count: fireCounts.vehiculos },
                                            { icon: Store,   label: 'Comercios',             count: fireCounts.comercios },
                                            { icon: Factory, label: 'Industrias / Galpones', count: fireCounts.industrias },
                                            { icon: Leaf,    label: 'Forestales / Cerros',   count: fireCounts.forestales },
                                            { icon: Wheat,   label: 'Rurales / Fincas',      count: fireCounts.rurales },
                                            { icon: Layers,  label: 'Otros Focos',           count: fireCounts.otros },
                                        ].map(f => <TypeCard key={f.label} {...f} accent="#DC2626" />)}
                                    </div>
                                </SectionCard>
                            </div>
                        )}

                        {/* ── WIND SECTION ── */}
                        {activeSection === 'wind' && (
                            <div className="space-y-5">
                                {/* KPIs */}
                                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                                    <KpiCard label="Total Eventos Climáticos" value={windIncidents.length} subtext={periodDays === 7 ? 'Últimos 7 días' : 'Últimos 30 días'} color="#F28C28" icon={Wind} border="border-orange-500/20" />
                                    <div className="bg-[#111A2E] p-5 rounded-2xl border border-orange-500/20 text-left">
                                        <span className="text-[10px] text-gray-400 uppercase font-black tracking-wider">Daño Más Frecuente</span>
                                        <h4 className="text-xl font-black mt-3 text-white truncate">{topWindDamage}</h4>
                                        <span className="text-[10px] text-amber-400 font-bold block mt-1">Detectado por análisis de texto</span>
                                    </div>
                                    <KpiCard label="Con Fallecidos" value={windIncidents.filter(i=>i.is_fatal).length} subtext={windIncidents.filter(i=>i.is_fatal).length === 0 ? 'Sin fallecidos en el período' : 'Víctimas confirmadas'} color={windIncidents.filter(i=>i.is_fatal).length > 0 ? '#EF4444' : '#6B7280'} icon={Skull} border={windIncidents.filter(i=>i.is_fatal).length > 0 ? 'border-red-500/20' : 'border-white/5'} />
                                </div>

                                {/* Wind damage types */}
                                <SectionCard title="Clasificación por Tipo de Daño" accent="#F28C28">
                                    <p className="text-[11px] text-gray-500 -mt-3 mb-4">Clasificación automática por análisis de palabras clave en el texto de cada noticia.</p>
                                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                                        {[
                                            { icon: Trees,       label: 'Árboles Caídos',     count: windCounts.arboles },
                                            { icon: Home,        label: 'Techos Volados',     count: windCounts.techos },
                                            { icon: ZapOff,      label: 'Cortes de Energía',  count: windCounts.cortes },
                                            { icon: Droplets,    label: 'Crecientes de Ríos', count: windCounts.crecientes },
                                            { icon: MapPin,      label: 'Derrumbes en Rutas', count: windCounts.derrumbes },
                                            { icon: CloudRain,   label: 'Tormentas / Granizo',count: windCounts.tormentas },
                                            { icon: Snowflake,   label: 'Nevadas y Heladas',  count: windCounts.nevadas },
                                            { icon: Layers,      label: 'Otros Daños',         count: windCounts.otros },
                                        ].map(w => <TypeCard key={w.label} {...w} accent="#F28C28" />)}
                                    </div>
                                </SectionCard>
                            </div>
                        )}

                        {/* ── Charts (always visible) ── */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

                            {/* Department horizontal bar chart */}
                            <SectionCard title="Incidentes por Departamento">
                                <div className="flex items-center justify-between -mt-3 mb-4">
                                    <span className="text-[10px] text-gray-500 bg-white/5 px-2 py-0.5 rounded-md">
                                        {currentFilterIncidents.length} eventos • {activeSection === 'general' ? 'Todos' : SECTION_META[activeSection].label}
                                    </span>
                                </div>
                                <div className="space-y-2">
                                    {departmentChartData.map(d => (
                                        <BarRow key={d.label} {...d} accent={accent} />
                                    ))}
                                </div>
                            </SectionCard>

                            {/* Daily bar chart */}
                            <SectionCard title={`Incidentes por Día — ${MONTH_NAMES[currentMonth]} ${currentYear}`}>
                                <div className="flex items-center justify-between -mt-3 mb-4">
                                    <span className="text-[10px] text-gray-500 bg-white/5 px-2 py-0.5 rounded-md">
                                        Tendencia de siniestralidad
                                    </span>
                                </div>
                                <div className="h-48 flex items-end gap-[2px] sm:gap-[4px] border-b border-gray-700/40 pb-1 overflow-x-auto">
                                    {dailyChartData.map(d => (
                                        <DayBar key={d.key} {...d} accent={accent} />
                                    ))}
                                </div>
                                <div className="flex justify-between text-[9px] text-gray-600 mt-3">
                                    <span>1</span>
                                    <span className="text-[#F28C28]">▲ hoy</span>
                                    <span>{dailyChartData.length}</span>
                                </div>
                            </SectionCard>
                        </div>

                        {/* ── Data source disclaimer ── */}
                        <div className="bg-[#111A2E]/60 border border-white/5 rounded-2xl p-4 flex items-start gap-3">
                            <Info size={14} className="text-gray-500 mt-0.5 shrink-0" />
                            <p className="text-[11px] text-gray-500 leading-relaxed">
                                Los datos son recopilados automáticamente mediante scraping de 12 medios de comunicación locales de San Juan. La clasificación por tipo de vehículo, daño y heridos se realiza con inteligencia artificial (Gemini) y análisis de texto. Los valores pueden no reflejar la totalidad de incidentes de la provincia.
                                {' '}<span className="text-gray-400 font-bold">Los datos de fallecidos son los únicos 100% verificados por fuente primaria.</span>
                            </p>
                        </div>

                        {/* ── CTA Banner ── */}
                        <div className="bg-gradient-to-r from-[#111A2E] to-[#1a2540] p-7 rounded-2xl border border-white/5 flex flex-col md:flex-row items-center justify-between gap-6">
                            <div className="space-y-1">
                                <h3 className="text-lg font-black">¿Querés el dataset completo de San Juan?</h3>
                                <p className="text-xs text-gray-400 max-w-xl">
                                    El acceso premium desbloquea datos históricos ilimitados, exportación en Excel/CSV/JSON y filtros avanzados por departamento, fecha y tipo de incidente.
                                </p>
                            </div>
                            <button
                                onClick={() => window.location.href = '/dashboard_premium'}
                                className="bg-[#F28C28] text-white hover:brightness-110 font-black text-xs uppercase tracking-wider py-3 px-6 rounded-xl shadow-lg shadow-[#F28C28]/25 transition-all shrink-0 cursor-pointer active:scale-95 whitespace-nowrap"
                            >
                                Adquirir Acceso Premium
                            </button>
                        </div>
                    </>
                )}
            </main>
        </div>
    );
};

export default PublicDashboardView;
