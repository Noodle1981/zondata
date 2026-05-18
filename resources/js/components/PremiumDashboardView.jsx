import React from 'react';
import { 
    Lock, 
    ArrowLeft, 
    Check, 
    TrendingUp, 
    Database, 
    Download,
    Filter,
    LineChart,
    Sparkles,
    Shield
} from 'lucide-react';

const PremiumDashboardView = () => {
    return (
        <div className="bg-[#0B1528] min-h-screen text-white font-sans antialiased relative overflow-hidden pb-12">
            
            {/* ========================================== */}
            {/* FONDO BLUR/SKELETON (Dashboard Premium Guardado) */}
            {/* ========================================== */}
            <div className="filter blur-md opacity-25 select-none pointer-events-none w-full max-w-7xl mx-auto px-6 pt-8 space-y-8">
                {/* Header Mockup */}
                <div className="flex items-center justify-between pb-6 border-b border-white/10">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl font-black text-[#F28C28]">ZonData Premium PRO</span>
                        <span className="bg-emerald-500/20 text-emerald-400 text-xs px-3 py-1 rounded-md font-bold">Activo</span>
                    </div>
                    <div className="h-10 w-48 bg-white/10 rounded-xl"></div>
                </div>

                {/* Filters Row Mockup */}
                <div className="bg-[#111A2E] p-4 rounded-2xl flex gap-4">
                    <div className="h-10 w-40 bg-white/5 rounded-lg flex items-center gap-2 px-3"><Filter size={14} /> Filtro Departamento</div>
                    <div className="h-10 w-40 bg-white/5 rounded-lg flex items-center gap-2 px-3"><Filter size={14} /> Filtro Severidad</div>
                    <div className="h-10 w-40 bg-white/5 rounded-lg flex items-center gap-2 px-3"><Filter size={14} /> Rango de Años</div>
                    <div className="ml-auto h-10 w-36 bg-[#F28C28] rounded-lg flex items-center justify-center gap-2"><Download size={14} /> Exportar Excel</div>
                </div>

                {/* Grid stats Mockup */}
                <div className="grid grid-cols-4 gap-6">
                    {[1, 2, 3, 4].map(i => (
                        <div key={i} className="bg-[#111A2E] p-6 rounded-2xl space-y-3">
                            <span className="text-xs text-gray-400 font-bold">Estadística Avanzada</span>
                            <div className="h-8 w-20 bg-white/10 rounded-md"></div>
                            <div className="h-4 w-32 bg-white/5 rounded-md"></div>
                        </div>
                    ))}
                </div>

                {/* Grid graphs Mockup */}
                <div className="grid grid-cols-3 gap-6">
                    <div className="bg-[#111A2E] p-6 rounded-2xl h-80 col-span-2 flex flex-col justify-between">
                        <span className="font-bold flex items-center gap-2"><LineChart size={16} /> Tendencia de 10 Años</span>
                        <div className="h-52 w-full bg-white/5 rounded-xl"></div>
                    </div>
                    <div className="bg-[#111A2E] p-6 rounded-2xl h-80 flex flex-col justify-between">
                        <span className="font-bold flex items-center gap-2"><Sparkles size={16} /> Predicción AI de Incidentes</span>
                        <div className="h-52 w-full bg-white/5 rounded-xl"></div>
                    </div>
                </div>
            </div>

            {/* ========================================== */}
            {/* PARED DE SUSCRIPCIÓN PREMIUM (Modal Overlay) */}
            {/* ========================================== */}
            <div className="absolute inset-0 bg-[#0B1528]/80 backdrop-blur-sm flex items-center justify-center p-6 z-50 overflow-y-auto">
                <div className="bg-[#0F1C34] border border-white/10 rounded-3xl p-8 max-w-5xl w-full shadow-2xl shadow-black/60 relative animate-fadeIn my-12">
                    
                    {/* Botón Volver */}
                    <button 
                        onClick={() => window.location.href = '/'}
                        className="absolute top-6 left-6 text-gray-400 hover:text-white flex items-center gap-2 text-xs font-bold transition-all cursor-pointer"
                    >
                        <ArrowLeft size={14} />
                        Volver al Mapa
                    </button>

                    {/* Logo & Lock Header */}
                    <div className="text-center mt-6">
                        <div className="mx-auto w-16 h-16 bg-[#F28C28]/10 rounded-2xl flex items-center justify-center border border-[#F28C28]/20 shadow-lg shadow-[#F28C28]/10 animate-bounce">
                            <Lock size={28} className="text-[#F28C28]" />
                        </div>
                        
                        <h2 className="text-2xl font-black mt-4 flex items-center justify-center gap-2 text-white">
                            Acceso Premium Requerido
                        </h2>
                        
                        <p className="text-sm text-gray-400 mt-2 max-w-xl mx-auto">
                            Desbloquea el dataset histórico completo (2016-2026), descarga ilimitada de reportes y predicciones de riesgo inteligentes.
                        </p>
                    </div>

                    {/* Tabla de Planes de Precios */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-10">
                        {/* Plan Mensual */}
                        <div className="bg-[#111A2E]/60 border border-white/5 hover:border-white/10 transition-all rounded-2xl p-6 flex flex-col justify-between text-left">
                            <div>
                                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Suscripción Mensual</span>
                                <h4 className="text-lg font-black text-white mt-1">Plan Mensual</h4>
                                <div className="mt-4 flex items-baseline gap-1">
                                    <span className="text-3xl font-black text-white">$1.900</span>
                                    <span className="text-xs text-gray-400">/ mes</span>
                                </div>
                                <ul className="mt-6 space-y-3 text-xs text-gray-300">
                                    <li className="flex items-center gap-2">
                                        <Check size={14} className="text-emerald-500 shrink-0" />
                                        Consulta histórica de 90 días
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <Check size={14} className="text-emerald-500 shrink-0" />
                                        Filtros de departamentos
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <Check size={14} className="text-emerald-500 shrink-0" />
                                        1 alerta SMS configurada
                                    </li>
                                </ul>
                            </div>
                            <button className="w-full mt-8 bg-white/5 hover:bg-white/10 text-white font-bold py-2.5 rounded-xl text-xs transition-colors border border-white/10 cursor-pointer">
                                Adquirir Básico
                            </button>
                        </div>

                        {/* Plan Anual PRO */}
                        <div className="bg-[#111A2E] border-2 border-[#F28C28] rounded-2xl p-6 flex flex-col justify-between relative transform hover:scale-[1.02] transition-all text-left shadow-xl shadow-[#F28C28]/10">
                            <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#F28C28] text-white text-[9px] font-black uppercase tracking-wider py-1 px-3 rounded-full shadow-md">
                                RECOMENDADO
                            </span>
                            <div>
                                <span className="text-[10px] font-bold text-[#F28C28] uppercase tracking-widest">Mejor Valor</span>
                                <h4 className="text-lg font-black text-white mt-1">Plan Anual PRO</h4>
                                <div className="mt-4 flex items-baseline gap-1">
                                    <span className="text-3xl font-black text-white">$14.900</span>
                                    <span className="text-xs text-gray-400">/ año</span>
                                </div>
                                <ul className="mt-6 space-y-3 text-xs text-gray-300">
                                    <li className="flex items-center gap-2">
                                        <Check size={14} className="text-[#F28C28] shrink-0" />
                                        Acceso histórico <b>ilimitado</b>
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <Check size={14} className="text-[#F28C28] shrink-0" />
                                        Exportación Excel/CSV e informes
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <Check size={14} className="text-[#F28C28] shrink-0" />
                                        Alertas SMS y WhatsApp ilimitadas
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <Check size={14} className="text-[#F28C28] shrink-0" />
                                        Acceso a herramientas AI
                                    </li>
                                </ul>
                            </div>
                            <button className="w-full mt-8 bg-[#F28C28] text-white font-bold py-2.5 rounded-xl text-xs transition-transform hover:brightness-110 shadow-lg shadow-[#F28C28]/20 cursor-pointer">
                                Adquirir Anual PRO
                            </button>
                        </div>

                        {/* Plan Institucional */}
                        <div className="bg-[#111A2E]/60 border border-white/5 hover:border-white/10 transition-all rounded-2xl p-6 flex flex-col justify-between text-left">
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
                            <button className="w-full mt-8 bg-white/5 hover:bg-white/10 text-white font-bold py-2.5 rounded-xl text-xs transition-colors border border-white/10 cursor-pointer">
                                Contactar Soporte
                            </button>
                        </div>
                    </div>

                    {/* Footer del Modal */}
                    <div className="mt-8 pt-6 border-t border-white/5 flex items-center justify-center gap-2 text-xs text-gray-400">
                        <Shield size={14} className="text-emerald-500" />
                        <span>Transacciones seguras encriptadas en cumplimiento con normativas bancarias.</span>
                    </div>

                </div>
            </div>

        </div>
    );
};

export default PremiumDashboardView;
