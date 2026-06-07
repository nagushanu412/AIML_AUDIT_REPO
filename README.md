# AuditAI Platform — Login

Enterprise SaaS login page for the AuditAI audit automation platform (Next.js 14, React, TypeScript, Tailwind CSS).

## Quick start

```bash
cd auditai-login
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Demo credentials

| Field    | Value                      |
| -------- | -------------------------- |
| Email    | `auditor@demo.auditai.com` |
| Password | `AuditAI2026!`             |

## Project structure

```
app/
  page.tsx          # Two-column login layout
  layout.tsx        # Fonts & metadata
  globals.css       # Tailwind base styles
components/
  auth/
    LoginForm.tsx       # Main form (client)
    BrandingPanel.tsx   # Left branding column
    PasswordInput.tsx   # Password + show/hide
    SSOButton.tsx       # Microsoft / Google placeholders
  ui/
    Button.tsx, Input.tsx, Checkbox.tsx, Spinner.tsx
lib/
  auth/
    mockAuth.ts     # Dummy auth + validation
    types.ts        # JWT / role / subscription types
    constants.ts    # Product copy & feature list
```

## Future integration hooks

- **JWT**: `AuthSession.tokens` in `lib/auth/types.ts`
- **Roles**: `UserRole` on `AuthUser`
- **Subscription**: `subscriptionValid` on `AuthResult`
- **SSO**: Replace `mockMicrosoftSSO` / `mockGoogleSSO`
- **2FA**: Branch on `requiresMfa` in `LoginForm`
