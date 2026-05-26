export const AUTH_LOGIN_ENDPOINT = "/api/v1/auth/login";
export const AUTH_REFRESH_ENDPOINT = "/api/v1/auth/refresh";

export const AUTH_SESSION_STORAGE_POLICY = {
  accessToken: "memory_only",
  refreshToken: "not_stored_by_frontend_shell",
  authorization: "backend_owned",
} as const;

export type AuthSession =
  | {
      status: "checking";
    }
  | {
      status: "anonymous";
    }
  | {
      status: "authenticated";
      subject: string;
      accessToken: string;
      expiresAt: string;
    };

export function createAnonymousSession(): AuthSession {
  return { status: "anonymous" };
}

export function isAuthenticatedSession(
  session: AuthSession
): session is Extract<AuthSession, { status: "authenticated" }> {
  return session.status === "authenticated";
}

export function describeSessionStatus(session: AuthSession): string {
  switch (session.status) {
    case "checking":
      return "Checking session";
    case "authenticated":
      return `Signed in as ${session.subject}`;
    case "anonymous":
      return "Signed out";
  }
}
