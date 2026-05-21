import React, { useState, useEffect } from 'react';
import { Calendar, AlertTriangle, X, ArrowRight } from 'lucide-react';

const IncidentsSummaryModal = ({ onFocusIncident }) => {
    const [summary, setSummary] = useState(null);
    const [notifications, setNotifications] = useState([]);
    const [isOpen, setIsOpen] = useState(true);
    const [toastVisible, setToastVisible] = useState(false);

    useEffect(() => {
        const fetchSummary = async () => {
            try {
                const res = await fetch('/api/incidents/summary');
                const data = await res.json();
                setSummary(data);
            } catch (error) {
                console.error("Error fetching summary:", error);
            }
        };

        const fetchNotifications = async () => {
            try {
                const res = await fetch('/api/incidents/notifications');
                const data = await res.json();
                setNotifications(data);
                if (data.length > 0) {
                    setToastVisible(true);
                }
            } catch (error) {
                console.error("Error fetching notifications:", error);
            }
        };

        fetchSummary();
        fetchNotifications();
        
        // Refresh every 5 minutes
        const interval = setInterval(() => {
            fetchSummary();
            fetchNotifications();
        }, 300000);

        return () => clearInterval(interval);
    }, []);

    if (!isOpen) return null;

    return (
        <div className="fixed bottom-6 right-6 z-[1000] flex flex-col gap-3 pointer-events-auto select-none">
            {/* Modal Toast de Alerta */}
            {toastVisible && notifications.length > 0 && (
                <div className="bg-gradient-to-br from-[#EAB308]/90 to-[#B45309]/90 backdrop-blur-md p-4 rounded-xl shadow-2xl border border-amber-400/50 text-white w-80 animate-slide-up relative">
                    <button 
                        onClick={() => setToastVisible(false)}
                        className="absolute top-2 right-2 p-1 hover:bg-black/10 rounded-full transition-colors"
                    >
                        <X size={14} />
                    </button>
                    
                    <div className="flex items-start gap-3">
                        <div className="bg-white/20 p-2 rounded-lg mt-0.5">
                            <AlertTriangle size={18} className="text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                            <h4 className="font-black text-sm uppercase tracking-wider mb-1">Fallecimientos Pasados</h4>
                            <p className="text-xs font-medium text-white/90 leading-tight">
                                {notifications.length} fallecimiento(s) de incidentes pasados reportados hoy.
                            </p>
                        </div>
                    </div>
                    
                    <div className="mt-3 space-y-2 max-h-32 overflow-y-auto custom-scrollbar">
                        {notifications.map(notif => (
                            <div key={notif.id} className="bg-black/20 p-2.5 rounded-lg border border-white/10 hover:bg-black/30 transition-colors cursor-pointer" onClick={() => onFocusIncident && onFocusIncident(notif)}>
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-[9px] uppercase font-bold text-amber-200">Noticia Actualizada</span>
                                    <span className="text-[9px] opacity-75">{new Date(notif.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                                </div>
                                <h5 className="font-bold text-xs truncate" title={notif.title}>{notif.title}</h5>
                                <div className="flex items-center justify-between mt-1.5">
                                    <a href={notif.source_url} target="_blank" rel="noopener noreferrer" className="text-[10px] underline underline-offset-2 opacity-80 hover:opacity-100 transition-opacity">
                                        {notif.source_name}
                                    </a>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default IncidentsSummaryModal;
