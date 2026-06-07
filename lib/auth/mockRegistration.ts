import type { RegistrationFormData, RegistrationResult } from "./registrationTypes";
import {
  hasRegistrationErrors,
  validateRegistrationForm,
} from "./validateRegistration";

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Simulates tenant provisioning — replace with POST /api/auth/register */
export async function mockRegister(
  data: RegistrationFormData
): Promise<RegistrationResult> {
  const fieldErrors = validateRegistrationForm(data);

  if (hasRegistrationErrors(fieldErrors)) {
    return {
      success: false,
      error:
        fieldErrors.businessEmail ??
        fieldErrors.password ??
        fieldErrors.confirmPassword ??
        "Please correct the highlighted fields.",
    };
  }

  await delay(1500);

  const email = data.businessEmail.trim().toLowerCase();

  if (email.endsWith("@blocked.com")) {
    return {
      success: false,
      error: "This email domain is not eligible for registration.",
    };
  }

  return {
    success: true,
    organizationId: `org_${Date.now()}`,
  };
}
