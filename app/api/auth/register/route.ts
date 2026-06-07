import { NextResponse } from "next/server";
import type { RegistrationFormData } from "@/lib/auth/registrationTypes";
import {
  hasRegistrationErrors,
  validateRegistrationForm,
} from "@/lib/auth/validateRegistration";

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as RegistrationFormData;
    const errors = validateRegistrationForm(body);

    if (hasRegistrationErrors(errors)) {
      return NextResponse.json(
        { success: false, errors },
        { status: 400 }
      );
    }

    // TODO: Connect to identity provider, create tenant, send verification email
    const organizationId = `org_${crypto.randomUUID().slice(0, 8)}`;

    return NextResponse.json({
      success: true,
      organizationId,
      message: "Trial account created successfully.",
    });
  } catch {
    return NextResponse.json(
      { success: false, error: "Invalid registration request." },
      { status: 400 }
    );
  }
}
