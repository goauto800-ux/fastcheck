import { useState, useCallback, useRef } from "react";
import { motion } from "framer-motion";
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
    if (file) {
      setSelectedFile(file);
    }
  }, [disabled]);

  const handleFileSelect = useCallback((e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  }, []);

  const handleUpload = useCallback(() => {
    if (selectedFile && onFileUpload) {
      onFileUpload(selectedFile);
    }
  }, [selectedFile, onFileUpload]);

  const handleClearFile = useCallback(() => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);

  return (
    <div className="h-full">
      <h3 className="text-lg font-semibold text-white mb-4 font-heading flex items-center gap-2">
        <UploadCloud className="w-5 h-5 text-blue-400" />
        Upload Fichier
      </h3>

      <motion.div
        className={`
          relative border-2 border-dashed rounded-2xl p-8 sm:p-12
          flex flex-col items-center justify-center min-h-[280px]
          transition-all duration-300 cursor-pointer
          ${isDragging 
            ? "border-blue-500 bg-blue-500/10" 
            : "border-blue-500/30 bg-blue-500/5 hover:bg-blue-500/10 hover:border-blue-500/50"
          }
          ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && !selectedFile && fileInputRef.current?.click()}
        whileHover={!disabled && !selectedFile ? { scale: 1.01 } : {}}
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
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center"
          >
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center mx-auto mb-4 border border-white/10">
              <FileText className="w-8 h-8 text-blue-400" />
            </div>
            <p className="text-white font-medium mb-1 font-mono text-sm truncate max-w-[200px]">
              {selectedFile.name}
            </p>
            <p className="text-slate-500 text-xs font-mono mb-4">
              {(selectedFile.size / 1024).toFixed(1)} KB
            </p>
            <div className="flex gap-3 justify-center">
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  handleClearFile();
                }}
                disabled={disabled}
                className="border-white/10 text-slate-400 hover:text-white bg-transparent"
                data-testid="clear-file-btn"
              >
                <X className="w-4 h-4 mr-1" />
                Annuler
              </Button>
              <Button
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  handleUpload();
                }}
                disabled={disabled}
                className="bg-gradient-to-r from-blue-600 to-purple-600 btn-glow"
                data-testid="upload-submit-btn"
              >
                <UploadCloud className="w-4 h-4 mr-1" />
                Vérifier
              </Button>
            </div>
          </motion.div>
        ) : (
          <>
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/10 to-purple-500/10 flex items-center justify-center mb-4 border border-white/5">
              <UploadCloud className="w-8 h-8 text-blue-400" />
            </div>
            <p className="text-slate-300 font-medium mb-2 text-center">
              Glissez votre fichier ici
            </p>
            <p className="text-slate-500 text-xs font-mono text-center mb-4">
              ou cliquez pour parcourir
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              <span className="px-2 py-1 rounded-md bg-white/5 text-xs font-mono text-slate-400">
                .csv
              </span>
              <span className="px-2 py-1 rounded-md bg-white/5 text-xs font-mono text-slate-400">
                .txt
              </span>
            </div>
          </>
        )}
      </motion.div>
    </div>
  );
}
