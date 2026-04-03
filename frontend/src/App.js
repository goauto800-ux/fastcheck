import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import HomePage from "./pages/HomePage";

function App() {
  return (
    <div className="App min-h-screen bg-[#05030A]">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
        </Routes>
      </BrowserRouter>
      <Toaster 
        position="bottom-right" 
        theme="dark"
        toastOptions={{
          style: {
            background: '#0F0B1A',
            border: '1px solid rgba(139, 92, 246, 0.3)',
            color: '#F8FAFC',
          },
        }}
      />
    </div>
  );
}

export default App;
