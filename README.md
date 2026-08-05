# Flowglad Agent Skills

Official agent skills for authoring and operating Flowglad automations.

## Installation

```bash
npx skills add flowglad/agent-skills
```

## Available skills

| Skill | Description |
| --- | --- |
| [`author-flowglad-ows`](./skills/author-flowglad-ows/) | Author and revise Flowglad-profile Open Workflow Specification programs. |

## Current status

The authoring skill produces canonical Flowglad OWS documents. Flowglad can validate and publish
valid documents as immutable, inactive revisions. Activation and execution require the standalone
OWS executor and are not currently available.
