import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import {
  type AuthSession,
  isAuthenticatedSession,
  type SessionErrorCode,
} from "./session";

type LoginPageProps = {
  authNotice: string | null;
  isSubmitting: boolean;
  onLogin: (email: string, password: string) => Promise<void>;
  session: AuthSession;
};

const MESSAGE_BY_ERROR_CODE: Record<SessionErrorCode, string> = {
  expired_session: "Your session expired. Sign in again.",
  invalid_credentials: "Email or password is incorrect.",
  invalid_session: "Your session is invalid. Sign in again.",
  network_error: "TaskMaster could not reach the authentication service.",
  revoked_session: "Your session was revoked. Sign in again.",
  unknown_auth_error: "Authentication failed. Try again.",
};

export function LoginPage({
  authNotice,
  isSubmitting,
  onLogin,
  session,
}: LoginPageProps) {
  const navigate = useNavigate();
  const [email, setEmail] = useState("person@example.com");
  const [password, setPassword] = useState("secret");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (isAuthenticatedSession(session)) {
    return <Navigate replace to="/workspace" />;
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage(null);

    try {
      await onLogin(email, password);
      navigate("/workspace", { replace: true });
    } catch (error) {
      const errorCode =
        error instanceof Error && "code" in error && typeof error.code === "string"
          ? (error.code as SessionErrorCode)
          : "unknown_auth_error";
      setErrorMessage(MESSAGE_BY_ERROR_CODE[errorCode]);
    }
  };

  return (
    <section aria-labelledby="login-heading">
      <p>Identity</p>
      <h1 id="login-heading">Sign in to TaskMaster</h1>
      <p>Use the backend auth endpoints to start or restore a Phase 1 session.</p>
      {authNotice !== null ? <p role="status">{authNotice}</p> : null}
      {errorMessage !== null ? <p role="alert">{errorMessage}</p> : null}
      <form onSubmit={handleSubmit}>
        <label>
          Email
          <input
            autoComplete="username"
            name="email"
            onChange={(event) => setEmail(event.target.value)}
            type="email"
            value={email}
          />
        </label>
        <label>
          Password
          <input
            autoComplete="current-password"
            name="password"
            onChange={(event) => setPassword(event.target.value)}
            type="password"
            value={password}
          />
        </label>
        <button disabled={isSubmitting} type="submit">
          {isSubmitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </section>
  );
}
