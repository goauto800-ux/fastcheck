import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Mail, Phone, FileText, X, Zap, CheckCircle2 } from "lucide-react";
import { Button } from "./ui/button";

export default function FilePreviewModal({ data, onConfirm, onCancel, disabled }) {
  const [selectedType, setSelectedType] = useState(null);
  if (!data) return null;
  const { filename, email_count, phone_count, preview, emails, phones } = data;
  const handleConfirm = (type) => {
    let ids = [];
    if (type === "email") ids = emails || [];
    else if (type === "phone") ids = phones || [];
    else ids = [...(emails || []), ...(phones || [])];
    onConfirm(ids, type);
  };
  const hasEmails = email_count > 0;
  const hasPhones = phone_count > 0;
  const hasBoth = hasEmails && hasPhones;

  return (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center p-4" data-testid="file-preview-modal">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onCancel} />
        <motion.div initial={{ opacity: 0, scale: 0.95, y: 12 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 12 }} transition={{ duration: 0.2 }}
          className="relative w-full max-w-md bg-[#0f0f22] border border-[#00e5ff]/10 rounded-xl shadow-2xl overflow-hidden" style={{boxShadow:'0 0 60px rgba(0,229,255,0.06)'}}>

          <div className="flex items-center justify-between p-5 border-b border-white/[0.04]">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#00e5ff]/[0.08] flex items-center justify-center border border-[#00e5ff]/15" style={{boxShadow:'0 0 15px rgba(0,229,255,0.1)'}}>
                <FileText className="w-4 h-4 text-[#00e5ff]" />
              </div>
              <div>
                <h3 className="text-white text-sm font-semibold">Fichier analysé</h3>
                <p className="text-[#44445e] text-[11px] font-mono truncate max-w-[220px]">{filename}</p>
              </div>
            </div>
            <button onClick={onCancel} className="p-1.5 rounded-md hover:bg-white/[0.04] text-[#44445e] hover:text-white transition-colors" data-testid="close-modal-btn"><X className="w-4 h-4" /></button>
          </div>

          <div className="p-5 space-y-3">
            <div className="grid grid-cols-2 gap-2.5">
              <button className={`relative p-3.5 rounded-lg border text-left transition-all ${selectedType === "email" ? "border-[#00e5ff]/30 bg-[#00e5ff]/[0.05]" : hasEmails ? "border-white/[0.05] bg-white/[0.02] hover:border-[#00e5ff]/15" : "border-white/[0.03] opacity-40 cursor-not-allowed"}`}
                style={selectedType === "email" ? {boxShadow:'0 0 20px rgba(0,229,255,0.06)'} : {}}
                onClick={() => hasEmails && setSelectedType(selectedType === "email" ? null : "email")} data-testid="email-card">
                {selectedType === "email" && <CheckCircle2 className="absolute top-2 right-2 w-3.5 h-3.5 text-[#00e5ff]" />}
                <Mail className={`w-6 h-6 mb-1.5 ${hasEmails ? "text-[#00e5ff]" : "text-[#2a2a40]"}`} />
                <p className={`text-xl font-bold font-mono ${hasEmails ? "text-white" : "text-[#2a2a40]"}`}>{email_count}</p>
                <p className={`text-[11px] ${hasEmails ? "text-[#7a7a9a]" : "text-[#2a2a40]"}`}>email{email_count !== 1 ? "s" : ""}</p>
              </button>
              <button className={`relative p-3.5 rounded-lg border text-left transition-all ${selectedType === "phone" ? "border-[#a855f7]/30 bg-[#a855f7]/[0.05]" : hasPhones ? "border-white/[0.05] bg-white/[0.02] hover:border-[#a855f7]/15" : "border-white/[0.03] opacity-40 cursor-not-allowed"}`}
                style={selectedType === "phone" ? {boxShadow:'0 0 20px rgba(168,85,247,0.06)'} : {}}
                onClick={() => hasPhones && setSelectedType(selectedType === "phone" ? null : "phone")} data-testid="phone-card">
                {selectedType === "phone" && <CheckCircle2 className="absolute top-2 right-2 w-3.5 h-3.5 text-[#a855f7]" />}
                <Phone className={`w-6 h-6 mb-1.5 ${hasPhones ? "text-[#a855f7]" : "text-[#2a2a40]"}`} />
                <p className={`text-xl font-bold font-mono ${hasPhones ? "text-white" : "text-[#2a2a40]"}`}>{phone_count}</p>
                <p className={`text-[11px] ${hasPhones ? "text-[#7a7a9a]" : "text-[#2a2a40]"}`}>numéro{phone_count !== 1 ? "s" : ""}</p>
              </button>
            </div>

            {hasEmails && (selectedType === null || selectedType === "email") && (
              <div>
                <p className="text-[10px] text-[#44445e] flex items-center gap-1 mb-1"><Mail className="w-2.5 h-2.5" /> Aperçu</p>
                <div className="bg-white/[0.015] rounded-md p-2.5 max-h-[80px] overflow-y-auto">
                  {preview.emails.map((email, i) => <p key={i} className="text-[11px] font-mono text-[#00e5ff]/50 py-px">{email}</p>)}
                  {email_count > 10 && <p className="text-[11px] font-mono text-[#2a2a40]">... +{email_count - 10}</p>}
                </div>
              </div>
            )}
            {hasPhones && (selectedType === null || selectedType === "phone") && (
              <div>
                <p className="text-[10px] text-[#44445e] flex items-center gap-1 mb-1"><Phone className="w-2.5 h-2.5" /> Aperçu</p>
                <div className="bg-white/[0.015] rounded-md p-2.5 max-h-[80px] overflow-y-auto">
                  {preview.phones.map((phone, i) => <p key={i} className="text-[11px] font-mono text-[#a855f7]/50 py-px">{phone}</p>)}
                  {phone_count > 10 && <p className="text-[11px] font-mono text-[#2a2a40]">... +{phone_count - 10}</p>}
                </div>
              </div>
            )}
          </div>

          <div className="p-5 border-t border-white/[0.04] space-y-2">
            {selectedType && (
              <Button onClick={() => handleConfirm(selectedType)} disabled={disabled} className="w-full bg-[#00e5ff] text-[#060612] hover:bg-[#00e5ff]/90 h-9 text-xs font-semibold btn-glow" data-testid="verify-selected-btn">
                <Zap className="w-3.5 h-3.5 mr-1.5" />
                {selectedType === "email" ? `Vérifier ${email_count} email${email_count !== 1 ? "s" : ""}` : `Vérifier ${phone_count} numéro${phone_count !== 1 ? "s" : ""}`}
              </Button>
            )}
            {!selectedType && (
              <div className="space-y-1.5">
                {hasEmails && <Button onClick={() => handleConfirm("email")} disabled={disabled} className="w-full bg-[#00e5ff]/[0.08] text-[#00e5ff] hover:bg-[#00e5ff]/[0.15] border border-[#00e5ff]/15 h-9 text-xs" data-testid="verify-emails-btn"><Mail className="w-3.5 h-3.5 mr-1.5" /> Vérifier {email_count} email{email_count !== 1 ? "s" : ""}</Button>}
                {hasPhones && <Button onClick={() => handleConfirm("phone")} disabled={disabled} className="w-full bg-[#a855f7]/[0.08] text-[#a855f7] hover:bg-[#a855f7]/[0.15] border border-[#a855f7]/15 h-9 text-xs" data-testid="verify-phones-btn"><Phone className="w-3.5 h-3.5 mr-1.5" /> Vérifier {phone_count} numéro{phone_count !== 1 ? "s" : ""}</Button>}
                {hasBoth && <Button onClick={() => handleConfirm("all")} disabled={disabled} variant="outline" className="w-full border-white/[0.06] text-[#7a7a9a] hover:text-white bg-transparent h-9 text-xs" data-testid="verify-all-btn"><Zap className="w-3.5 h-3.5 mr-1.5" /> Tout ({email_count + phone_count})</Button>}
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
