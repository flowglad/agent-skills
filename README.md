# Flowglad Agent Skills

Official agent skills for authoring reusable Flowglad capabilities and composing them into
automations.

## Installation

```bash
npx skills add flowglad/agent-skills
```

## Available skills

| Skill | Description |
| --- | --- |
| [`author-flowglad-skill`](./skills/author-flowglad-skill/) | Author, submit, and follow verification for reusable Flowglad Skill packages. |
| [`author-flowglad-ows`](./skills/author-flowglad-ows/) | Compose verified Skill revisions and other Flowglad capabilities into OWS programs. |

## Current status

Flowglad automatically verifies packages submitted through the Skill lifecycle. The OWS authoring
skill composes exact verified Skill revisions and other Flowglad capabilities into canonical OWS
documents. Flowglad validates and publishes valid documents as immutable revisions for the
standalone OWS executor. Activation validates the sealed runtime identity, while routing remains
default-off and organization-allowlisted. Successful compilation alone does not authorize
execution.
