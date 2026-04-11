import { loadPipelineState, loadInterviews, loadChapters, loadSchemas } from "@/lib/data";

const phaseLabels: Record<string, string> = {
  "interview-collection": "Interview Collection",
  structuring: "Structuring",
  drafting: "Drafting",
  revision: "Revision",
  final: "Final",
};

const phaseColors: Record<string, string> = {
  "interview-collection": "bg-blue-100 text-blue-800",
  structuring: "bg-yellow-100 text-yellow-800",
  drafting: "bg-purple-100 text-purple-800",
  revision: "bg-orange-100 text-orange-800",
  final: "bg-green-100 text-green-800",
};

export default function DashboardPage() {
  const state = loadPipelineState();
  const interviews = loadInterviews();
  const chapters = loadChapters();
  const schemas = loadSchemas();

  const phase = state?.meta?.current_phase ?? "unknown";

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2" data-testid="dashboard-title">
        Pipeline Dashboard
      </h1>
      <p className="text-gray-500 mb-8">
        AI Autobiography Generator — Pipeline Overview
      </p>

      {/* Phase Status */}
      <div className="bg-white rounded-lg shadow p-6 mb-6" data-testid="phase-card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
              Current Phase
            </h2>
            <p className="text-2xl font-semibold mt-1">
              {phaseLabels[phase] ?? phase}
            </p>
          </div>
          <span
            className={`px-4 py-2 rounded-full text-sm font-medium ${
              phaseColors[phase] ?? "bg-gray-100 text-gray-800"
            }`}
            data-testid="phase-badge"
          >
            {phase}
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8" data-testid="stats-grid">
        <StatCard
          label="Interviews"
          value={interviews.length}
          detail={`${state?.interviews?.total_collected ?? 0} collected`}
          color="indigo"
        />
        <StatCard
          label="Target Chapters"
          value={state?.meta?.target_chapters ?? 0}
          detail={`${state?.drafts?.chapters_drafted ?? 0} drafted`}
          color="purple"
        />
        <StatCard
          label="Word Target"
          value={
            state?.meta?.target_word_count
              ? `${(state.meta.target_word_count / 1000).toFixed(0)}K`
              : "0"
          }
          detail="target word count"
          color="emerald"
        />
        <StatCard
          label="Schemas"
          value={schemas.length}
          detail="JSON schemas defined"
          color="amber"
        />
      </div>

      {/* Pipeline Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quality Scores */}
        <div className="bg-white rounded-lg shadow p-6" data-testid="quality-card">
          <h3 className="text-lg font-semibold mb-4">Quality Metrics</h3>
          <div className="space-y-3">
            <QualityRow
              label="Voice Consistency"
              value={state?.quality?.voice_consistency_score}
            />
            <QualityRow
              label="Factual Accuracy"
              value={state?.quality?.factual_accuracy_score}
            />
            <QualityRow
              label="Readability (Flesch-Kincaid)"
              value={state?.quality?.readability_avg}
              isGrade
            />
          </div>
          {state?.quality?.last_eval_date && (
            <p className="text-xs text-gray-400 mt-3">
              Last evaluated: {state.quality.last_eval_date}
            </p>
          )}
        </div>

        {/* Available Data */}
        <div className="bg-white rounded-lg shadow p-6" data-testid="data-card">
          <h3 className="text-lg font-semibold mb-4">Available Data</h3>
          <div className="space-y-2">
            <DataRow label="Interview Transcripts" count={interviews.length} />
            <DataRow label="Chapter Drafts" count={chapters.length} />
            <DataRow label="JSON Schemas" count={schemas.length} />
            <DataRow
              label="Pipeline Errors"
              count={state?.pipeline?.errors?.length ?? 0}
              warn
            />
          </div>
        </div>
      </div>

      {/* Interview Preview */}
      {interviews.length > 0 && (
        <div className="mt-8 bg-white rounded-lg shadow p-6" data-testid="interviews-preview">
          <h3 className="text-lg font-semibold mb-4">
            Recent Interviews ({interviews.length})
          </h3>
          <div className="divide-y">
            {interviews.map((iv) => (
              <div key={iv.meta.session_id} className="py-3">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-mono text-sm text-indigo-600">
                      {iv.meta.session_id}
                    </span>
                    <span className="ml-2 text-gray-700">
                      {iv.meta.life_period?.label}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    {iv.meta.themes?.map((t) => (
                      <span
                        key={t}
                        className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  {iv.segments?.length ?? 0} segments |{" "}
                  {iv.meta.duration_minutes} min |{" "}
                  {iv.meta.emotional_tone}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  detail,
  color,
}: {
  label: string;
  value: string | number;
  detail: string;
  color: string;
}) {
  const colorMap: Record<string, string> = {
    indigo: "border-indigo-500 text-indigo-600",
    purple: "border-purple-500 text-purple-600",
    emerald: "border-emerald-500 text-emerald-600",
    amber: "border-amber-500 text-amber-600",
  };
  return (
    <div
      className={`bg-white rounded-lg shadow p-5 border-l-4 ${
        colorMap[color] ?? "border-gray-300"
      }`}
      data-testid={`stat-${label.toLowerCase().replace(/\s/g, "-")}`}
    >
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className="text-3xl font-bold mt-1">{value}</p>
      <p className="text-xs text-gray-400 mt-1">{detail}</p>
    </div>
  );
}

function QualityRow({
  label,
  value,
  isGrade,
}: {
  label: string;
  value: number | null | undefined;
  isGrade?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-600">{label}</span>
      {typeof value === "number" ? (
        <span className="font-mono text-sm font-semibold">
          {isGrade ? value.toFixed(1) : `${(value * 100).toFixed(0)}%`}
        </span>
      ) : (
        <span className="text-xs text-gray-400">Not evaluated</span>
      )}
    </div>
  );
}

function DataRow({
  label,
  count,
  warn,
}: {
  label: string;
  count: number;
  warn?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-600">{label}</span>
      <span
        className={`font-mono text-sm font-semibold ${
          warn && count > 0 ? "text-red-600" : ""
        }`}
      >
        {count}
      </span>
    </div>
  );
}
