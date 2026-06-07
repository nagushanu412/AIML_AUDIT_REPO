import type {
  RegistrationFormData,
  RegistrationValidationErrors,
} from "./registrationTypes";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MOBILE_REGEX = /^[+]?[\d\s()-]{10,20}$/;
export const MIN_PASSWORD_LENGTH = 8;

export function validateRegistrationForm(
  data: RegistrationFormData
): RegistrationValidationErrors {
  const errors: RegistrationValidationErrors = {};

  const companyName = data.companyName.trim();
  const adminFullName = data.adminFullName.trim();
  const businessEmail = data.businessEmail.trim();
  const mobileNumber = data.mobileNumber.trim();

  if (!companyName) {
    errors.companyName = "Company name is required.";
  } else if (companyName.length < 2) {
    errors.companyName = "Enter a valid company name.";
  }

  if (!adminFullName) {
    errors.adminFullName = "Admin full name is required.";
  } else if (adminFullName.length < 2) {
    errors.adminFullName = "Enter your full name.";
  }

  if (!businessEmail) {
    errors.businessEmail = "Business email is required.";
  } else if (!EMAIL_REGEX.test(businessEmail)) {
    errors.businessEmail = "Enter a valid business email address.";
  }

  if (!mobileNumber) {
    errors.mobileNumber = "Mobile number is required.";
  } else if (!MOBILE_REGEX.test(mobileNumber)) {
    errors.mobileNumber = "Enter a valid mobile number.";
  }

  if (!data.password) {
    errors.password = "Password is required.";
  } else if (data.password.length < MIN_PASSWORD_LENGTH) {
    errors.password = `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`;
  }

  if (!data.confirmPassword) {
    errors.confirmPassword = "Please confirm your password.";
  } else if (data.password !== data.confirmPassword) {
    errors.confirmPassword = "Passwords do not match.";
  }

  if (!data.agreeToTerms) {
    errors.agreeToTerms = "You must agree to the Terms and Privacy Policy.";
  }

  return errors;
}

export function hasRegistrationErrors(
  errors: RegistrationValidationErrors
): boolean {
  return Object.values(errors).some(Boolean);
}
