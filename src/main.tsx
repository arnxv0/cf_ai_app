import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import Overlay from "./Overlay";
import ResponseWindow from "./ResponseWindow";

// Check window type based on hash
const isOverlay = window.location.hash === "#overlay";
const isResponse = window.location.hash === "#response";

// Add class to body for window-specific styling
if (isOverlay) {
  document.body.classList.add("overlay-window");
} else if (isResponse) {
  document.body.classList.add("response-window");
}

// Render appropriate component based on window type
let Component = App;
if (isOverlay) {
  Component = Overlay;
} else if (isResponse) {
  Component = ResponseWindow;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Component />
  </React.StrictMode>
);
