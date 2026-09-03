import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Disputes from "./pages/Disputes";

export default function App() {
  return (
    <div className="flex min-h-screen bg-[#0a0e1a] text-slate-100 font-sans antialiased selection:bg-blue-600 selection:text-white">
      {/* Fixed Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <main className="flex-1 ml-64 min-h-screen p-8 md:p-10 overflow-y-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/disputes" element={<Disputes />} />
        </Routes>
      </main>
    </div>
  );
}
