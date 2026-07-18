import React from 'react';
import { createRoot } from 'react-dom/client';
import MapComponent from './components/MapComponent';
import PremiumDashboardView from './components/PremiumDashboardView';

const App = () => {
    const rawPath = window.location.pathname;
    const decodedPath = decodeURIComponent(rawPath);

    if (decodedPath === '/data') {
        return <PremiumDashboardView />;
    }

    return <MapComponent />;
};

if (document.getElementById('map-root')) {
    const root = createRoot(document.getElementById('map-root'));
    root.render(<App />);
}
