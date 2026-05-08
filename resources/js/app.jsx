import React from 'react';
import { createRoot } from 'react-dom/client';
import MapComponent from './components/MapComponent';

if (document.getElementById('map-root')) {
    const root = createRoot(document.getElementById('map-root'));
    root.render(<MapComponent />);
}
