import { useState, useCallback, useRef } from "react";
import { UploadCloud, FileText, X } from "lucide-react";
import { Button } from "./ui/button";

export default function UploadZone({ onFileUpload, disabled }) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  }, [disabled]);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    const file = e.dataTransfer.files[0];
    if (file) setSelectedFile(file);
  }, [disabled]);

  const handleFileSelect = useCallback((e) => {
    const file = e.target.files?.[0];
    if (file) setSelectedFile(file);
  }, []);

  const handleUpload = useCallback(() => {
    if (selectedFile && onFileUpload) onFileUpload(selectedFile);
  }, [selectedFile, onFileUpload]);

  const handleClearFile = useCallback(() => {
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, []);

  return (
    <div className="h-full">
      <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
        <UploadCloud className="w-4 h-4 text-[#00d4ff]" />
        Upload Fichier
      </h3>

      <div
        className={`
          relative border border-dashed rounded-xl p-8 sm:p-10
          flex flex-col items-center justify-center min-h-[260px]
          transition-all duration-200 cursor-pointer
          ${isDragging
            ? "border-[#00d4ff] bg-[#00d4ff]/[0.06]"
            : "border-white/[0.1] bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/[0.15]"
          }
          ${disabled ? "opacity-40 cursor-not-allowed" : ""}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && !selectedFile && fileInputRef.current?.click()}
        data-testid="upload-dropzone"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.txt,.text"
          onChange={handleFileSelect}
          className="hidden"
          disabled={disabled}
          data-testid="file-input"
        />

        {selectedFile ? (
          <div className="text-center">
            <div className="w-12 h-12 rounded-xl bg-[#00d4ff]/[0.08] flex items-center justify-center mx-auto mb-3 border border-[#00d4ff]/20">
              <FileText className="w-6 h-6 text-[#00d4ff]" />
            </div>
            <p className="text-white font-medium mb-0.5 text-sm truncate max-w-[200px] font-mono">
              {selectedFile.name}
            </p>
            <p className="text-[#55556a] text-xs font-mono mb-4">
              {(selectedFile.size / 1024).toFixed(1)} KB
            </p>
            <div className="flex gap-2 justify-center">
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => { e.stopPropagation(); handleClearFile(); }}
                disabled={disabled}
                className="border-white/[0.08] text-[#8888a0] hover:text-white bg-transparent text-xs h-8"
                data-testid="clear-file-btn"
              >
                <X className="w-3.5 h-3.5 mr-1" />
                Annuler
              </Button>
              <Button
                size="sm"
                onClick={(e) => { e.stopPropagation(); handleUpload(); }}
                disabled={disabled}
                className="bg-[#00d4ff] text-black hover:bg-[#00d4ff]/90 text-xs h-8 font-semibold"
                data-testid="upload-submit-btn"
              >
                <UploadCloud className="w-3.5 h-3.5 mr-1" />
                Vérifier
              </Button>
            </div>
          </div>
        ) : (
          <>
            <div className="w-12 h-12 rounded-xl bg-white/[0.03] flex items-center justify-center mb-3 border border-white/[0.06]">
              <UploadCloud className="w-6 h-6 text-[#55556a]" />
            </div>
            <p className="text-[#8888a0] text-sm font-medium mb-1 text-center">
              Glissez votre fichier ici
            </p>
            <p className="text-[#55556a] text-xs text-center mb-3">
              ou cliquez pour parcourir
            </p>
            <div className="flex gap-2 justify-center">
              <span className="px-2 py-0.5 rounded bg-white/[0.04] text-[10px] font-mono text-[#55556a]">.csv</span>
              <span className="px-2 py-0.5 rounded bg-white/[0.04] text-[10px] font-mono text-[#55556a]">.txt</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
