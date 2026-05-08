import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./routes/AppShell";

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate replace to="/workspace" />} />
        <Route path="/workspace" element={<div>Workspace shell</div>} />
      </Route>
    </Routes>
  );
}
