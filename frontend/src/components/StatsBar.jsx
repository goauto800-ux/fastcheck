import { motion } from "framer-motion";
import { Users, CheckCircle, XCircle } from "lucide-react";

export default function StatsBar({ stats }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex flex-wrap gap-4 sm:gap-6"
      data-testid="stats-bar"
    >
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
          <Users className="w-4 h-4 text-blue-400" />
        </div>
        <div>
          <p className="text-xs text-slate-500 font-mono uppercase tracking-wider">Total</p>
          <p className="text-lg font-bold text-white font-mono">{stats.total}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
          <CheckCircle className="w-4 h-4 text-emerald-400" />
        </div>
        <div>
          <p className="text-xs text-slate-500 font-mono uppercase tracking-wider">Trouvés</p>
          <p className="text-lg font-bold text-emerald-400 font-mono">{stats.found}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-rose-500/10 flex items-center justify-center">
          <XCircle className="w-4 h-4 text-rose-400" />
        </div>
        <div>
          <p className="text-xs text-slate-500 font-mono uppercase tracking-wider">Non trouvés</p>
          <p className="text-lg font-bold text-rose-400 font-mono">{stats.notFound}</p>
        </div>
      </div>
    </motion.div>
  );
}
