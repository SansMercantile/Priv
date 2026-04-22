import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Read device param from querystring so iframes can request a specific layout
const params = new URLSearchParams(window.location.search);
const device = params.get('device') || 'desktop';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App initialDevice={device} />
  </React.StrictMode>
);
