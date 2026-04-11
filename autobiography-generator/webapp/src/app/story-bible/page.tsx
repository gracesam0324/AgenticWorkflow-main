import { loadStoryBible, loadInterviews } from "@/lib/data";

export default function StoryBiblePage() {
  const bible = loadStoryBible();
  const interviews = loadInterviews();

  // Extract characters/places/events from interviews if no story bible
  const characters = new Map<string, { name: string; relationship: string; sources: string[] }>();
  const places = new Map<string, { name: string; city: string; country: string; sources: string[] }>();
  const events: Array<{ description: string; date: string; significance: string; source: string }> = [];

  for (const iv of interviews) {
    for (const seg of iv.segments ?? []) {
      for (const p of seg.people_mentioned ?? []) {
        const existing = characters.get(p.name);
        if (existing) {
          if (!existing.sources.includes(iv.meta.session_id))
            existing.sources.push(iv.meta.session_id);
        } else {
          characters.set(p.name, {
            name: p.name,
            relationship: p.relationship,
            sources: [iv.meta.session_id],
          });
        }
      }
      for (const pl of seg.places_mentioned ?? []) {
        const key = `${pl.name}-${pl.city}`;
        const existing = places.get(key);
        if (existing) {
          if (!existing.sources.includes(iv.meta.session_id))
            existing.sources.push(iv.meta.session_id);
        } else {
          places.set(key, {
            name: pl.name,
            city: pl.city,
            country: pl.country,
            sources: [iv.meta.session_id],
          });
        }
      }
      for (const ev of seg.events ?? []) {
        events.push({
          description: ev.description,
          date: ev.date_approximate,
          significance: ev.significance,
          source: iv.meta.session_id,
        });
      }
    }
  }

  const sigColors: Record<string, string> = {
    "turning-point": "bg-red-100 text-red-700",
    milestone: "bg-blue-100 text-blue-700",
    background: "bg-gray-100 text-gray-600",
    anecdote: "bg-green-100 text-green-700",
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2" data-testid="story-bible-title">
        Story Bible
      </h1>
      <p className="text-gray-500 mb-8">
        {bible
          ? "Compiled story bible"
          : `Extracted from ${interviews.length} interview transcripts`}
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Characters */}
        <div className="bg-white rounded-lg shadow p-6" data-testid="characters-card">
          <h2 className="text-lg font-semibold mb-4">
            Characters ({characters.size})
          </h2>
          <div className="space-y-3">
            {[...characters.values()].map((c) => (
              <div key={c.name} className="border-b pb-2 last:border-0">
                <p className="font-medium text-gray-800">{c.name}</p>
                <p className="text-sm text-gray-500">{c.relationship}</p>
                <div className="flex gap-1 mt-1">
                  {c.sources.map((s) => (
                    <span
                      key={s}
                      className="px-1.5 py-0.5 bg-indigo-50 text-indigo-600 rounded text-xs"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            ))}
            {characters.size === 0 && (
              <p className="text-gray-400 text-sm">No characters found</p>
            )}
          </div>
        </div>

        {/* Places */}
        <div className="bg-white rounded-lg shadow p-6" data-testid="places-card">
          <h2 className="text-lg font-semibold mb-4">
            Places ({places.size})
          </h2>
          <div className="space-y-3">
            {[...places.values()].map((p) => (
              <div key={`${p.name}-${p.city}`} className="border-b pb-2 last:border-0">
                <p className="font-medium text-gray-800">{p.name}</p>
                <p className="text-sm text-gray-500">
                  {p.city}, {p.country}
                </p>
                <div className="flex gap-1 mt-1">
                  {p.sources.map((s) => (
                    <span
                      key={s}
                      className="px-1.5 py-0.5 bg-emerald-50 text-emerald-600 rounded text-xs"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            ))}
            {places.size === 0 && (
              <p className="text-gray-400 text-sm">No places found</p>
            )}
          </div>
        </div>

        {/* Timeline */}
        <div className="bg-white rounded-lg shadow p-6" data-testid="timeline-card">
          <h2 className="text-lg font-semibold mb-4">
            Timeline ({events.length} events)
          </h2>
          <div className="space-y-3">
            {events.map((ev, i) => (
              <div key={i} className="border-b pb-2 last:border-0">
                <div className="flex items-start justify-between">
                  <p className="text-sm font-medium text-gray-800">
                    {ev.description}
                  </p>
                  <span
                    className={`px-2 py-0.5 rounded text-xs shrink-0 ml-2 ${
                      sigColors[ev.significance] ?? "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {ev.significance}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {ev.date} | {ev.source}
                </p>
              </div>
            ))}
            {events.length === 0 && (
              <p className="text-gray-400 text-sm">No events found</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
