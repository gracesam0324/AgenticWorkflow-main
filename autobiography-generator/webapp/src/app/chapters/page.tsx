import { loadChapters } from "@/lib/data";

export default function ChaptersPage() {
  const chapters = loadChapters();

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2" data-testid="chapters-title">
        Chapter Drafts
      </h1>
      <p className="text-gray-500 mb-8">
        {chapters.length} chapter files available
      </p>

      {chapters.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-400" data-testid="no-chapters">
          No chapter drafts found. Run the pipeline to generate chapters.
        </div>
      ) : (
        <div className="space-y-6">
          {chapters.map((ch) => {
            const wordCount = ch.content.split(/\s+/).length;
            const paragraphs = ch.content
              .split("\n\n")
              .filter((p) => p.trim().length > 0);
            const headings = ch.content
              .split("\n")
              .filter((l) => l.startsWith("#"));
            const preview = ch.content.slice(0, 500);

            return (
              <div
                key={ch.filename}
                className="bg-white rounded-lg shadow overflow-hidden"
                data-testid={`chapter-${ch.filename}`}
              >
                <div className="bg-purple-50 px-6 py-4 border-b flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-purple-900">
                      {ch.filename}
                    </h2>
                    <div className="flex gap-4 text-sm text-purple-600 mt-1">
                      <span>{wordCount.toLocaleString()} words</span>
                      <span>{paragraphs.length} paragraphs</span>
                      <span>{headings.length} headings</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-2xl font-bold text-purple-700">
                      {wordCount.toLocaleString()}
                    </span>
                    <p className="text-xs text-purple-400">words</p>
                  </div>
                </div>
                <div className="px-6 py-4">
                  {headings.length > 0 && (
                    <div className="mb-4">
                      <h3 className="text-sm font-medium text-gray-500 mb-2">
                        Structure
                      </h3>
                      <div className="space-y-1">
                        {headings.map((h, i) => {
                          const level = h.match(/^#+/)?.[0]?.length ?? 1;
                          return (
                            <p
                              key={i}
                              className="text-sm text-gray-700"
                              style={{ paddingLeft: `${(level - 1) * 16}px` }}
                            >
                              {h.replace(/^#+\s*/, "")}
                            </p>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-2">
                      Preview
                    </h3>
                    <div className="bg-gray-50 rounded p-4 text-sm text-gray-700 leading-relaxed font-serif whitespace-pre-wrap">
                      {preview}
                      {ch.content.length > 500 && (
                        <span className="text-gray-400">
                          {"\n\n"}[... {wordCount - preview.split(/\s+/).length}{" "}
                          more words ...]
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
