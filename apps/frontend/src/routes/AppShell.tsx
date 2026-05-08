import { Link, Outlet } from "react-router-dom";

export function AppShell() {
  return (
    <div>
      <header>
        <Link to="/workspace">TaskMaster</Link>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
