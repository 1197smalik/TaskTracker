import { FormEvent, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { type AuthenticatedApiClient } from "../identity/apiClient";
import { createWorkspace, WorkspaceCreateError } from "./api";

type WorkspaceCreatePageProps = {
  apiClient: AuthenticatedApiClient;
  isAuthenticated: boolean;
  onWorkspaceCreated: (workspace: {
    id: string;
    organizationId: string;
    name: string;
  }) => Promise<void>;
};

export function WorkspaceCreatePage({
  apiClient,
  isAuthenticated,
  onWorkspaceCreated,
}: WorkspaceCreatePageProps) {
  const navigate = useNavigate();
  const { organizationId } = useParams();
  const [name, setName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [nameErrors, setNameErrors] = useState<string[]>([]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (organizationId === undefined) {
      setErrorMessage("Workspace creation requires an organization context.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setNameErrors([]);

    try {
      const workspace = await createWorkspace(apiClient, organizationId, name);
      await onWorkspaceCreated(workspace);
      navigate("/workspace");
    } catch (error) {
      if (error instanceof WorkspaceCreateError) {
        setErrorMessage(error.message);
        setNameErrors(error.fieldErrors.name ?? []);
      } else if (error instanceof Error) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("Workspace creation failed.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section aria-labelledby="workspace-create-heading">
      <p>Workspace</p>
      <h1 id="workspace-create-heading">Create workspace</h1>
      <p>
        Create the Phase 1 workspace shell inside the selected organization.
        Project creation stays in the next story.
      </p>
      {!isAuthenticated ? (
        <p>Sign in before creating a workspace.</p>
      ) : (
        <form onSubmit={handleSubmit}>
          <label htmlFor="workspace-name">Workspace name</label>
          <input
            id="workspace-name"
            name="name"
            onChange={(event) => setName(event.target.value)}
            value={name}
          />
          {nameErrors.map((message) => (
            <p key={message} role="alert">
              {message}
            </p>
          ))}
          {errorMessage !== null ? <p role="alert">{errorMessage}</p> : null}
          <button disabled={isSubmitting} type="submit">
            {isSubmitting ? "Creating..." : "Create workspace"}
          </button>
        </form>
      )}
    </section>
  );
}
