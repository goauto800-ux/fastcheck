import { Users, CheckCircle, XCircle, AlertCircle, ShieldAlert } from "lucide-react";

export default function StatsBar({ stats }) {
  return (
    <div className="flex flex-wrap gap-5" data-testid="stats-bar">
      {[
        { label: 'Total', value: stats.total, icon: Users, color: 'from-[#00F0FF] to-[#8B5CF6]', text: 'text-white' },
        { label: 'Trouvés', value: stats.found, icon: CheckCircle, color: 'from-green-500 to-emerald-600', text: 'text-green-400' },
        { label: 'Non trouvés', value: stats.notFound, icon: XCircle, color: 'from-red-500 to-rose-600', text: 'text-red-400' },
      ].map((s, i) => (
        <div key={i} className="flex items-center gap-2.5">
          <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${s.color} flex items-center justify-center`}>
            <s.icon className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">{s.label}</p>
            <p className={`text-lg font-bold font-mono leading-none ${s.text}`}>{s.value}</p>
          </div>
        </div>
      ))}

      {stats.unverifiable > 0 && (
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-yellow-500 to-orange-600 flex items-center justify-center">
            <ShieldAlert className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">N/V</p>
            <p className="text-lg font-bold font-mono leading-none text-yellow-400">{stats.unverifiable}</p>
          </div>
        </div>
      )}

      {stats.rateLimited > 0 && (
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center">
            <AlertCircle className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">Limités</p>
            <p className="text-lg font-bold font-mono leading-none text-orange-400">{stats.rateLimited}</p>
          </div>
        </div>
      )}
    </div>
  );
}
