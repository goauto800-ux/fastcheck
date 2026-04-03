import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Terminal, Zap, Clipboard } from "lucide-react";
import { Button } from "./ui/button";
import { toast } from "sonner";

export default function TextPasteZone({ onVerify, disabled }) {
  const [text, setText] = useState("");

  const parseIdentifiers = useCallback((input) => {
    if (!input.trim()) return [];

    // Split by newlines, commas, semicolons, spaces, tabs
    const items = input
      .split(/[\n,;\t\s]+/)
      .map((item) => item.trim())
      .filter((item) => {
        // Check if it looks like an email or phone
        if (item.includes("@")) return true;
        const digits = (item.match(/\d/g) || []).length;
        return digits >= 8;
      });

    // Remove duplicates
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
      toast.success("Contenu collé depuis le presse-papiers");
    } catch (err) {
      toast.error("Impossible d'accéder au presse-papiers");
    }
  }, []);

  const handleClear = useCallback(() => {
    setText("");
  }, []);

  const identifierCount = parseIdentifiers(text).length;

  return (
    <div className="h-full">
      <h3 className="text-lg font-semibold text-white mb-4 font-heading flex items-center gap-2">
        <Terminal className="w-5 h-5 text-purple-400" />
        Coller du Texte
      </h3>

      <div className="relative">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Collez vos emails ou numéros ici...&#10;&#10;Exemple:&#10;email@example.com&#10;+33612345678&#10;user@domain.fr"
          disabled={disabled}
          className={`
            w-full h-[280px] rounded-2xl p-6 font-mono text-sm resize-none
            bg-[#0A0710] border border-white/10 text-blue-300
            placeholder:text-slate-600
            focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20
            transition-all duration-300
            ${disabled ? "opacity-50 cursor-not-allowed" : ""}
          `}
          data-testid="text-input"
        />

        {/* Character count */}
        <div className="absolute bottom-4 left-6 text-xs font-mono text-slate-600">
          {identifierCount > 0 && (
            <span className="text-blue-400">{identifierCount} identifiant(s) détecté(s)</span>
          )}
        </div>

        {/* Paste button */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handlePaste}
          disabled={disabled}
          className="absolute top-4 right-4 p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-all"
          title="Coller depuis le presse-papiers"
          data-testid="paste-btn"
        >
          <Clipboard className="w-4 h-4" />
        </motion.button>
      </div>

      {/* Actions */}
      <div className="flex gap-3 mt-4 justify-end">
        {text && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleClear}
            disabled={disabled}
            className="border-white/10 text-slate-400 hover:text-white bg-transparent"
            data-testid="clear-text-btn"
          >
            Effacer
          </Button>
        )}
        <Button
          size="sm"
          onClick={handleVerify}
          disabled={disabled || !text.trim()}
          className="bg-gradient-to-r from-blue-600 to-purple-600 btn-glow px-6"
          data-testid="verify-submit-btn"
        >
          <Zap className="w-4 h-4 mr-2" />
          Vérifier
        </Button>
      </div>
    </div>
  );
}
