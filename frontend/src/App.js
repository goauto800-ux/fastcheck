import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import HomePage from "./pages/HomePage";

function App() {
  return (
    <div className="App min-h-screen bg-[#05050A]">
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
            background: '#0C0C16',
            border: '1px solid rgba(255,255,255,0.1)',
            color: '#FFFFFF',
            fontFamily: 'Manrope, sans-serif',
            boxShadow: '0 0 20px rgba(139,92,246,0.1)',
          },
        }}
      />
    </div>
  );
}

export default App;
