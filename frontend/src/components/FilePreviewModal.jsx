import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Mail, Phone, FileText, X, Zap, CheckCircle2 } from "lucide-react";
import { Button } from "./ui/button";

export default function FilePreviewModal({ data, onConfirm, onCancel, disabled }) {
  const [selectedType, setSelectedType] = useState(null);
  if (!data) return null;

  const { filename, email_count, phone_count, preview, emails, phones } = data;

  const handleConfirm = (type) => {
    let identifiers = [];
    if (type === "email") identifiers = emails || [];
    else if (type === "phone") identifiers = phones || [];
    else identifiers = [...(emails || []), ...(phones || [])];
    onConfirm(identifiers, type);
  };

  const hasEmails = email_count > 0;
  const hasPhones = phone_count > 0;
  const hasBoth = hasEmails && hasPhones;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        data-testid="file-preview-modal"
      >
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          onClick={onCancel}
        />

        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 12 }}
          transition={{ duration: 0.2 }}
          className="relative w-full max-w-md bg-[#111120] border border-white/[0.08] rounded-xl shadow-2xl overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-5 border-b border-white/[0.04]">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#00d4ff]/[0.08] flex items-center justify-center border border-[#00d4ff]/20">
                <FileText className="w-4 h-4 text-[#00d4ff]" />
              </div>
              <div>
                <h3 className="text-white text-sm font-semibold">Fichier analysé</h3>
                <p className="text-[#55556a] text-[11px] font-mono truncate max-w-[220px]">{filename}</p>
              </div>
            </div>
            <button onClick={onCancel}
              className="p-1.5 rounded-md hover:bg-white/[0.06] text-[#55556a] hover:text-white transition-colors"
              data-testid="close-modal-btn">
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Content */}
          <div className="p-5 space-y-3">
            <div className="grid grid-cols-2 gap-2.5">
              {/* Emails */}
              <button
                className={`relative p-3.5 rounded-lg border text-left transition-all ${
                  selectedType === "email"
                    ? "border-[#00d4ff]/40 bg-[#00d4ff]/[0.06]"
                    : hasEmails
                      ? "border-white/[0.06] bg-white/[0.02] hover:border-[#00d4ff]/20"
                      : "border-white/[0.03] bg-white/[0.01] opacity-40 cursor-not-allowed"
                }`}
                onClick={() => hasEmails && setSelectedType(selectedType === "email" ? null : "email")}
                data-testid="email-card"
              >
                {selectedType === "email" && <CheckCircle2 className="absolute top-2 right-2 w-3.5 h-3.5 text-[#00d4ff]" />}
                <Mail className={`w-6 h-6 mb-1.5 ${hasEmails ? "text-[#00d4ff]" : "text-[#33334a]"}`} />
                <p className={`text-xl font-bold font-mono ${hasEmails ? "text-white" : "text-[#33334a]"}`}>{email_count}</p>
                <p className={`text-[11px] ${hasEmails ? "text-[#8888a0]" : "text-[#33334a]"}`}>
                  email{email_count !== 1 ? "s" : ""}
                </p>
              </button>

              {/* Phones */}
              <button
                className={`relative p-3.5 rounded-lg border text-left transition-all ${
                  selectedType === "phone"
                    ? "border-[#a855f7]/40 bg-[#a855f7]/[0.06]"
                    : hasPhones
                      ? "border-white/[0.06] bg-white/[0.02] hover:border-[#a855f7]/20"
                      : "border-white/[0.03] bg-white/[0.01] opacity-40 cursor-not-allowed"
                }`}
                onClick={() => hasPhones && setSelectedType(selectedType === "phone" ? null : "phone")}
                data-testid="phone-card"
              >
                {selectedType === "phone" && <CheckCircle2 className="absolute top-2 right-2 w-3.5 h-3.5 text-[#a855f7]" />}
                <Phone className={`w-6 h-6 mb-1.5 ${hasPhones ? "text-[#a855f7]" : "text-[#33334a]"}`} />
                <p className={`text-xl font-bold font-mono ${hasPhones ? "text-white" : "text-[#33334a]"}`}>{phone_count}</p>
                <p className={`text-[11px] ${hasPhones ? "text-[#8888a0]" : "text-[#33334a]"}`}>
                  numéro{phone_count !== 1 ? "s" : ""}
                </p>
              </button>
            </div>

            {/* Preview */}
            {hasEmails && (selectedType === null || selectedType === "email") && (
              <div>
                <p className="text-[10px] text-[#55556a] flex items-center gap-1 mb-1">
                  <Mail className="w-2.5 h-2.5" /> Aperçu
                </p>
                <div className="bg-white/[0.02] rounded-md p-2.5 max-h-[80px] overflow-y-auto">
                  {preview.emails.map((email, i) => (
                    <p key={i} className="text-[11px] font-mono text-[#00d4ff]/60 py-px">{email}</p>
                  ))}
                  {email_count > 10 && <p className="text-[11px] font-mono text-[#33334a]">... +{email_count - 10}</p>}
                </div>
              </div>
            )}

            {hasPhones && (selectedType === null || selectedType === "phone") && (
              <div>
                <p className="text-[10px] text-[#55556a] flex items-center gap-1 mb-1">
                  <Phone className="w-2.5 h-2.5" /> Aperçu
                </p>
                <div className="bg-white/[0.02] rounded-md p-2.5 max-h-[80px] overflow-y-auto">
                  {preview.phones.map((phone, i) => (
                    <p key={i} className="text-[11px] font-mono text-[#a855f7]/60 py-px">{phone}</p>
                  ))}
                  {phone_count > 10 && <p className="text-[11px] font-mono text-[#33334a]">... +{phone_count - 10}</p>}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-5 border-t border-white/[0.04] space-y-2">
            {selectedType && (
              <Button onClick={() => handleConfirm(selectedType)} disabled={disabled}
                className="w-full bg-[#00d4ff] text-black hover:bg-[#00d4ff]/90 h-9 text-xs font-semibold"
                data-testid="verify-selected-btn">
                <Zap className="w-3.5 h-3.5 mr-1.5" />
                {selectedType === "email"
                  ? `Vérifier ${email_count} email${email_count !== 1 ? "s" : ""}`
                  : `Vérifier ${phone_count} numéro${phone_count !== 1 ? "s" : ""}`}
              </Button>
            )}

            {!selectedType && (
              <div className="space-y-1.5">
                {hasEmails && (
                  <Button onClick={() => handleConfirm("email")} disabled={disabled}
                    className="w-full bg-[#00d4ff]/10 text-[#00d4ff] hover:bg-[#00d4ff]/20 border border-[#00d4ff]/20 h-9 text-xs"
                    data-testid="verify-emails-btn">
                    <Mail className="w-3.5 h-3.5 mr-1.5" />
                    Vérifier {email_count} email{email_count !== 1 ? "s" : ""}
                  </Button>
                )}
                {hasPhones && (
                  <Button onClick={() => handleConfirm("phone")} disabled={disabled}
                    className="w-full bg-[#a855f7]/10 text-[#a855f7] hover:bg-[#a855f7]/20 border border-[#a855f7]/20 h-9 text-xs"
                    data-testid="verify-phones-btn">
                    <Phone className="w-3.5 h-3.5 mr-1.5" />
                    Vérifier {phone_count} numéro{phone_count !== 1 ? "s" : ""}
                  </Button>
                )}
                {hasBoth && (
                  <Button onClick={() => handleConfirm("all")} disabled={disabled} variant="outline"
                    className="w-full border-white/[0.08] text-[#8888a0] hover:text-white bg-transparent h-9 text-xs"
                    data-testid="verify-all-btn">
                    <Zap className="w-3.5 h-3.5 mr-1.5" />
                    Tout ({email_count + phone_count})
                  </Button>
                )}
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
