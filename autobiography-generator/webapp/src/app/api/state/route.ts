import { NextResponse } from "next/server";
import { loadPipelineState } from "@/lib/data";

export async function GET() {
  const state = loadPipelineState();
  if (!state) {
    return NextResponse.json({ error: "Pipeline state not found" }, { status: 404 });
  }
  return NextResponse.json(state);
}
