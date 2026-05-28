import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { App } from "./App";
import { AppErrorBoundary, initFrontendSentry } from "./observability/sentry";

const root = ReactDOM.createRoot(document.getElementById("root") as HTMLElement);
initFrontendSentry();

root.render(
  <React.StrictMode>
    <AppErrorBoundary>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </AppErrorBoundary>
  </React.StrictMode>
);
