import { NextResponse } from "next/server";
import { loadQualityData, loadSchemas } from "@/lib/data";

export async function GET() {
  const quality = loadQualityData();
  const schemas = loadSchemas();
  return NextResponse.json({
    quality,
    schemas: schemas.map((s) => s.name),
    schemasCount: schemas.length,
  });
}
