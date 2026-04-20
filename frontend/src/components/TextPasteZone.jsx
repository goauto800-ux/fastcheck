import { useState, useCallback } from "react";
import { Terminal, Zap, Clipboard } from "lucide-react";
import { Button } from "./ui/button";
import { toast } from "sonner";

export default function TextPasteZone({ onVerify, disabled }) {
  const [text, setText] = useState("");
  
  const parseEmails = useCallback((input) => {
    if (!input.trim()) return [];
    const emailRegex = /[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/g;
    const matches = input.match(emailRegex) || [];
    return [...new Set(matches.map(e => e.toLowerCase()))];
  }, []);

  const handleVerify = useCallback(() => {
    const emails = parseEmails(text);
    if (emails.length === 0) { toast.error("Aucun email valide détecté"); return; }
    onVerify(emails);
  }, [text, parseEmails, onVerify]);

  const handlePaste = useCallback(async () => {
    try { const c = await navigator.clipboard.readText(); setText(p => p ? p + "\n" + c : c); toast.success("Collé"); }
    catch { toast.error("Presse-papiers inaccessible"); }
  }, []);

  const count = parseEmails(text).length;

  return (
    <div className="h-full">
      <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2 font-heading">
        <Terminal className="w-4 h-4 text-[#06C167]" /> Coller des Emails
      </h3>
      <div className="relative">
        <textarea value={text} onChange={(e) => setText(e.target.value)}
          placeholder={"Collez vos emails ici...\n\nExemple:\nuser@example.com\ntest@gmail.com\ncombo@mail.fr:password123"}
          disabled={disabled}
          className={`w-full h-[260px] rounded-xl p-4 font-mono text-sm resize-none bg-[#0C0C16] border border-white/10 text-[#06C167]/70 placeholder:text-gray-700 focus:outline-none focus:border-[#06C167]/40 focus:ring-1 focus:ring-[#06C167]/20 transition-all duration-300 ${disabled ? 'opacity-40 cursor-not-allowed' : ''}`}
          data-testid="text-input" />
        <div className="absolute bottom-3 left-4 text-[11px] text-gray-600">
          {count > 0 && <span className="text-[#06C167]/50">{count} email(s) détecté(s)</span>}
        </div>
        <button onClick={handlePaste} disabled={disabled}
          className="absolute top-3 right-3 p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-500 hover:text-white transition-all border border-white/5" title="Coller" data-testid="paste-btn">
          <Clipboard className="w-3.5 h-3.5" />
        </button>
      </div>
      <div className="flex gap-2 mt-3 justify-end">
        {text && <Button variant="outline" size="sm" onClick={() => setText("")} disabled={disabled}
          className="border-white/10 text-gray-400 hover:text-white bg-transparent text-xs h-8" data-testid="clear-text-btn">Effacer</Button>}
        <Button size="sm" onClick={handleVerify} disabled={disabled || !text.trim()}
          className="btn-click-effect bg-[#06C167] text-white font-bold text-xs h-8 px-5 hover:bg-[#06C167]/80" data-testid="verify-submit-btn">
          <Zap className="w-3.5 h-3.5 mr-1.5" /> Vérifier Uber Eats
        </Button>
      </div>
    </div>
  );
}
