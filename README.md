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
skill produces canonical Flowglad OWS documents and can prefer exact verified Skill revisions for
code resources. Flowglad can validate and publish valid OWS documents as immutable, inactive
revisions. Activation and execution require the standalone OWS executor and are not currently
available.
