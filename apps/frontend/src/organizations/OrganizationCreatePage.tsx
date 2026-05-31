import { FormEvent, useState } from "react";

import { type AuthenticatedApiClient } from "../identity/apiClient";
import { createOrganization, OrganizationCreateError } from "./api";

type OrganizationCreatePageProps = {
  apiClient: AuthenticatedApiClient;
  isAuthenticated: boolean;
};

export function OrganizationCreatePage({
  apiClient,
  isAuthenticated,
}: OrganizationCreatePageProps) {
  const [name, setName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [nameErrors, setNameErrors] = useState<string[]>([]);
  const [createdOrganization, setCreatedOrganization] = useState<{
    id: string;
    name: string;
    createdAt: string;
  } | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    setIsSubmitting(true);
    setErrorMessage(null);
    setNameErrors([]);

    try {
      const organization = await createOrganization(apiClient, name);
      setCreatedOrganization(organization);
      setName(organization.name);
    } catch (error) {
      if (error instanceof OrganizationCreateError) {
        setErrorMessage(error.message);
        setNameErrors(error.fieldErrors.name ?? []);
      } else if (error instanceof Error) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage("Organization creation failed.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section aria-labelledby="organization-create-heading">
      <p>Organization</p>
      <h1 id="organization-create-heading">Create organization</h1>
      <p>
        Create the Phase 1 organization boundary with the authenticated API client.
        Workspace creation stays in the next story.
      </p>
      {!isAuthenticated ? (
        <p>Sign in before creating an organization.</p>
      ) : (
        <form onSubmit={handleSubmit}>
          <label htmlFor="organization-name">Organization name</label>
          <input
            id="organization-name"
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
            {isSubmitting ? "Creating..." : "Create organization"}
          </button>
        </form>
      )}
      {createdOrganization !== null ? (
        <section aria-label="Created organization">
          <h2>{createdOrganization.name}</h2>
          <p>Organization id: {createdOrganization.id}</p>
          <p>Created at: {createdOrganization.createdAt}</p>
          <p>Organization state is ready for workspace setup in the next story.</p>
        </section>
      ) : null}
    </section>
  );
}
