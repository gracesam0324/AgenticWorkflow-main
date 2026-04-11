import { loadPipelineState, loadQualityData, loadSchemas } from "@/lib/data";

export default function QualityPage() {
  const state = loadPipelineState();
  const qualityData = loadQualityData();
  const schemas = loadSchemas();

  const dimensions = [
    { key: "emotional_authenticity", label: "Emotional Authenticity", description: "How genuine the emotional content feels" },
    { key: "sensory_detail_preservation", label: "Sensory Detail", description: "Retention of sensory details from interviews" },
    { key: "narrative_flow", label: "Narrative Flow", description: "Coherence and pacing of the narrative" },
    { key: "voice_consistency", label: "Voice Consistency", description: "Consistency of the subject's voice throughout" },
    { key: "factual_grounding", label: "Factual Grounding", description: "Accuracy against interview source material" },
  ];

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2" data-testid="quality-title">
        Quality Dashboard
      </h1>
      <p className="text-gray-500 mb-8">
        Quality metrics, schema validation, and pipeline health
      </p>

      {/* Pipeline Quality Scores */}
      <div className="bg-white rounded-lg shadow p-6 mb-6" data-testid="pipeline-quality">
        <h2 className="text-lg font-semibold mb-4">Pipeline Quality Scores</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <QualityMeter
            label="Voice Consistency"
            value={state?.quality?.voice_consistency_score ?? null}
          />
          <QualityMeter
            label="Factual Accuracy"
            value={state?.quality?.factual_accuracy_score ?? null}
          />
          <QualityMeter
            label="Readability (FK Grade)"
            value={state?.quality?.readability_avg ?? null}
            isGrade
          />
        </div>
      </div>

      {/* Quality Dimensions */}
      <div className="bg-white rounded-lg shadow p-6 mb-6" data-testid="quality-dimensions">
        <h2 className="text-lg font-semibold mb-4">Quality Dimensions</h2>
        {qualityData ? (
          <div className="space-y-4">
            {dimensions.map((dim) => {
              const data = qualityData.dimensions[dim.key];
              return (
                <div key={dim.key} className="border-b pb-3 last:border-0">
                  <div className="flex items-center justify-between mb-1">
                    <div>
                      <span className="font-medium text-gray-800">
                        {dim.label}
                      </span>
                      <span className="text-xs text-gray-400 ml-2">
                        {dim.description}
                      </span>
                    </div>
                    {data ? (
                      <div className="flex items-center gap-3">
                        <span className="text-sm text-gray-500">
                          Mean: {data.mean.toFixed(3)}
                        </span>
                        <span className="font-mono font-bold text-lg">
                          {data.latest.toFixed(3)}
                        </span>
                        <TrendBadge trend={data.trend} delta={data.trend_delta} />
                      </div>
                    ) : (
                      <span className="text-xs text-gray-400">No data</span>
                    )}
                  </div>
                  {data && (
                    <div className="w-full bg-gray-100 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          data.latest >= 0.75
                            ? "bg-green-500"
                            : data.latest >= 0.6
                            ? "bg-yellow-500"
                            : "bg-red-500"
                        }`}
                        style={{ width: `${data.latest * 100}%` }}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-gray-400 text-sm" data-testid="no-quality-data">
            No evaluation data available. Run test_quality.py to generate
            evaluation data.
          </p>
        )}
      </div>

      {/* Schemas */}
      <div className="bg-white rounded-lg shadow p-6" data-testid="schemas-card">
        <h2 className="text-lg font-semibold mb-4">
          JSON Schemas ({schemas.length})
        </h2>
        {schemas.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {schemas.map((s) => {
              let parsed: Record<string, unknown> | null = null;
              try {
                parsed = JSON.parse(s.content);
              } catch { /* skip */ }
              const properties = parsed?.properties
                ? Object.keys(parsed.properties as Record<string, unknown>)
                : [];
              return (
                <div
                  key={s.name}
                  className="border rounded-lg p-4"
                  data-testid={`schema-${s.name}`}
                >
                  <h3 className="font-mono text-sm font-semibold text-indigo-700">
                    {s.name}
                  </h3>
                  {typeof parsed?.description === "string" && (
                    <p className="text-xs text-gray-500 mt-1">
                      {parsed.description}
                    </p>
                  )}
                  {properties.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs text-gray-400">
                        {properties.length} properties
                      </p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {properties.slice(0, 8).map((p) => (
                          <span
                            key={p}
                            className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded text-xs font-mono"
                          >
                            {p}
                          </span>
                        ))}
                        {properties.length > 8 && (
                          <span className="text-xs text-gray-400">
                            +{properties.length - 8} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-gray-400 text-sm">No schemas found</p>
        )}
      </div>
    </div>
  );
}

function QualityMeter({
  label,
  value,
  isGrade,
}: {
  label: string;
  value: number | null;
  isGrade?: boolean;
}) {
  return (
    <div className="text-center p-4 border rounded-lg">
      <p className="text-sm text-gray-500 mb-2">{label}</p>
      {typeof value === "number" ? (
        <>
          <p className="text-3xl font-bold">
            {isGrade ? value.toFixed(1) : `${(value * 100).toFixed(0)}%`}
          </p>
          {!isGrade && (
            <div className="w-full bg-gray-100 rounded-full h-2 mt-2">
              <div
                className={`h-2 rounded-full ${
                  value >= 0.75
                    ? "bg-green-500"
                    : value >= 0.6
                    ? "bg-yellow-500"
                    : "bg-red-500"
                }`}
                style={{ width: `${value * 100}%` }}
              />
            </div>
          )}
        </>
      ) : (
        <p className="text-2xl text-gray-300">--</p>
      )}
    </div>
  );
}

function TrendBadge({
  trend,
  delta,
}: {
  trend: string;
  delta: number;
}) {
  const config: Record<string, { bg: string; text: string }> = {
    improving: { bg: "bg-green-100", text: "text-green-700" },
    declining: { bg: "bg-red-100", text: "text-red-700" },
    stable: { bg: "bg-gray-100", text: "text-gray-600" },
  };
  const c = config[trend] ?? config.stable;
  return (
    <span className={`px-2 py-0.5 rounded text-xs ${c.bg} ${c.text}`}>
      {trend} {delta !== 0 ? `(${delta > 0 ? "+" : ""}${delta.toFixed(3)})` : ""}
    </span>
  );
}
