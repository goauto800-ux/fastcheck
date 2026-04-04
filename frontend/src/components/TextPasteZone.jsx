import { useState, useCallback } from "react";
import { Terminal, Zap, Clipboard } from "lucide-react";
import { Button } from "./ui/button";
import { toast } from "sonner";

export default function TextPasteZone({ onVerify, disabled }) {
  const [text, setText] = useState("");

  const parseIdentifiers = useCallback((input) => {
    if (!input.trim()) return [];
    const items = input
      .split(/[\n,;\t\s]+/)
      .map((item) => item.trim())
      .filter((item) => {
        if (item.includes("@")) return true;
        const digits = (item.match(/\d/g) || []).length;
        return digits >= 8;
      });
    return [...new Set(items)];
  }, []);

  const handleVerify = useCallback(() => {
    const identifiers = parseIdentifiers(text);
    if (identifiers.length === 0) {
      toast.error("Aucun email ou numéro valide détecté");
      return;
    }
    onVerify(identifiers);
  }, [text, parseIdentifiers, onVerify]);

  const handlePaste = useCallback(async () => {
    try {
      const clipboardText = await navigator.clipboard.readText();
      setText((prev) => (prev ? prev + "\n" + clipboardText : clipboardText));
      toast.success("Contenu collé");
    } catch (err) {
      toast.error("Impossible d'accéder au presse-papiers");
    }
  }, []);

  const handleClear = useCallback(() => { setText(""); }, []);

  const identifierCount = parseIdentifiers(text).length;

  return (
    <div className="h-full">
      <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
        <Terminal className="w-4 h-4 text-[#a855f7]" />
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
            bg-[#0e0e1a] border border-white/[0.08] text-[#00d4ff]/80
            placeholder:text-[#33334a]
            focus:outline-none focus:border-[#00d4ff]/30 focus:ring-1 focus:ring-[#00d4ff]/10
            transition-all duration-200
            ${disabled ? "opacity-40 cursor-not-allowed" : ""}
          `}
          data-testid="text-input"
        />

        {/* Count */}
        <div className="absolute bottom-3 left-4 text-[11px] text-[#55556a]">
          {identifierCount > 0 && (
            <span className="text-[#00d4ff]/60">{identifierCount} détecté(s)</span>
          )}
        </div>

        {/* Paste button */}
        <button
          onClick={handlePaste}
          disabled={disabled}
          className="absolute top-3 right-3 p-1.5 rounded-md bg-white/[0.04] hover:bg-white/[0.08] text-[#55556a] hover:text-white transition-all"
          title="Coller"
          data-testid="paste-btn"
        >
          <Clipboard className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Actions */}
      <div className="flex gap-2 mt-3 justify-end">
        {text && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleClear}
            disabled={disabled}
            className="border-white/[0.08] text-[#8888a0] hover:text-white bg-transparent text-xs h-8"
            data-testid="clear-text-btn"
          >
            Effacer
          </Button>
        )}
        <Button
          size="sm"
          onClick={handleVerify}
          disabled={disabled || !text.trim()}
          className="bg-[#00d4ff] text-black hover:bg-[#00d4ff]/90 text-xs h-8 px-5 font-semibold btn-glow"
          data-testid="verify-submit-btn"
        >
          <Zap className="w-3.5 h-3.5 mr-1.5" />
          Vérifier
        </Button>
      </div>
    </div>
  );
}
