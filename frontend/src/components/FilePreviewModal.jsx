import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Mail, Phone, FileText, X, Zap, CheckCircle2 } from "lucide-react";
import { Button } from "./ui/button";

export default function FilePreviewModal({ data, onConfirm, onCancel, disabled }) {
  const [selectedType, setSelectedType] = useState(null);
  if (!data) return null;
  const { filename, email_count, phone_count, preview, emails, phones } = data;
  const handleConfirm = (type) => {
    let ids = type === 'email' ? (emails || []) : type === 'phone' ? (phones || []) : [...(emails || []), ...(phones || [])];
    onConfirm(ids, type);
  };
  const hasE = email_count > 0, hasP = phone_count > 0, hasBoth = hasE && hasP;

  return (
    <AnimatePresence>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center p-4" data-testid="file-preview-modal">
        <motion.div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onCancel} />
        <motion.div initial={{ opacity: 0, scale: 0.95, y: 12 }} animate={{ opacity: 1, scale: 1, y: 0 }} transition={{ duration: 0.2 }}
          className="relative w-full max-w-md bg-[#0C0C16] border border-white/10 rounded-2xl shadow-[0_0_60px_rgba(139,92,246,0.1)] overflow-hidden">

          <div className="flex items-center justify-between p-5 border-b border-white/5">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#00F0FF]/20 to-[#8B5CF6]/20 flex items-center justify-center border border-white/10">
                <FileText className="w-5 h-5 text-[#00F0FF]" />
              </div>
              <div>
                <h3 className="text-white text-sm font-semibold font-heading">Fichier analysé</h3>
                <p className="text-gray-500 text-[11px] font-mono truncate max-w-[220px]">{filename}</p>
              </div>
            </div>
            <button onClick={onCancel} className="p-1.5 rounded-lg hover:bg-white/5 text-gray-500 hover:text-white transition-colors" data-testid="close-modal-btn"><X className="w-4 h-4" /></button>
          </div>

          <div className="p-5 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <button className={`relative p-4 rounded-xl border text-left transition-all ${selectedType === 'email' ? 'border-[#00F0FF]/40 bg-[#00F0FF]/[0.06] shadow-[0_0_20px_rgba(0,240,255,0.08)]' : hasE ? 'border-white/10 bg-white/[0.02] hover:border-[#00F0FF]/20' : 'border-white/5 opacity-40 cursor-not-allowed'}`}
                onClick={() => hasE && setSelectedType(selectedType === 'email' ? null : 'email')} data-testid="email-card">
                {selectedType === 'email' && <CheckCircle2 className="absolute top-2 right-2 w-4 h-4 text-[#00F0FF]" />}
                <Mail className={`w-7 h-7 mb-2 ${hasE ? 'text-[#00F0FF]' : 'text-gray-700'}`} />
                <p className={`text-2xl font-bold font-mono ${hasE ? 'text-white' : 'text-gray-700'}`}>{email_count}</p>
                <p className={`text-xs ${hasE ? 'text-gray-400' : 'text-gray-700'}`}>email{email_count !== 1 ? 's' : ''}</p>
              </button>
              <button className={`relative p-4 rounded-xl border text-left transition-all ${selectedType === 'phone' ? 'border-[#FF00FF]/40 bg-[#FF00FF]/[0.06] shadow-[0_0_20px_rgba(255,0,255,0.08)]' : hasP ? 'border-white/10 bg-white/[0.02] hover:border-[#FF00FF]/20' : 'border-white/5 opacity-40 cursor-not-allowed'}`}
                onClick={() => hasP && setSelectedType(selectedType === 'phone' ? null : 'phone')} data-testid="phone-card">
                {selectedType === 'phone' && <CheckCircle2 className="absolute top-2 right-2 w-4 h-4 text-[#FF00FF]" />}
                <Phone className={`w-7 h-7 mb-2 ${hasP ? 'text-[#FF00FF]' : 'text-gray-700'}`} />
                <p className={`text-2xl font-bold font-mono ${hasP ? 'text-white' : 'text-gray-700'}`}>{phone_count}</p>
                <p className={`text-xs ${hasP ? 'text-gray-400' : 'text-gray-700'}`}>numéro{phone_count !== 1 ? 's' : ''}</p>
              </button>
            </div>

            {hasE && (!selectedType || selectedType === 'email') && (
              <div><p className="text-[10px] text-gray-500 flex items-center gap-1 mb-1"><Mail className="w-2.5 h-2.5" /> Aperçu</p>
                <div className="bg-white/[0.02] rounded-lg p-2.5 max-h-[80px] overflow-y-auto border border-white/5">
                  {preview.emails.map((e, i) => <p key={i} className="text-[11px] font-mono text-[#00F0FF]/40 py-px">{e}</p>)}
                  {email_count > 10 && <p className="text-[11px] font-mono text-gray-700">... +{email_count - 10}</p>}
                </div>
              </div>
            )}
            {hasP && (!selectedType || selectedType === 'phone') && (
              <div><p className="text-[10px] text-gray-500 flex items-center gap-1 mb-1"><Phone className="w-2.5 h-2.5" /> Aperçu</p>
                <div className="bg-white/[0.02] rounded-lg p-2.5 max-h-[80px] overflow-y-auto border border-white/5">
                  {preview.phones.map((p, i) => <p key={i} className="text-[11px] font-mono text-[#FF00FF]/40 py-px">{p}</p>)}
                  {phone_count > 10 && <p className="text-[11px] font-mono text-gray-700">... +{phone_count - 10}</p>}
                </div>
              </div>
            )}
          </div>

          <div className="p-5 border-t border-white/5 space-y-2">
            {selectedType && (
              <Button onClick={() => handleConfirm(selectedType)} disabled={disabled}
                className="w-full btn-click-effect bg-gradient-to-r from-[#00F0FF] to-[#8B5CF6] text-white font-bold h-10 text-xs hover:opacity-90" data-testid="verify-selected-btn">
                <Zap className="w-4 h-4 mr-1.5" />
                {selectedType === 'email' ? `Vérifier ${email_count} email${email_count !== 1 ? 's' : ''}` : `Vérifier ${phone_count} numéro${phone_count !== 1 ? 's' : ''}`}
              </Button>
            )}
            {!selectedType && (
              <div className="space-y-1.5">
                {hasE && <Button onClick={() => handleConfirm('email')} disabled={disabled} className="w-full bg-[#00F0FF]/10 text-[#00F0FF] hover:bg-[#00F0FF]/20 border border-[#00F0FF]/20 h-9 text-xs" data-testid="verify-emails-btn"><Mail className="w-3.5 h-3.5 mr-1.5" /> Vérifier {email_count} email{email_count !== 1 ? 's' : ''}</Button>}
                {hasP && <Button onClick={() => handleConfirm('phone')} disabled={disabled} className="w-full bg-[#FF00FF]/10 text-[#FF00FF] hover:bg-[#FF00FF]/20 border border-[#FF00FF]/20 h-9 text-xs" data-testid="verify-phones-btn"><Phone className="w-3.5 h-3.5 mr-1.5" /> Vérifier {phone_count} numéro{phone_count !== 1 ? 's' : ''}</Button>}
                {hasBoth && <Button onClick={() => handleConfirm('all')} disabled={disabled} variant="outline" className="w-full border-white/10 text-gray-400 hover:text-white bg-transparent h-9 text-xs" data-testid="verify-all-btn"><Zap className="w-3.5 h-3.5 mr-1.5" /> Tout ({email_count + phone_count})</Button>}
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
