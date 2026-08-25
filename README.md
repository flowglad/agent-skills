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
| [`author-flowglad-skill`](./skills/author-flowglad-skill/) | Author, submit, and follow verification for OWS-native Flowglad Skill packages. |
| [`author-flowglad-ows`](./skills/author-flowglad-ows/) | Compose verified Skill revisions and other Flowglad capabilities into OWS programs. |

## Current status

Flowglad automatically verifies packages submitted through the Skill lifecycle. The OWS authoring
skill composes exact verified Skill revisions and other Flowglad capabilities into canonical OWS
documents. Flowglad validates and publishes valid documents as immutable revisions for the
standalone OWS executor. Activation validates the sealed runtime identity. Successful compilation
alone does not authorize publication, activation, or execution.

## Validation and source sync

The compiler guide, executor ABI, and canonical examples are exported from the private
`flowglad/provisioning-agent` repository with source hashes recorded in `sources.lock.json`.

From a checkout with both repositories available:

```bash
python3 scripts/sync_from_provisioning_agent.py --source-root ../provisioning-agent
python3 scripts/sync_from_provisioning_agent.py --source-root ../provisioning-agent --check --validate-compiler
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_repository.py
python3 -B -m unittest discover -s skills/author-flowglad-skill/tests -v
```

The public CI validates skill metadata, current exported OWS authoring shapes, source-lock
integrity, the OWS-native starter package, and the package-payload helper. The cross-repository
`--check --validate-compiler` additionally proves that generated references match an exact
provisioning-agent commit and that every bundled OWS document passes that checkout's compiler.
