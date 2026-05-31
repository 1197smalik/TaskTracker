import {
  type AuthSession,
  isAuthenticatedSession,
  refreshSession,
  SessionRequestError,
} from "./session";

export type AuthenticatedApiClient = {
  getJson<T>(path: string): Promise<T>;
  request(path: string, init?: globalThis.RequestInit): Promise<Response>;
};

type AuthenticatedApiClientOptions = {
  getSession: () => AuthSession;
  onSessionInvalidated: (error: SessionRequestError) => void;
  onSessionRenewed: (session: AuthSession) => void;
};

export function createAuthenticatedApiClient({
  getSession,
  onSessionInvalidated,
  onSessionRenewed,
}: AuthenticatedApiClientOptions): AuthenticatedApiClient {
  return {
    async getJson<T>(path: string): Promise<T> {
      const response = await requestWithAuthentication(path);

      if (!response.ok) {
        throw new ApiClientResponseError(
          response.status,
          `Authenticated request failed with HTTP ${response.status}.`
        );
      }

      return (await response.json()) as T;
    },
    request(path: string, init?: globalThis.RequestInit): Promise<Response> {
      return requestWithAuthentication(path, init);
    },
  };

  async function requestWithAuthentication(
    path: string,
    init?: globalThis.RequestInit,
    hasRetried = false
  ): Promise<Response> {
    const session = getSession();
    if (!isAuthenticatedSession(session)) {
      throw new SessionRequestError(
        "invalid_session",
        "Protected API requests require an authenticated session."
      );
    }

    const response = await fetch(path, withBearerToken(session.accessToken, init));
    if (response.status !== 401 || hasRetried) {
      return response;
    }

    try {
      const renewedSession = await refreshSession();
      onSessionRenewed(renewedSession);
      return await requestWithAuthentication(path, init, true);
    } catch (error) {
      const sessionError =
        error instanceof SessionRequestError
          ? error
          : new SessionRequestError(
              "network_error",
              "TaskMaster could not reach the authentication service."
            );
      onSessionInvalidated(sessionError);
      throw sessionError;
    }
  }
}

export class ApiClientResponseError extends Error {
  statusCode: number;

  constructor(statusCode: number, message: string) {
    super(message);
    this.statusCode = statusCode;
  }
}

function withBearerToken(
  accessToken: string,
  init?: globalThis.RequestInit
): globalThis.RequestInit {
  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${accessToken}`);

  return {
    ...init,
    headers,
  };
}
