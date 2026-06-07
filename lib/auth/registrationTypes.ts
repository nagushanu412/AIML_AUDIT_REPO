export interface RegistrationFormData {
  companyName: string;
  adminFullName: string;
  businessEmail: string;
  mobileNumber: string;
  password: string;
  confirmPassword: string;
  agreeToTerms: boolean;
}

export interface RegistrationValidationErrors {
  companyName?: string;
  adminFullName?: string;
  businessEmail?: string;
  mobileNumber?: string;
  password?: string;
  confirmPassword?: string;
  agreeToTerms?: string;
}

export interface RegistrationResult {
  success: boolean;
  error?: string;
  organizationId?: string;
}
