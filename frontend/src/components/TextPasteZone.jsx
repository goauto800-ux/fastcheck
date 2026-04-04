import { useState, useCallback } from "react";
import { Terminal, Zap, Clipboard } from "lucide-react";
import { Button } from "./ui/button";
import { toast } from "sonner";

export default function TextPasteZone({ onVerify, disabled }) {
  const [text, setText] = useState("");

  const parseIdentifiers = useCallback((input) => {
    if (!input.trim()) return [];
    const items = input.split(/[\n,;\t\s]+/).map((item) => item.trim()).filter((item) => {
      if (item.includes("@")) return true;
      return (item.match(/\d/g) || []).length >= 8;
    });
    return [...new Set(items)];
  }, []);

  const handleVerify = useCallback(() => {
    const identifiers = parseIdentifiers(text);
    if (identifiers.length === 0) { toast.error("Aucun email ou numéro valide détecté"); return; }
    onVerify(identifiers);
  }, [text, parseIdentifiers, onVerify]);

  const handlePaste = useCallback(async () => {
    try {
      const clipboardText = await navigator.clipboard.readText();
      setText((prev) => (prev ? prev + "\n" + clipboardText : clipboardText));
      toast.success("Contenu collé");
    } catch (err) { toast.error("Impossible d'accéder au presse-papiers"); }
  }, []);

  const identifierCount = parseIdentifiers(text).length;

  return (
    <div className="h-full">
      <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
        <Terminal className="w-4 h-4 text-[#a855f7]" style={{filter:'drop-shadow(0 0 4px rgba(168,85,247,0.4))'}} />
        Coller du Texte
      </h3>

      <div className="relative">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={"Collez vos emails ou numéros ici...\n\nExemple:\nemail@example.com\n+33612345678\nuser@domain.fr"}
          disabled={disabled}
          className={`
            w-full h-[260px] rounded-xl p-4 font-mono text-sm resize-none
            bg-[#0c0c1d] border border-white/[0.06] text-[#00e5ff]/70
            placeholder:text-[#2a2a40]
            focus:outline-none focus:border-[#00e5ff]/25
            transition-all duration-200
            ${disabled ? "opacity-40 cursor-not-allowed" : ""}
          `}
          style={{boxShadow:'inset 0 0 30px rgba(0,229,255,0.02)'}}
          data-testid="text-input"
        />

        <div className="absolute bottom-3 left-4 text-[11px] text-[#44445e]">
          {identifierCount > 0 && <span className="text-[#00e5ff]/50">{identifierCount} détecté(s)</span>}
        </div>

        <button onClick={handlePaste} disabled={disabled}
          className="absolute top-3 right-3 p-1.5 rounded-md bg-white/[0.03] hover:bg-white/[0.06] text-[#44445e] hover:text-white transition-all" title="Coller" data-testid="paste-btn">
          <Clipboard className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="flex gap-2 mt-3 justify-end">
        {text && (
          <Button variant="outline" size="sm" onClick={() => setText("")} disabled={disabled}
            className="border-white/[0.06] text-[#7a7a9a] hover:text-white bg-transparent text-xs h-8" data-testid="clear-text-btn">
            Effacer
          </Button>
        )}
        <Button size="sm" onClick={handleVerify} disabled={disabled || !text.trim()}
          className="bg-[#00e5ff] text-[#060612] hover:bg-[#00e5ff]/90 text-xs h-8 px-5 font-semibold btn-glow" data-testid="verify-submit-btn">
          <Zap className="w-3.5 h-3.5 mr-1.5" style={{filter:'drop-shadow(0 0 3px rgba(0,229,255,0.5))'}} /> Vérifier
        </Button>
      </div>
    </div>
  );
}
