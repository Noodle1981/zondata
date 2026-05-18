import React from 'react';
import { createRoot } from 'react-dom/client';
import MapComponent from './components/MapComponent';
import PublicDashboardView from './components/PublicDashboardView';
import PremiumDashboardView from './components/PremiumDashboardView';

const App = () => {
    const rawPath = window.location.pathname;
    const decodedPath = decodeURIComponent(rawPath);

    // Support both accented and unaccented paths for maximum browser compatibility
    if (decodedPath === '/dashboard_public' || decodedPath === '/dashboard_públic') {
        return <PublicDashboardView />;
    }
    
    if (decodedPath === '/dashboard_premium') {
        return <PremiumDashboardView />;
    }

    return <MapComponent />;
};

if (document.getElementById('map-root')) {
    const root = createRoot(document.getElementById('map-root'));
    root.render(<App />);
}
