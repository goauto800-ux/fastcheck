import { useState, useCallback, useRef } from "react";
import { UploadCloud, FileText, X } from "lucide-react";
import { Button } from "./ui/button";

export default function UploadZone({ onFileUpload, disabled }) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = useCallback((e) => { e.preventDefault(); if (!disabled) setIsDragging(true); }, [disabled]);
  const handleDragLeave = useCallback((e) => { e.preventDefault(); setIsDragging(false); }, []);
  const handleDrop = useCallback((e) => { e.preventDefault(); setIsDragging(false); if (disabled) return; const f = e.dataTransfer.files[0]; if (f) setSelectedFile(f); }, [disabled]);
  const handleFileSelect = useCallback((e) => { const f = e.target.files?.[0]; if (f) setSelectedFile(f); }, []);
  const handleUpload = useCallback(() => { if (selectedFile && onFileUpload) onFileUpload(selectedFile); }, [selectedFile, onFileUpload]);
  const handleClear = useCallback(() => { setSelectedFile(null); if (fileInputRef.current) fileInputRef.current.value = ""; }, []);

  return (
    <div className="h-full">
      <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2 font-heading">
        <UploadCloud className="w-4 h-4 text-[#00F0FF]" /> Upload Fichier
      </h3>
      <div
        className={`relative border border-dashed rounded-xl p-8 sm:p-10 flex flex-col items-center justify-center min-h-[260px] transition-all duration-300 cursor-pointer
          ${isDragging ? 'border-[#00F0FF]/50 bg-[#00F0FF]/[0.04] shadow-[0_0_30px_rgba(0,240,255,0.1)]' : 'border-white/10 bg-white/[0.02] hover:bg-white/[0.04] hover:border-purple-500/30'}
          ${disabled ? 'opacity-40 cursor-not-allowed' : ''}`}
        onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}
        onClick={() => !disabled && !selectedFile && fileInputRef.current?.click()} data-testid="upload-dropzone">
        <input ref={fileInputRef} type="file" accept=".csv,.txt,.text" onChange={handleFileSelect} className="hidden" disabled={disabled} data-testid="file-input" />
        {selectedFile ? (
          <div className="text-center">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-[#00F0FF]/20 to-[#8B5CF6]/20 flex items-center justify-center mx-auto mb-3 border border-white/10">
              <FileText className="w-7 h-7 text-[#00F0FF]" />
            </div>
            <p className="text-white font-medium mb-0.5 text-sm truncate max-w-[200px] font-mono">{selectedFile.name}</p>
            <p className="text-gray-500 text-xs font-mono mb-4">{(selectedFile.size / 1024).toFixed(1)} KB</p>
            <div className="flex gap-2 justify-center">
              <Button variant="outline" size="sm" onClick={(e) => { e.stopPropagation(); handleClear(); }} disabled={disabled}
                className="border-white/10 text-gray-400 hover:text-white bg-transparent text-xs h-8" data-testid="clear-file-btn">
                <X className="w-3.5 h-3.5 mr-1" /> Annuler
              </Button>
              <Button size="sm" onClick={(e) => { e.stopPropagation(); handleUpload(); }} disabled={disabled}
                className="btn-click-effect bg-gradient-to-r from-[#00F0FF] to-[#8B5CF6] text-white font-bold text-xs h-8 hover:opacity-90" data-testid="upload-submit-btn">
                <UploadCloud className="w-3.5 h-3.5 mr-1" /> Vérifier
              </Button>
            </div>
          </div>
        ) : (
          <>
            <div className="w-14 h-14 rounded-xl bg-white/[0.03] border border-white/10 flex items-center justify-center mb-3">
              <UploadCloud className="w-7 h-7 text-gray-600" />
            </div>
            <p className="text-gray-300 text-sm font-medium mb-1 text-center">Glissez votre fichier ici</p>
            <p className="text-gray-500 text-xs text-center mb-3">ou cliquez pour parcourir</p>
            <div className="flex gap-2">
              <span className="px-2.5 py-0.5 rounded-md bg-white/5 text-[10px] font-mono text-gray-500 border border-white/5">.csv</span>
              <span className="px-2.5 py-0.5 rounded-md bg-white/5 text-[10px] font-mono text-gray-500 border border-white/5">.txt</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
