# c0nkcr33t's Dalamud plugins

Add this URL under Dalamud Settings → Experimental → Custom Plugin Repositories:

```text
https://raw.githubusercontent.com/c0nkcr33t/dalamud-plugins/main/pluginmaster.json
```

Save, then install plugins through `/xlplugins`. This feed replaces the individual
plugin feed URLs; remove those if you use this one to avoid duplicate entries.
Disable dev copies before installing the corresponding normal plugin.

## Automatic updates

The **Refresh plugin catalog** Action checks the repositories in `sources.json`
every 30 minutes. It also has a **Run workflow** button for immediate refresh.
GitHub schedules can be delayed; inactive public repositories may have their
schedules disabled after 60 days. Re-enable the workflow if that happens.

The updater reads each latest stable release's `latest.zip`, validates its DLL
and manifest, and generates the catalog from that manifest. No draft or
prerelease builds are advertised. A plugin with no releases is omitted until
one exists. Failed downloads or invalid packages fail the job without replacing
the catalog. Check the Actions tab if a new release does not appear.

No personal access token is required: the workflow's built-in token writes only
to this repository, while releases are downloaded publicly. Repository rules
must allow the workflow to push to main.

## Release a plugin

From either plugin repository, with your code committed on `main`:

```bash
./scripts/release.sh 0.4.0
```

Choose a new version for that plugin. The helper updates its project version,
commits it, and atomically pushes main and the version tag. Its release Action
builds, tests, uploads a draft release, and publishes it only after the ZIP is
attached. This catalog then discovers it automatically.

To publish the first automated Chocobo Radio release at its current version:

```bash
./scripts/release.sh 0.3.0
```

Already published tags cannot be reused. Build failures are visible in each
plugin's Actions tab; fix code with a new version, or rerun the failed workflow
for a transient network failure.

## Add another plugin

Add its public GitHub repository and exact Dalamud InternalName to `sources.json`.
It must publish a `latest.zip` with the same-named DLL and JSON manifest at the
archive root. Commit and push; the catalog refreshes automatically.

Local checks: `python3 -m unittest discover -s tests`.
Local refresh: `python3 scripts/update_catalog.py` (requires internet).
