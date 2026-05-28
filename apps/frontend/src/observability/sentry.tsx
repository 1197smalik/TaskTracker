import React from "react";
import * as Sentry from "@sentry/react";

export const FRONTEND_SENTRY_DSN_ENV_VAR = "VITE_SENTRY_DSN";
export const FRONTEND_SENTRY_ALLOWED_CONTEXT_FIELDS = [
  "correlation_id",
  "route_template",
  "method",
  "status_code",
] as const;
export const FRONTEND_SENTRY_FORBIDDEN_CONTEXT_FIELDS = [
  "raw_path",
  "query_string",
  "authorization",
  "cookie",
  "token",
  "access_token",
  "refresh_token",
  "password",
  "secret",
  "email",
  "user_id",
] as const;

type FrontendRuntimeEnv = Record<string, string | boolean | undefined>;

export type FrontendSentryStrategy = {
  enabled: boolean;
  dsnEnvVar: typeof FRONTEND_SENTRY_DSN_ENV_VAR;
  captureUnhandledErrors: true;
  captureUnhandledRejections: true;
  captureServerErrors: true;
  sendDefaultPii: false;
  userMessage: string;
};

type ErrorBoundaryState = {
  hasError: boolean;
};

const FALLBACK_MESSAGE = "Something went wrong. Please try again.";

export function buildFrontendSentryStrategy(
  env: FrontendRuntimeEnv = import.meta.env,
): FrontendSentryStrategy {
  const dsn = env[FRONTEND_SENTRY_DSN_ENV_VAR];
  return {
    enabled: typeof dsn === "string" && dsn.trim() !== "",
    dsnEnvVar: FRONTEND_SENTRY_DSN_ENV_VAR,
    captureUnhandledErrors: true,
    captureUnhandledRejections: true,
    captureServerErrors: true,
    sendDefaultPii: false,
    userMessage: FALLBACK_MESSAGE,
  };
}

export function redactFrontendSentryEvent(
  event: Sentry.ErrorEvent,
): Sentry.ErrorEvent {
  return redactFrontendValue(event) as Sentry.ErrorEvent;
}

export function initFrontendSentry(
  env: FrontendRuntimeEnv = import.meta.env,
): FrontendSentryStrategy {
  const strategy = buildFrontendSentryStrategy(env);
  if (!strategy.enabled) {
    return strategy;
  }

  const dsn = env[FRONTEND_SENTRY_DSN_ENV_VAR];
  if (typeof dsn !== "string") {
    return strategy;
  }

  Sentry.init({
    dsn,
    sendDefaultPii: strategy.sendDefaultPii,
    beforeSend: redactFrontendSentryEvent,
  });
  return strategy;
}

export function captureFrontendServerError(details: {
  status: number;
  routeTemplate: string;
  correlationId?: string;
}): boolean {
  if (details.status < 500 || details.status > 599) {
    return false;
  }

  Sentry.captureMessage("frontend.server_error", {
    level: "error",
    tags: {
      route_template: details.routeTemplate,
      status_code: String(details.status),
    },
    extra: {
      correlation_id: details.correlationId,
      route_template: details.routeTemplate,
      status_code: details.status,
    },
  });
  return true;
}

export class AppErrorBoundary extends React.Component<
  React.PropsWithChildren,
  ErrorBoundaryState
> {
  override state: ErrorBoundaryState = {
    hasError: false,
  };

  override componentDidCatch(
    error: Error,
    errorInfo: React.ErrorInfo,
  ): void {
    Sentry.captureException(error, {
      extra: {
        componentStack: errorInfo.componentStack,
      },
    });
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  override render(): React.ReactNode {
    if (this.state.hasError) {
      return (
        <section aria-labelledby="app-error-heading" role="alert">
          <p>Application error</p>
          <h1 id="app-error-heading">{FALLBACK_MESSAGE}</h1>
          <p>
            The frontend shell captured the failure for observability and kept
            the message free of sensitive details.
          </p>
        </section>
      );
    }

    return this.props.children;
  }
}

function redactFrontendValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(redactFrontendValue);
  }
  if (value === null || typeof value !== "object") {
    return value;
  }

  const redacted: Record<string, unknown> = {};
  for (const [key, nestedValue] of Object.entries(value)) {
    if (
      FRONTEND_SENTRY_FORBIDDEN_CONTEXT_FIELDS.includes(
        key.toLowerCase() as (typeof FRONTEND_SENTRY_FORBIDDEN_CONTEXT_FIELDS)[number],
      )
    ) {
      continue;
    }
    redacted[key] = redactFrontendValue(nestedValue);
  }
  return redacted;
}
