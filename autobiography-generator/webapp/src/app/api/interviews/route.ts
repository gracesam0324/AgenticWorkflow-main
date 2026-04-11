import { NextResponse } from "next/server";
import { loadInterviews } from "@/lib/data";

export async function GET() {
  const interviews = loadInterviews();
  return NextResponse.json({ interviews, count: interviews.length });
}
