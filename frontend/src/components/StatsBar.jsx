import { Users, CheckCircle, XCircle, AlertCircle, ShieldAlert } from "lucide-react";

export default function StatsBar({ stats }) {
  return (
    <div className="flex flex-wrap gap-5" data-testid="stats-bar">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-md bg-[#00d4ff]/[0.08] flex items-center justify-center">
          <Users className="w-3.5 h-3.5 text-[#00d4ff]" />
        </div>
        <div>
          <p className="text-[10px] text-[#55556a] uppercase tracking-wider">Total</p>
          <p className="text-base font-semibold text-white font-mono leading-none">{stats.total}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-md bg-[#00ff88]/[0.08] flex items-center justify-center">
          <CheckCircle className="w-3.5 h-3.5 text-[#00ff88]" />
        </div>
        <div>
          <p className="text-[10px] text-[#55556a] uppercase tracking-wider">Trouvés</p>
          <p className="text-base font-semibold text-[#00ff88] font-mono leading-none">{stats.found}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-md bg-[#ff3860]/[0.08] flex items-center justify-center">
          <XCircle className="w-3.5 h-3.5 text-[#ff3860]" />
        </div>
        <div>
          <p className="text-[10px] text-[#55556a] uppercase tracking-wider">Non trouvés</p>
          <p className="text-base font-semibold text-[#ff3860] font-mono leading-none">{stats.notFound}</p>
        </div>
      </div>

      {stats.unverifiable > 0 && (
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-[#ffb020]/[0.08] flex items-center justify-center">
            <ShieldAlert className="w-3.5 h-3.5 text-[#ffb020]" />
          </div>
          <div>
            <p className="text-[10px] text-[#55556a] uppercase tracking-wider">Non vérifiables</p>
            <p className="text-base font-semibold text-[#ffb020] font-mono leading-none">{stats.unverifiable}</p>
          </div>
        </div>
      )}

      {stats.rateLimited > 0 && (
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-orange-500/[0.08] flex items-center justify-center">
            <AlertCircle className="w-3.5 h-3.5 text-orange-400" />
          </div>
          <div>
            <p className="text-[10px] text-[#55556a] uppercase tracking-wider">Limités</p>
            <p className="text-base font-semibold text-orange-400 font-mono leading-none">{stats.rateLimited}</p>
          </div>
        </div>
      )}
    </div>
  );
}
