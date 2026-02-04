import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';
import './index.css';

// Create the root element and render the application.  The BrowserRouter
// provides client‑side routing functionality so that the SPA can use
// standard URL paths without reloading the page.  Tailwind styles are
// imported globally via index.css.
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);