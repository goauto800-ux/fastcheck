import { useState, useCallback } from "react";
import { Terminal, Zap, Clipboard } from "lucide-react";
import { Button } from "./ui/button";
import { toast } from "sonner";

export default function TextPasteZone({ onVerify, disabled }) {
  const [text, setText] = useState("");
  const parseIdentifiers = useCallback((input) => {
    if (!input.trim()) return [];
    const items = input.split(/[\n,;\t\s]+/).map(s => s.trim()).filter(s => s.includes("@") || (s.match(/\d/g) || []).length >= 8);
    return [...new Set(items)];
  }, []);

  const handleVerify = useCallback(() => {
    const ids = parseIdentifiers(text);
    if (ids.length === 0) { toast.error("Aucun email ou numéro valide détecté"); return; }
    onVerify(ids);
  }, [text, parseIdentifiers, onVerify]);

  const handlePaste = useCallback(async () => {
    try { const c = await navigator.clipboard.readText(); setText(p => p ? p + "\n" + c : c); toast.success("Collé"); }
    catch { toast.error("Presse-papiers inaccessible"); }
  }, []);

  const count = parseIdentifiers(text).length;

  return (
    <div className="h-full">
      <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2 font-heading">
        <Terminal className="w-4 h-4 text-[#FF00FF]" /> Coller du Texte
      </h3>
      <div className="relative">
        <textarea value={text} onChange={(e) => setText(e.target.value)}
          placeholder={"Collez vos emails ou numéros ici...\n\nExemple:\nemail@example.com\n+33612345678\nuser@domain.fr"}
          disabled={disabled}
          className={`w-full h-[260px] rounded-xl p-4 font-mono text-sm resize-none bg-[#0C0C16] border border-white/10 text-[#00F0FF]/70 placeholder:text-gray-700 focus:outline-none focus:border-[#00F0FF]/40 focus:ring-1 focus:ring-[#00F0FF]/20 focus:shadow-[0_0_20px_rgba(0,240,255,0.08)] transition-all duration-300 ${disabled ? 'opacity-40 cursor-not-allowed' : ''}`}
          data-testid="text-input" />
        <div className="absolute bottom-3 left-4 text-[11px] text-gray-600">
          {count > 0 && <span className="text-[#00F0FF]/50">{count} détecté(s)</span>}
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
          className="btn-click-effect bg-gradient-to-r from-[#00F0FF] to-[#8B5CF6] text-white font-bold text-xs h-8 px-5 hover:opacity-90 hover:shadow-[0_0_20px_rgba(0,240,255,0.4)]" data-testid="verify-submit-btn">
          <Zap className="w-3.5 h-3.5 mr-1.5" /> Vérifier
        </Button>
      </div>
    </div>
  );
}
