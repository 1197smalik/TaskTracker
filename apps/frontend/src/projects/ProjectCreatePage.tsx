import { FormEvent, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { type AuthenticatedApiClient } from "../identity/apiClient";
import { createProject, ProjectCreateError } from "./api";

type ProjectCreatePageProps = {
  apiClient: AuthenticatedApiClient;
  isAuthenticated: boolean;
  onProjectCreated: (project: {
    id: string;
    workspaceId: string;
    key: string;
    name: string;
  }) => Promise<void>;
};

export function ProjectCreatePage({
  apiClient,
  isAuthenticated,
  onProjectCreated,
}: ProjectCreatePageProps) {
  const navigate = useNavigate();
  const { workspaceId } = useParams();
  const [key, setKey] = useState("");
  const [name, setName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [keyErrors, setKeyErrors] = useState<string[]>([]);
  const [nameErrors, setNameErrors] = useState<string[]>([]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (workspaceId === undefined) {
      setErrorMessage("Project creation requires a workspace context.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setKeyErrors([]);
    setNameErrors([]);

    try {
      const project = await createProject(apiClient, workspaceId, key, name);
      await onProjectCreated(project);
      navigate(`/workspace/${workspaceId}/projects/${project.id}`);
    } catch (error) {
      if (error instanceof ProjectCreateError) {
        setErrorMessage(error.message);
        setKeyErrors(error.fieldErrors.key ?? []);
        setNameErrors(error.fieldErrors.name ?? []);
      } else if (error instanceof Error) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("Project creation failed.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section aria-labelledby="project-create-heading">
      <p>Project</p>
      <h1 id="project-create-heading">Create project</h1>
      <p>
        Create the Phase 1 project shell inside the selected workspace. Boards and
        work item wiring stay in later stories.
      </p>
      {!isAuthenticated ? (
        <p>Sign in before creating a project.</p>
      ) : (
        <form onSubmit={handleSubmit}>
          <label htmlFor="project-key">Project key</label>
          <input
            id="project-key"
            name="key"
            onChange={(event) => setKey(event.target.value)}
            value={key}
          />
          {keyErrors.map((message) => (
            <p key={message} role="alert">
              {message}
            </p>
          ))}
          <label htmlFor="project-name">Project name</label>
          <input
            id="project-name"
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
            {isSubmitting ? "Creating..." : "Create project"}
          </button>
        </form>
      )}
    </section>
  );
}
