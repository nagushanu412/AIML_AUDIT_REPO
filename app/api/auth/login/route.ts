import { NextResponse } from "next/server";
import type { LoginCredentials } from "@/lib/auth/types";

/**
 * Future JWT issuance endpoint — wire to your identity provider.
 * Client currently uses `mockLogin` directly; migrate by POSTing here.
 */
export async function POST(request: Request) {
  const body = (await request.json()) as LoginCredentials;

  if (!body?.email || !body?.password) {
    return NextResponse.json(
      { success: false, error: "Email and password are required." },
      { status: 400 }
    );
  }

  // TODO: validate credentials, issue JWT, check subscription, handle MFA
  return NextResponse.json(
    {
      success: false,
      error: "API auth not configured. Use client-side mock login for development.",
    },
    { status: 501 }
  );
}
