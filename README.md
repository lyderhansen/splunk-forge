# FAKE_DATA

> An A-to-Z Claude Code plugin for generating synthetic Splunk data.

FAKE_DATA helps you build a fictional world (organization, locations, users, servers) and then research, scaffold, and run Python generators that produce realistic log events for Splunk ingestion. It is designed to be used in any empty repository, by anyone, with no prior Splunk-demo tooling.

## Status

**Pre-alpha.** Plugin scaffold only. Nothing is wired up yet. See `docs/superpowers/specs/` and `docs/superpowers/plans/` for the design in progress.

## Lineage

FAKE_DATA is a standalone reimplementation of the skills and framework originally built inside the [FAKE T-Shirt Company](https://github.com/lyderhansen/The-Fake-T-Shirt-Company) Splunk TA. The existing FAKE T-Shirt project is the first intended *user* of this plugin — not its parent.

## License

MIT
