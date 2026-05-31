export const AUTH_LOGIN_ENDPOINT = "/api/v1/auth/login";
export const AUTH_REFRESH_ENDPOINT = "/api/v1/auth/refresh";
export const AUTH_LOGOUT_ENDPOINT = "/api/v1/auth/logout";
export const AUTH_REFRESH_TOKEN_STORAGE_KEY = "taskmaster.refresh_token";

export const AUTH_SESSION_STORAGE_POLICY = {
  accessToken: "memory_only",
  refreshToken: "local_storage_rotating",
  authorization: "backend_owned",
} as const;

export type SessionErrorCode =
  | "expired_session"
  | "invalid_credentials"
  | "invalid_session"
  | "network_error"
  | "revoked_session"
  | "unknown_auth_error";

export type AuthSession =
  | {
      status: "checking";
    }
  | {
      status: "anonymous";
    }
  | {
      status: "authenticated";
      accessToken: string;
      expiresAt: number;
    };

type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
};

type AuthErrorResponse = {
  error_code?: string;
  message?: string;
};

let refreshRequest: Promise<AuthSession> | null = null;

export class SessionRequestError extends Error {
  code: SessionErrorCode;

  constructor(code: SessionErrorCode, message: string) {
    super(message);
    this.code = code;
  }
}

export function createCheckingSession(): AuthSession {
  return { status: "checking" };
}

export function createAnonymousSession(): AuthSession {
  return { status: "anonymous" };
}

export function createAuthenticatedSession(
  tokenResponse: TokenResponse,
  now: () => number = Date.now
): AuthSession {
  persistRefreshToken(tokenResponse.refresh_token);

  return {
    status: "authenticated",
    accessToken: tokenResponse.access_token,
    expiresAt: now() + tokenResponse.expires_in * 1000,
  };
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
      return "Signed in";
    case "anonymous":
      return "Signed out";
  }
}

export async function login(
  email: string,
  password: string
): Promise<AuthSession> {
  try {
    const response = await fetch(AUTH_LOGIN_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
      }),
    });

    return await buildSessionFromResponse(response);
  } catch (error) {
    throw normalizeRequestFailure(error);
  }
}

export async function refreshSession(
  refreshToken: string | null = readStoredRefreshToken()
): Promise<AuthSession> {
  if (refreshToken === null) {
    throw new SessionRequestError("invalid_session", "No refresh token is stored.");
  }

  if (refreshRequest !== null) {
    return refreshRequest;
  }

  refreshRequest = (async () => {
    try {
      const response = await fetch(AUTH_REFRESH_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          refresh_token: refreshToken,
        }),
      });

      return await buildSessionFromResponse(response);
    } catch (error) {
      throw normalizeRequestFailure(error);
    } finally {
      refreshRequest = null;
    }
  })();

  return refreshRequest;
}

export async function logout(
  refreshToken: string | null = readStoredRefreshToken()
): Promise<void> {
  if (refreshToken === null) {
    clearStoredRefreshToken();
    return;
  }

  try {
    const response = await fetch(AUTH_LOGOUT_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        refresh_token: refreshToken,
      }),
    });

    if (!response.ok) {
      await toSessionError(response);
    }
  } finally {
    clearStoredRefreshToken();
  }
}

export function readStoredRefreshToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(AUTH_REFRESH_TOKEN_STORAGE_KEY);
}

export function clearStoredRefreshToken(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(AUTH_REFRESH_TOKEN_STORAGE_KEY);
}

export function getRefreshDelay(session: AuthSession): number | null {
  if (!isAuthenticatedSession(session)) {
    return null;
  }

  return Math.max(1_000, session.expiresAt - Date.now() - 60_000);
}

function persistRefreshToken(refreshToken: string): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(AUTH_REFRESH_TOKEN_STORAGE_KEY, refreshToken);
}

async function buildSessionFromResponse(response: Response): Promise<AuthSession> {
  if (!response.ok) {
    throw await toSessionError(response);
  }

  const data = (await response.json()) as TokenResponse;
  if (data.token_type !== "bearer") {
    throw new SessionRequestError(
      "unknown_auth_error",
      "TaskMaster received an unsupported token response."
    );
  }

  return createAuthenticatedSession(data);
}

async function toSessionError(response: Response): Promise<SessionRequestError> {
  let errorCode: SessionErrorCode = "unknown_auth_error";
  let message = "Authentication failed.";

  try {
    const data = (await response.json()) as AuthErrorResponse;
    if (typeof data.error_code === "string") {
      errorCode = normalizeErrorCode(data.error_code);
    }
    if (typeof data.message === "string" && data.message !== "") {
      message = data.message;
    }
  } catch {
    message = "Authentication failed.";
  }

  return new SessionRequestError(errorCode, message);
}

function normalizeErrorCode(errorCode: string): SessionErrorCode {
  switch (errorCode) {
    case "expired_session":
    case "invalid_credentials":
    case "invalid_session":
    case "revoked_session":
      return errorCode;
    default:
      return "unknown_auth_error";
  }
}

function normalizeRequestFailure(error: unknown): SessionRequestError {
  if (error instanceof SessionRequestError) {
    return error;
  }

  return new SessionRequestError(
    "network_error",
    "TaskMaster could not reach the authentication service."
  );
}
