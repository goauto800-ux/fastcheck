import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import HomePage from "./pages/HomePage";

function App() {
  return (
    <div className="App min-h-screen bg-[#080810]">
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
            background: '#111120',
            border: '1px solid rgba(255,255,255,0.08)',
            color: '#e8e8f0',
            fontFamily: 'Inter, sans-serif',
          },
        }}
      />
    </div>
  );
}

export default App;
