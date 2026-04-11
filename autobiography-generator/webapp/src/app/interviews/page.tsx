import { loadInterviews } from "@/lib/data";

export default function InterviewsPage() {
  const interviews = loadInterviews();

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2" data-testid="interviews-title">
        Interview Transcripts
      </h1>
      <p className="text-gray-500 mb-8">
        {interviews.length} interview sessions available
      </p>

      {interviews.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-400" data-testid="no-interviews">
          No interview transcripts found.
        </div>
      ) : (
        <div className="space-y-6">
          {interviews.map((iv) => (
            <div
              key={iv.meta.session_id}
              className="bg-white rounded-lg shadow overflow-hidden"
              data-testid={`interview-${iv.meta.session_id}`}
            >
              {/* Header */}
              <div className="bg-indigo-50 px-6 py-4 border-b">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-indigo-900">
                      {iv.meta.session_id}: {iv.meta.life_period?.label}
                    </h2>
                    <p className="text-sm text-indigo-600">
                      Subject: {iv.meta.subject_name} | Date: {iv.meta.date} |{" "}
                      {iv.meta.duration_minutes} minutes
                    </p>
                  </div>
                  <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm">
                    {iv.meta.emotional_tone}
                  </span>
                </div>
                <div className="flex gap-2 mt-2">
                  {iv.meta.themes?.map((t) => (
                    <span
                      key={t}
                      className="px-2 py-0.5 bg-white text-indigo-600 rounded text-xs border border-indigo-200"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              {/* Segments */}
              <div className="divide-y">
                {iv.segments?.map((seg) => (
                  <div key={seg.segment_id} className="px-6 py-4">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <span className="font-mono text-xs text-gray-400">
                          {seg.segment_id}
                        </span>
                        <h3 className="font-medium text-gray-800">
                          {seg.topic}
                        </h3>
                      </div>
                      <div className="flex gap-1">
                        {seg.emotional_markers?.map((em, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 bg-amber-50 text-amber-700 rounded text-xs"
                            title={`Trigger: ${em.trigger}`}
                          >
                            {em.emotion} ({em.intensity}/10)
                          </span>
                        ))}
                      </div>
                    </div>
                    <p className="text-gray-600 text-sm leading-relaxed">
                      {seg.content}
                    </p>

                    {/* Key Quotes */}
                    {seg.key_quotes?.length > 0 && (
                      <div className="mt-3 space-y-2">
                        {seg.key_quotes.map((q, i) => (
                          <blockquote
                            key={i}
                            className="border-l-3 border-indigo-300 pl-3 text-sm italic text-gray-700"
                          >
                            &ldquo;{q.text}&rdquo;
                            <span className="text-xs text-gray-400 ml-2 not-italic">
                              — {q.context}
                            </span>
                          </blockquote>
                        ))}
                      </div>
                    )}

                    {/* People & Places */}
                    <div className="flex gap-4 mt-3 text-xs text-gray-500">
                      {seg.people_mentioned?.length > 0 && (
                        <span>
                          People:{" "}
                          {seg.people_mentioned
                            .map((p) => `${p.name} (${p.relationship})`)
                            .join(", ")}
                        </span>
                      )}
                      {seg.places_mentioned?.length > 0 && (
                        <span>
                          Places:{" "}
                          {seg.places_mentioned
                            .map((p) => `${p.name}, ${p.city}`)
                            .join("; ")}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
