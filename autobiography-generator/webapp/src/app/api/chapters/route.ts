import { NextResponse } from "next/server";
import { loadChapters } from "@/lib/data";

export async function GET() {
  const chapters = loadChapters();
  return NextResponse.json({
    chapters: chapters.map((c) => ({
      filename: c.filename,
      wordCount: c.content.split(/\s+/).length,
      preview: c.content.slice(0, 200),
    })),
    count: chapters.length,
  });
}
