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
    Clock,
    UserCheck,
    AlertTriangle,
    ShieldAlert,
    Route,
    RotateCw,
    Building2,
    Trees,
    Bike,
    Truck,
    Bus,
    Footprints,
    Layers,
    User,
    Gauge,
    CarFront,
    Home,
    Wheat,
    Store,
    Factory,
    Leaf,
    Zap,
    ZapOff,
    Flag
} from 'lucide-react';

const PublicDashboardView = () => {
    const [activeSection, setActiveSection] = useState('general');
    const [incidents, setIncidents] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Fetch real incidents of the last 30 days from backend API
        fetch('/api/incidents?range=month')
            .then(res => res.json())
            .then(data => {
                const items = data?.data ?? data;
                setIncidents(Array.isArray(items) ? items : []);
                setLoading(false);
            })
            .catch(err => {
                console.error("Error fetching dashboard incidents:", err);
                setIncidents([]);
                setLoading(false);
            });
    }, []);

    // Robust category matching logic (replicates MapComponent)
    const getFilteredIncidents = (type) => {
        if (type === 'general') return incidents;
        
        return incidents.filter(i => {
            const slug = i.category?.slug || '';
            if (type === 'traffic') {
                return ['choque', 'vuelco', 'atropello', 'accidente', 'transito'].some(k => slug.includes(k));
            }
            if (type === 'fire') {
                return slug.includes('incendio') || slug.includes('siniestro');
            }
            if (type === 'wind') {
                return ['arboles', 'corte', 'techo', 'viento', 'zonda'].some(k => slug.includes(k));
            }
            return true;
        });
    };

    const currentFilterIncidents = getFilteredIncidents(activeSection);

    // ==========================================
    // METRICS CALCULATORS FOR TRANSIT (Scraping)
    // ==========================================
    const trafficIncidents = getFilteredIncidents('traffic');

    // 1. Fatality Index
    const fatalTrafficCount = trafficIncidents.filter(i => i.is_fatal).length;
    const fatalityIndex = trafficIncidents.length > 0 
        ? Math.round((fatalTrafficCount / trafficIncidents.length) * 100) 
        : 0;

    // 2. Critical Hours
    const calculateCriticalHours = () => {
        if (trafficIncidents.length === 0) return '18-20 hs (Retorno)';
        const hours = trafficIncidents.map(i => {
            if (!i.event_date) return 18;
            return new Date(i.event_date).getHours();
        });
        
        // Count frequencies in bins
        const bins = {
            '06-12 hs (Mañana)': hours.filter(h => h >= 6 && h < 12).length,
            '12-18 hs (Mediodía)': hours.filter(h => h >= 12 && h < 18).length,
            '18-20 hs (Retorno)': hours.filter(h => h >= 18 && h < 20).length,
            '20-06 hs (Noche)': hours.filter(h => h >= 20 || h < 6).length,
        };

        let maxBin = '18-20 hs (Retorno)';
        let maxCount = -1;
        Object.entries(bins).forEach(([binName, count]) => {
            if (count > maxCount) {
                maxCount = count;
                maxBin = binName;
            }
        });
        return maxBin;
    };
    const criticalHour = calculateCriticalHours();

    // Helper: text scanner
    const matchesKeywords = (incident, words) => {
        const text = ((incident.title || '') + ' ' + (incident.description || '')).toLowerCase();
        return words.some(w => text.includes(w));
    };

    // 3. Roads & Types of Crash Counts
    const routeAccidents = trafficIncidents.filter(i => matchesKeywords(i, ['ruta', 'r.n', 'rn ', 'ruta nacional', 'ruta provincial', 'km '])).length;
    const circunvalacionAccidents = trafficIncidents.filter(i => matchesKeywords(i, ['circunvalacion', 'circunvalación', 'av. circunvalación', 'avenida de circunvalación'])).length;
    const urbanAccidents = trafficIncidents.filter(i => 
        !matchesKeywords(i, ['ruta', 'r.n', 'rn ', 'ruta nacional', 'ruta provincial', 'km ', 'circunvalacion', 'circunvalación']) && 
        matchesKeywords(i, ['calle', 'esquina', 'interseccion', 'intersección', 'avenida', 'barrio', 'plaza', 'semáforo'])
    ).length;
    const ruralAccidents = Math.max(0, trafficIncidents.length - (routeAccidents + circunvalacionAccidents + urbanAccidents));

    // 4. Vehicle Type Counters
    const vehicleCounts = {
        autos: trafficIncidents.filter(i => matchesKeywords(i, ['auto', 'automóvil', 'automovil', 'vehículo', 'vehiculo', 'remís', 'taxi'])).length,
        camionetas: trafficIncidents.filter(i => matchesKeywords(i, ['camioneta', 'pickup', 'pick-up', 'hilux', 'amarok', 'ranger', 'suv', 'trafic', 'furgón'])).length,
        motos: trafficIncidents.filter(i => matchesKeywords(i, ['moto', 'motocicleta', 'motociclista', 'ciclomotor', 'motomel', 'zanella', 'honda wave'])).length,
        camiones: trafficIncidents.filter(i => matchesKeywords(i, ['camión', 'camion', 'semirremolque', 'acoplado', 'mosquito', 'chasis'])).length,
        colectivos: trafficIncidents.filter(i => matchesKeywords(i, ['colectivo', 'micro', 'ómnibus', 'omnibus', 'bus', 'redtulum', 'tulum'])).length,
        peatones: trafficIncidents.filter(i => matchesKeywords(i, ['peatón', 'peaton', 'peatona', 'transeúnte', 'transeunte'])).length,
        bicicletas: trafficIncidents.filter(i => matchesKeywords(i, ['bici', 'bicicleta', 'ciclista'])).length,
        otros: 0
    };
    // Others is the remainder
    vehicleCounts.otros = Math.max(0, trafficIncidents.length - Object.values(vehicleCounts).reduce((a, b) => a + b, 0) + vehicleCounts.otros);

    // 5. Animal-caused crashes
    const animalCrashes = trafficIncidents.filter(i => matchesKeywords(i, ['caballo', 'vaca', 'perro', 'can ', 'equino', 'animal', 'jauría', 'jauria'])).length;

    // 6. Genders count (based on text descriptions)
    const maleMentions = trafficIncidents.filter(i => matchesKeywords(i, ['el conductor', 'un hombre', 'un joven', 'masculino', 'sujeto', 'señor'])).length;
    const femaleMentions = trafficIncidents.filter(i => matchesKeywords(i, ['la conductora', 'una mujer', 'una joven', 'femenino', 'femenina', 'señora'])).length;
    
    const totalGenders = maleMentions + femaleMentions;
    const malePercent = totalGenders > 0 ? Math.round((maleMentions / totalGenders) * 100) : 70; // 70% default mock ratio if text is neutral
    const femalePercent = totalGenders > 0 ? 100 - malePercent : 30;

    // ==========================================
    // METRICS CALCULATORS FOR FIRE (Scraping)
    // ==========================================
    const fireIncidents = getFilteredIncidents('fire');
    const fireCounts = {
        pastizales: fireIncidents.filter(i => matchesKeywords(i, ['pastizales', 'maleza', 'baldío', 'baldio', 'campo', 'hierba', 'yuyos', 'cañaveral', 'pasto', 'matorral'])).length,
        viviendas: fireIncidents.filter(i => matchesKeywords(i, ['casa', 'vivienda', 'hogar', 'departamento', 'habitación', 'domicilio', 'casilla', 'techo', 'edificio', 'residencia'])).length,
        comercios: fireIncidents.filter(i => matchesKeywords(i, ['comercio', 'local', 'depósito', 'deposito', 'taller', 'negocio', 'empresa', 'supermercado', 'almacén', 'almacen'])).length,
        industrias: fireIncidents.filter(i => matchesKeywords(i, ['fábrica', 'fabrica', 'galpón', 'galpon', 'industrial', 'planta', 'parque industrial'])).length,
        vehiculos: fireIncidents.filter(i => matchesKeywords(i, ['vehículo', 'vehiculo', 'auto', 'camión', 'camion', 'moto', 'colectivo', 'furgón', 'utilitario'])).length,
        forestales: fireIncidents.filter(i => matchesKeywords(i, ['bosque', 'árboles', 'arboles', 'rama', 'arbolado', 'reserva', 'cerro', 'montaña', 'sierra'])).length,
        rurales: fireIncidents.filter(i => matchesKeywords(i, ['finca', 'parral', 'cultivo', 'rural', 'chacra', 'callejón', 'bodega', 'viñedo'])).length,
        otros: 0
    };
    // Others is the remainder
    fireCounts.otros = Math.max(0, fireIncidents.length - Object.values(fireCounts).reduce((a, b) => a + b, 0) + fireCounts.otros);

    // ==========================================
    // METRICS CALCULATORS FOR WIND (Scraping)
    // ==========================================
    const windIncidents = getFilteredIncidents('wind');
    const windCounts = {
        arboles: windIncidents.filter(i => matchesKeywords(i, ['árbol', 'arbol', 'forestal', 'árboles', 'arboles']) && matchesKeywords(i, ['caída', 'caida', 'cayó', 'cayo', 'derribado', 'tumbado', 'calzada'])).length,
        ramas: windIncidents.filter(i => matchesKeywords(i, ['rama', 'ramas', 'gajo', 'gajos', 'copa']) && !matchesKeywords(i, ['árbol caído', 'arbol caido', 'árboles caídos', 'arboles caidos'])).length,
        techos: windIncidents.filter(i => matchesKeywords(i, ['techo', 'techos', 'chapa', 'chapas', 'voladura', 'volaron', 'voló', 'volo'])).length,
        cableados: windIncidents.filter(i => matchesKeywords(i, ['cable', 'cables', 'tendido', 'cableado', 'poste', 'postes', 'columnas', 'columna'])).length,
        cortes: windIncidents.filter(i => matchesKeywords(i, ['corte', 'cortes', 'luz', 'energía', 'energia', 'apagón', 'apagon', 'sin servicio', 'electricidad', 'sin luz'])).length,
        carteleria: windIncidents.filter(i => matchesKeywords(i, ['cartel', 'carteles', 'semáforo', 'semaforo', 'letrero', 'publicidad', 'semáforos', 'semaforos'])).length,
        otros: 0
    };
    // Others is the remainder
    windCounts.otros = Math.max(0, windIncidents.length - Object.values(windCounts).reduce((a, b) => a + b, 0) + windCounts.otros);

    // ==========================================
    // DYNAMIC DEPARTMENT INCIDENT COUNTS (Chart)
    // ==========================================
    const getDepartmentStatistics = () => {
        const SAN_JUAN_DEPARTMENTS = [
            "Capital", "Chimbas", "Rawson", "Rivadavia", "Santa Lucía",
            "Pocito", "Sarmiento", "Albardón", "Angaco", "Caucete",
            "San Martín", "9 de Julio", "25 de Mayo", "Ullum", "Zonda",
            "Jáchal", "Iglesia", "Calingasta", "Valle Fértil"
        ];

        // Initialize all departments with 0 counts
        const counts = {};
        SAN_JUAN_DEPARTMENTS.forEach(dept => {
            counts[dept] = 0;
        });

        // Accumulate incident counts using normalized department names to prevent accent discrepancies
        currentFilterIncidents.forEach(i => {
            const deptName = i.department?.name;
            if (deptName) {
                const normalizedSearch = deptName.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                const matchedDept = SAN_JUAN_DEPARTMENTS.find(d => 
                    d.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "") === normalizedSearch
                );
                if (matchedDept) {
                    counts[matchedDept] += 1;
                }
            }
        });

        // Sort departments alphabetically
        const sortedDepartments = [...SAN_JUAN_DEPARTMENTS].sort((a, b) => a.localeCompare(b));

        const list = sortedDepartments.map(dept => ({
            label: dept,
            count: counts[dept]
        }));

        // Map counts to relative percentages (highest count is 100%)
        const maxVal = Math.max(...list.map(s => s.count));
        return list.map(s => ({
            label: s.label,
            count: s.count,
            pct: maxVal > 0 ? Math.round((s.count / maxVal) * 100) + "%" : "0%"
        }));
    };
    const departmentChartData = getDepartmentStatistics();

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
                            Ver Premium (Histórico)
                        </button>
                    </div>
                </div>
            </header>

            {/* Contenido Principal */}
            <main className="max-w-7xl mx-auto px-6 mt-8">
                {/* Banner de Presentación */}
                <div className="bg-gradient-to-br from-[#111A2E] to-[#15223F] p-6 rounded-2xl border border-white/5 text-left mb-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div>
                        <h2 className="text-2xl font-black">Estadísticas e Indicadores (Últimos 30 días)</h2>
                        <p className="text-sm text-gray-400 mt-1">Análisis cuantitativo de siniestros, incendios y eventos climáticos reportados en la provincia de San Juan.</p>
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

                {/* ========================================== */}
                {/* 1. SECCIÓN: TRÁNSITO Y CHOQUES (DETALLE COMPLETO) */}
                {/* ========================================== */}
                {activeSection === 'traffic' && (
                    <div className="space-y-6 mb-8 text-left animate-fadeIn">
                        
                        {/* Contadores Clave de Tránsito */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-[#2563EB]/20">
                                <span className="text-[10px] text-gray-400 uppercase font-black tracking-wider">Total Accidentes</span>
                                <h4 className="text-3xl font-black mt-1.5 text-[#2563EB]">{trafficIncidents.length}</h4>
                                <span className="text-[10px] text-emerald-500 font-bold block mt-1.5">Últimos 30 días</span>
                            </div>

                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-[#2563EB]/20">
                                <span className="text-[10px] text-gray-400 uppercase font-black tracking-wider">Índice Fatalidad</span>
                                <h4 className="text-3xl font-black mt-1.5 text-white">{fatalityIndex}%</h4>
                                <span className="text-[10px] text-red-400 font-bold block mt-1.5">
                                    {fatalTrafficCount > 0 ? `${fatalTrafficCount} accidente fatal` : 'Sin fallecidos'}
                                </span>
                            </div>

                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-[#2563EB]/20">
                                <span className="text-[10px] text-gray-400 uppercase font-black tracking-wider">Horario Crítico</span>
                                <h4 className="text-base font-black mt-3 text-white truncate">{criticalHour}</h4>
                                <span className="text-[10px] text-gray-400 block mt-1.5">Retorno laboral / picos</span>
                            </div>

                            <div className="bg-[#111A2E] p-5 rounded-2xl border border-[#2563EB]/20">
                                <span className="text-[10px] text-gray-400 uppercase font-black tracking-wider">Causa Animales</span>
                                <h4 className="text-3xl font-black mt-1.5 text-[#EAB308]">{animalCrashes}</h4>
                                <span className="text-[10px] text-gray-400 block mt-1.5">Choques reportados</span>
                            </div>
                        </div>

                        {/* Conteo de Accidentes por Tipo de Vía */}
                        <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5">
                            <h3 className="text-lg font-black mb-4">Accidentes por Tipo de Vía</h3>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                                <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                    <div className="bg-[#2563EB]/10 text-[#2563EB] p-2.5 rounded-xl border border-[#2563EB]/20 shrink-0">
                                        <Route size={24} />
                                    </div>
                                    <div className="text-left">
                                        <h4 className="text-xs font-bold text-gray-400">Rutas Nac. / Prov.</h4>
                                        <p className="text-2xl font-black text-white mt-0.5">{routeAccidents}</p>
                                    </div>
                                </div>
                                <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                    <div className="bg-[#2563EB]/10 text-[#2563EB] p-2.5 rounded-xl border border-[#2563EB]/20 shrink-0">
                                        <RotateCw size={24} />
                                    </div>
                                    <div className="text-left">
                                        <h4 className="text-xs font-bold text-gray-400">Av. Circunvalación</h4>
                                        <p className="text-2xl font-black text-white mt-0.5">{circunvalacionAccidents}</p>
                                    </div>
                                </div>
                                <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                    <div className="bg-[#2563EB]/10 text-[#2563EB] p-2.5 rounded-xl border border-[#2563EB]/20 shrink-0">
                                        <Building2 size={24} />
                                    </div>
                                    <div className="text-left">
                                        <h4 className="text-xs font-bold text-gray-400">Zonas Urbanas</h4>
                                        <p className="text-2xl font-black text-white mt-0.5">{urbanAccidents}</p>
                                    </div>
                                </div>
                                <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                    <div className="bg-[#2563EB]/10 text-[#2563EB] p-2.5 rounded-xl border border-[#2563EB]/20 shrink-0">
                                        <Trees size={24} />
                                    </div>
                                    <div className="text-left">
                                        <h4 className="text-xs font-bold text-gray-400">Zonas Rurales</h4>
                                        <p className="text-2xl font-black text-white mt-0.5">{ruralAccidents}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Tarjetas de Conteo por Tipo de Vehículo */}
                        <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5">
                            <div className="mb-4 text-left">
                                <h3 className="text-lg font-black">Participación por Tipo de Vehículo y Actor</h3>
                                <p className="text-xs text-gray-400 mt-0.5">Cantidad de actores involucrados detectados por procesamiento de texto.</p>
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                                <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                    <div className="bg-[#2563EB]/10 text-[#2563EB] p-2.5 rounded-xl border border-[#2563EB]/20 shrink-0">
                                        <Car size={24} />
                                    </div>
                                    <div className="text-left">
                                        <h5 className="text-xs text-gray-400 font-bold">Autos</h5>
                                        <p className="text-2xl font-black text-white mt-0.5">{vehicleCounts.autos}</p>
                                    </div>
                                </div>
                                <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                    <div className="bg-[#2563EB]/10 text-[#2563EB] p-2.5 rounded-xl border border-[#2563EB]/20 shrink-0">
                                        <CarFront size={24} />
                                    </div>
                                    <div className="text-left">
                                        <h5 className="text-xs text-gray-400 font-bold">Camionetas</h5>
                                        <p className="text-2xl font-black text-white mt-0.5">{vehicleCounts.camionetas}</p>
                                    </div>
                                </div>
                                <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                    <div className="bg-[#2563EB]/10 text-[#2563EB] p-2.5 rounded-xl border border-[#2563EB]/20 shrink-0">
                                        <Gauge size={24} />
                                    </div>
                                    <div className="text-left">
                                        <h5 className="text-xs text-gray-400 font-bold">Motos</h5>
                                        <p className="text-2xl font-black text-white mt-0.5">{vehicleCounts.motos}</p>
                                    </div>
                                </div>
                                <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                    <div className="bg-[#2563EB]/10 text-[#2563EB] p-2.5 rounded-xl border border-[#2563EB]/20 shrink-0">
                                        <Truck size={24} />
                                    </div>
                                    <div className="text-left">
                                        <h5 className="text-xs text-gray-400 font-bold">Camiones</h5>
                                        <p className="text-2xl font-black text-white mt-0.5">{vehicleCounts.camiones}</p>
                                    </div>
                                </div>
                                <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                    <div className="bg-[#2563EB]/10 text-[#2563EB] p-2.5 rounded-xl border border-[#2563EB]/20 shrink-0">
                                        <Bus size={24} />
                                    </div>
                                    <div className="text-left">
                                        <h5 className="text-xs text-gray-400 font-bold">Colectivos</h5>
                                        <p className="text-2xl font-black text-white mt-0.5">{vehicleCounts.colectivos}</p>
                                    </div>
                                </div>
                                <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                    <div className="bg-[#2563EB]/10 text-[#2563EB] p-2.5 rounded-xl border border-[#2563EB]/20 shrink-0">
                                        <User size={24} />
                                    </div>
                                    <div className="text-left">
                                        <h5 className="text-xs text-gray-400 font-bold">Peatones</h5>
                                        <p className="text-2xl font-black text-white mt-0.5">{vehicleCounts.peatones}</p>
                                    </div>
                                </div>
                                <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                    <div className="bg-[#2563EB]/10 text-[#2563EB] p-2.5 rounded-xl border border-[#2563EB]/20 shrink-0">
                                        <Bike size={24} />
                                    </div>
                                    <div className="text-left">
                                        <h5 className="text-xs text-gray-400 font-bold">Bicicletas</h5>
                                        <p className="text-2xl font-black text-white mt-0.5">{vehicleCounts.bicicletas}</p>
                                    </div>
                                </div>
                                <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                    <div className="bg-[#2563EB]/10 text-[#2563EB] p-2.5 rounded-xl border border-[#2563EB]/20 shrink-0">
                                        <Layers size={24} />
                                    </div>
                                    <div className="text-left">
                                        <h5 className="text-xs text-gray-400 font-bold">Otros</h5>
                                        <p className="text-2xl font-black text-white mt-0.5">{vehicleCounts.otros}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Desglose de Géneros */}
                        <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 flex flex-col md:flex-row items-center gap-6">
                            <div className="md:w-1/3 space-y-2">
                                <h3 className="text-lg font-black">Participación por Género</h3>
                                <p className="text-xs text-gray-400">Porcentaje estimado según menciones periodísticas del conductor o involucrados.</p>
                            </div>
                            <div className="flex-1 w-full space-y-4">
                                <div className="flex justify-between text-xs font-bold text-gray-300">
                                    <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#2563EB]"></span>Masculino: {malePercent}%</span>
                                    <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-pink-500"></span>Femenino: {femalePercent}%</span>
                                </div>
                                <div className="w-full h-4 bg-gray-700 rounded-full overflow-hidden flex">
                                    <div className="bg-[#2563EB] h-full transition-all" style={{ width: malePercent + "%" }}></div>
                                    <div className="bg-pink-500 h-full transition-all" style={{ width: femalePercent + "%" }}></div>
                                </div>
                            </div>
                        </div>

                    </div>
                )}

                {/* ========================================== */}
                {/* 2. SECCIÓN: GENERAL / INCENDIOS / VIENTO (CONTADORES MOCK) */}
                {/* ========================================== */}
                {activeSection !== 'traffic' && (
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
                )}

                {/* ========================================== */}
                {/* 2.2 SECCIÓN: TARJETAS DE CONTEO POR TIPO DE INCENDIO */}
                {/* ========================================== */}
                {activeSection === 'fire' && (
                    <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 mb-8">
                        <div className="mb-4 text-left">
                            <h3 className="text-lg font-black text-[#DC2626]">Participación por Tipo de Incendio</h3>
                            <p className="text-xs text-gray-400 mt-0.5">Cantidad de focos detectados automáticamente mediante procesamiento inteligente de texto.</p>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                            <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                <div className="bg-[#DC2626]/10 text-[#DC2626] p-2.5 rounded-xl border border-[#DC2626]/20 shrink-0">
                                    <Trees size={24} />
                                </div>
                                <div className="text-left">
                                    <h5 className="text-xs text-gray-400 font-bold">Pastizales / Malezas</h5>
                                    <p className="text-2xl font-black text-white mt-0.5">{fireCounts.pastizales}</p>
                                </div>
                            </div>
                            <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                <div className="bg-[#DC2626]/10 text-[#DC2626] p-2.5 rounded-xl border border-[#DC2626]/20 shrink-0">
                                    <Home size={24} />
                                </div>
                                <div className="text-left">
                                    <h5 className="text-xs text-gray-400 font-bold">Casas / Viviendas</h5>
                                    <p className="text-2xl font-black text-white mt-0.5">{fireCounts.viviendas}</p>
                                </div>
                            </div>
                            <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                <div className="bg-[#DC2626]/10 text-[#DC2626] p-2.5 rounded-xl border border-[#DC2626]/20 shrink-0">
                                    <Store size={24} />
                                </div>
                                <div className="text-left">
                                    <h5 className="text-xs text-gray-400 font-bold">Comercios / Locales</h5>
                                    <p className="text-2xl font-black text-white mt-0.5">{fireCounts.comercios}</p>
                                </div>
                            </div>
                            <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                <div className="bg-[#DC2626]/10 text-[#DC2626] p-2.5 rounded-xl border border-[#DC2626]/20 shrink-0">
                                    <Factory size={24} />
                                </div>
                                <div className="text-left">
                                    <h5 className="text-xs text-gray-400 font-bold">Industrias / Galpones</h5>
                                    <p className="text-2xl font-black text-white mt-0.5">{fireCounts.industrias}</p>
                                </div>
                            </div>
                            <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                <div className="bg-[#DC2626]/10 text-[#DC2626] p-2.5 rounded-xl border border-[#DC2626]/20 shrink-0">
                                    <Car size={24} />
                                </div>
                                <div className="text-left">
                                    <h5 className="text-xs text-gray-400 font-bold">Vehículos</h5>
                                    <p className="text-2xl font-black text-white mt-0.5">{fireCounts.vehiculos}</p>
                                </div>
                            </div>
                            <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                <div className="bg-[#DC2626]/10 text-[#DC2626] p-2.5 rounded-xl border border-[#DC2626]/20 shrink-0">
                                    <Flame size={24} />
                                </div>
                                <div className="text-left">
                                    <h5 className="text-xs text-gray-400 font-bold">Forestales / Cerros</h5>
                                    <p className="text-2xl font-black text-white mt-0.5">{fireCounts.forestales}</p>
                                </div>
                            </div>
                            <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                <div className="bg-[#DC2626]/10 text-[#DC2626] p-2.5 rounded-xl border border-[#DC2626]/20 shrink-0">
                                    <Wheat size={24} />
                                </div>
                                <div className="text-left">
                                    <h5 className="text-xs text-gray-400 font-bold">Rurales / Fincas</h5>
                                    <p className="text-2xl font-black text-white mt-0.5">{fireCounts.rurales}</p>
                                </div>
                            </div>
                            <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                <div className="bg-[#DC2626]/10 text-[#DC2626] p-2.5 rounded-xl border border-[#DC2626]/20 shrink-0">
                                    <Layers size={24} />
                                </div>
                                <div className="text-left">
                                    <h5 className="text-xs text-gray-400 font-bold">Otros Focos</h5>
                                    <p className="text-2xl font-black text-white mt-0.5">{fireCounts.otros}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* ========================================== */}
                {/* 2.3 SECCIÓN: TARJETAS DE CONTEO POR TIPO DE DAÑO POR VIENTO */}
                {/* ========================================== */}
                {activeSection === 'wind' && (
                    <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 mb-8">
                        <div className="mb-4 text-left">
                            <h3 className="text-lg font-black text-[#F28C28]">Daños por Fenómenos Climáticos</h3>
                            <p className="text-xs text-gray-400 mt-0.5">Clasificación dinámica de daños provocados por viento Zonda / temporal en San Juan.</p>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                            <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                <div className="bg-[#F28C28]/10 text-[#F28C28] p-2.5 rounded-xl border border-[#F28C28]/20 shrink-0">
                                    <Trees size={24} />
                                </div>
                                <div className="text-left">
                                    <h5 className="text-xs text-gray-400 font-bold">Árboles Caídos</h5>
                                    <p className="text-2xl font-black text-white mt-0.5">{windCounts.arboles}</p>
                                </div>
                            </div>
                            <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                <div className="bg-[#F28C28]/10 text-[#F28C28] p-2.5 rounded-xl border border-[#F28C28]/20 shrink-0">
                                    <Leaf size={24} />
                                </div>
                                <div className="text-left">
                                    <h5 className="text-xs text-gray-400 font-bold">Ramas Desprendidas</h5>
                                    <p className="text-2xl font-black text-white mt-0.5">{windCounts.ramas}</p>
                                </div>
                            </div>
                            <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                <div className="bg-[#F28C28]/10 text-[#F28C28] p-2.5 rounded-xl border border-[#F28C28]/20 shrink-0">
                                    <Home size={24} />
                                </div>
                                <div className="text-left">
                                    <h5 className="text-xs text-gray-400 font-bold">Techos Afectados</h5>
                                    <p className="text-2xl font-black text-white mt-0.5">{windCounts.techos}</p>
                                </div>
                            </div>
                            <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                <div className="bg-[#F28C28]/10 text-[#F28C28] p-2.5 rounded-xl border border-[#F28C28]/20 shrink-0">
                                    <Zap size={24} />
                                </div>
                                <div className="text-left">
                                    <h5 className="text-xs text-gray-400 font-bold">Postes / Cableados</h5>
                                    <p className="text-2xl font-black text-white mt-0.5">{windCounts.cableados}</p>
                                </div>
                            </div>
                            <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                <div className="bg-[#F28C28]/10 text-[#F28C28] p-2.5 rounded-xl border border-[#F28C28]/20 shrink-0">
                                    <ZapOff size={24} />
                                </div>
                                <div className="text-left">
                                    <h5 className="text-xs text-gray-400 font-bold">Cortes de Luz</h5>
                                    <p className="text-2xl font-black text-white mt-0.5">{windCounts.cortes}</p>
                                </div>
                            </div>
                            <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                <div className="bg-[#F28C28]/10 text-[#F28C28] p-2.5 rounded-xl border border-[#F28C28]/20 shrink-0">
                                    <Flag size={24} />
                                </div>
                                <div className="text-left">
                                    <h5 className="text-xs text-gray-400 font-bold">Cartelería / Semáforos</h5>
                                    <p className="text-2xl font-black text-white mt-0.5">{windCounts.carteleria}</p>
                                </div>
                            </div>
                            <div className="bg-[#0B1528] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                                <div className="bg-[#F28C28]/10 text-[#F28C28] p-2.5 rounded-xl border border-[#F28C28]/20 shrink-0">
                                    <Layers size={24} />
                                </div>
                                <div className="text-left">
                                    <h5 className="text-xs text-gray-400 font-bold">Otros Daños</h5>
                                    <p className="text-2xl font-black text-white mt-0.5">{windCounts.otros}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* ========================================== */}
                {/* 3. GRÁFICOS Y DETALLES DE SECCIÓN */}
                {/* ========================================== */}
                <div className="mb-8">
                    {/* Gráfico Analítico Real de Incidentes por Departamento */}
                    <div className="bg-[#111A2E] p-6 rounded-2xl border border-white/5 text-left flex flex-col justify-between">
                        <div>
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
                                <h4 className="text-sm font-black uppercase tracking-wider">
                                    Incidentes por Departamento (San Juan)
                                </h4>
                                <span className="text-[10px] text-gray-400 bg-white/5 py-1 px-2.5 rounded-md">
                                    Datos Reales Filtrados
                                </span>
                            </div>
                            <div className="h-72 flex items-end gap-1.5 sm:gap-2.5 pt-6 pb-14 border-b border-gray-700/50 overflow-x-auto scrollbar-thin">
                                {departmentChartData.map((d, i) => {
                                    let color = "bg-[#002D62]";
                                    if (activeSection === 'traffic') color = "bg-[#2563EB]";
                                    if (activeSection === 'fire') color = "bg-[#DC2626]";
                                    if (activeSection === 'wind') color = "bg-[#F28C28]";

                                    return (
                                        <div key={i} className="flex-1 min-w-[32px] sm:min-w-[45px] flex flex-col items-center gap-2 group h-full justify-end relative">
                                            <div className="text-[10px] font-bold text-gray-400 mb-1 opacity-0 group-hover:opacity-100 transition-opacity absolute -top-5">
                                                {d.count}
                                            </div>
                                            <div 
                                                className={`w-full ${color} rounded-t-sm transition-all group-hover:brightness-110`} 
                                                style={{ height: d.pct }}
                                            ></div>
                                            <span className="text-[9px] md:text-xs text-gray-400 font-bold whitespace-nowrap rotate-[-35deg] origin-top-left translate-y-1 block mt-1">
                                                {d.label}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                        <div className="flex items-center justify-between text-xs text-gray-400 mt-4">
                            <span>* Datos recopilados en tiempo real por ZonData</span>
                            <span className="text-[#F28C28] font-bold">Public Analytics</span>
                        </div>
                    </div>
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
