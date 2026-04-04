import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import HomePage from "./pages/HomePage";

function App() {
  return (
    <div className="App min-h-screen bg-[#060612]">
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
            background: '#0f0f22',
            border: '1px solid rgba(0,229,255,0.12)',
            color: '#eeeef4',
            fontFamily: 'Inter, sans-serif',
            boxShadow: '0 0 20px rgba(0,229,255,0.06)',
          },
        }}
      />
    </div>
  );
}

export default App;
