import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mail, Phone, FileText, X, Zap, CheckCircle2 } from "lucide-react";
import { Button } from "./ui/button";

export default function FilePreviewModal({ data, onConfirm, onCancel, disabled }) {
  const [selectedType, setSelectedType] = useState(null);

  if (!data) return null;

  const { filename, email_count, phone_count, preview, emails, phones } = data;

  const handleConfirm = (type) => {
    let identifiers = [];
    if (type === "email") {
      identifiers = emails || [];
    } else if (type === "phone") {
      identifiers = phones || [];
    } else {
      identifiers = [...(emails || []), ...(phones || [])];
    }
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
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/70 backdrop-blur-sm"
          onClick={onCancel}
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          transition={{ type: "spring", duration: 0.5 }}
          className="relative w-full max-w-lg bg-[#0A0710] border border-white/10 rounded-2xl shadow-2xl shadow-purple-500/10 overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-white/5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center border border-white/10">
                <FileText className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <h3 className="text-white font-semibold font-heading">Fichier analysé</h3>
                <p className="text-slate-500 text-xs font-mono truncate max-w-[250px]">{filename}</p>
              </div>
            </div>
            <button
              onClick={onCancel}
              className="p-2 rounded-lg hover:bg-white/5 text-slate-500 hover:text-white transition-colors"
              data-testid="close-modal-btn"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-4">
            {/* Detection Summary */}
            <div className="grid grid-cols-2 gap-3">
              {/* Emails Card */}
              <motion.div
                whileHover={hasEmails ? { scale: 1.02 } : {}}
                className={`
                  relative p-4 rounded-xl border transition-all cursor-pointer
                  ${selectedType === "email"
                    ? "border-blue-500/50 bg-blue-500/10 ring-2 ring-blue-500/30"
                    : hasEmails
                      ? "border-white/10 bg-white/5 hover:border-blue-500/30 hover:bg-blue-500/5"
                      : "border-white/5 bg-white/[0.02] opacity-50 cursor-not-allowed"
                  }
                `}
                onClick={() => hasEmails && setSelectedType(selectedType === "email" ? null : "email")}
                data-testid="email-card"
              >
                {selectedType === "email" && (
                  <CheckCircle2 className="absolute top-2 right-2 w-4 h-4 text-blue-400" />
                )}
                <Mail className={`w-8 h-8 mb-2 ${hasEmails ? "text-blue-400" : "text-slate-600"}`} />
                <p className={`text-2xl font-bold font-mono ${hasEmails ? "text-white" : "text-slate-600"}`}>
                  {email_count}
                </p>
                <p className={`text-xs font-mono ${hasEmails ? "text-slate-400" : "text-slate-600"}`}>
                  email{email_count !== 1 ? "s" : ""} détecté{email_count !== 1 ? "s" : ""}
                </p>
              </motion.div>

              {/* Phones Card */}
              <motion.div
                whileHover={hasPhones ? { scale: 1.02 } : {}}
                className={`
                  relative p-4 rounded-xl border transition-all cursor-pointer
                  ${selectedType === "phone"
                    ? "border-purple-500/50 bg-purple-500/10 ring-2 ring-purple-500/30"
                    : hasPhones
                      ? "border-white/10 bg-white/5 hover:border-purple-500/30 hover:bg-purple-500/5"
                      : "border-white/5 bg-white/[0.02] opacity-50 cursor-not-allowed"
                  }
                `}
                onClick={() => hasPhones && setSelectedType(selectedType === "phone" ? null : "phone")}
                data-testid="phone-card"
              >
                {selectedType === "phone" && (
                  <CheckCircle2 className="absolute top-2 right-2 w-4 h-4 text-purple-400" />
                )}
                <Phone className={`w-8 h-8 mb-2 ${hasPhones ? "text-purple-400" : "text-slate-600"}`} />
                <p className={`text-2xl font-bold font-mono ${hasPhones ? "text-white" : "text-slate-600"}`}>
                  {phone_count}
                </p>
                <p className={`text-xs font-mono ${hasPhones ? "text-slate-400" : "text-slate-600"}`}>
                  numéro{phone_count !== 1 ? "s" : ""} détecté{phone_count !== 1 ? "s" : ""}
                </p>
              </motion.div>
            </div>

            {/* Preview List */}
            <div className="space-y-2">
              {hasEmails && (selectedType === null || selectedType === "email") && (
                <div className="space-y-1">
                  <p className="text-xs font-mono text-slate-500 flex items-center gap-1">
                    <Mail className="w-3 h-3" /> Aperçu emails
                  </p>
                  <div className="bg-white/[0.03] rounded-lg p-3 max-h-[100px] overflow-y-auto scrollbar-thin">
                    {preview.emails.map((email, i) => (
                      <p key={i} className="text-xs font-mono text-blue-300/80 py-0.5">
                        {email}
                      </p>
                    ))}
                    {email_count > 10 && (
                      <p className="text-xs font-mono text-slate-600 py-0.5">
                        ... et {email_count - 10} de plus
                      </p>
                    )}
                  </div>
                </div>
              )}

              {hasPhones && (selectedType === null || selectedType === "phone") && (
                <div className="space-y-1">
                  <p className="text-xs font-mono text-slate-500 flex items-center gap-1">
                    <Phone className="w-3 h-3" /> Aperçu numéros
                  </p>
                  <div className="bg-white/[0.03] rounded-lg p-3 max-h-[100px] overflow-y-auto scrollbar-thin">
                    {preview.phones.map((phone, i) => (
                      <p key={i} className="text-xs font-mono text-purple-300/80 py-0.5">
                        {phone}
                      </p>
                    ))}
                    {phone_count > 10 && (
                      <p className="text-xs font-mono text-slate-600 py-0.5">
                        ... et {phone_count - 10} de plus
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Footer - Action Buttons */}
          <div className="p-6 border-t border-white/5 space-y-3">
            {/* Quick action based on selection */}
            {selectedType && (
              <Button
                onClick={() => handleConfirm(selectedType)}
                disabled={disabled}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:shadow-[0_0_20px_rgba(139,92,246,0.4)] transition-all h-11"
                data-testid="verify-selected-btn"
              >
                <Zap className="w-4 h-4 mr-2" />
                {selectedType === "email"
                  ? `Vérifier ${email_count} email${email_count !== 1 ? "s" : ""}`
                  : `Vérifier ${phone_count} numéro${phone_count !== 1 ? "s" : ""}`
                }
              </Button>
            )}

            {!selectedType && (
              <div className="grid grid-cols-1 gap-2">
                {hasEmails && (
                  <Button
                    onClick={() => handleConfirm("email")}
                    disabled={disabled}
                    className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:shadow-[0_0_15px_rgba(59,130,246,0.3)] transition-all h-10"
                    data-testid="verify-emails-btn"
                  >
                    <Mail className="w-4 h-4 mr-2" />
                    Vérifier {email_count} email{email_count !== 1 ? "s" : ""}
                  </Button>
                )}

                {hasPhones && (
                  <Button
                    onClick={() => handleConfirm("phone")}
                    disabled={disabled}
                    className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:shadow-[0_0_15px_rgba(139,92,246,0.3)] transition-all h-10"
                    data-testid="verify-phones-btn"
                  >
                    <Phone className="w-4 h-4 mr-2" />
                    Vérifier {phone_count} numéro{phone_count !== 1 ? "s" : ""}
                  </Button>
                )}

                {hasBoth && (
                  <Button
                    onClick={() => handleConfirm("all")}
                    disabled={disabled}
                    variant="outline"
                    className="w-full border-white/10 text-slate-300 hover:text-white hover:border-white/20 bg-transparent h-10"
                    data-testid="verify-all-btn"
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    Vérifier tout ({email_count + phone_count})
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
