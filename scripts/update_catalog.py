#!/usr/bin/env python3
"""Build the catalog from actual release ZIP manifests; never advertise missing ZIPs."""
import datetime
import io
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def fetch(url, api=False):
    headers = {'User-Agent': 'c0nkcr33t-dalamud-catalog'}
    # Never send API credentials to release asset hosts or redirects.
    if api and os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
        data = response.read(100 * 1024 * 1024 + 1)
    if len(data) > 100 * 1024 * 1024:
        raise ValueError('Release response exceeds 100 MiB')
    return data


def entry_from_zip(source, release, asset, payload):
    name = source['internal_name']
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        info = archive.getinfo(name + '.json')
        if info.file_size > 1024 * 1024:
            raise ValueError('Manifest too large')
        manifest = json.loads(archive.read(info))
        if name + '.dll' not in archive.namelist():
            raise ValueError('Plugin DLL missing')
    if manifest.get('InternalName') != name:
        raise ValueError('Unexpected InternalName')
    version = manifest['AssemblyVersion'].split('.')
    if len(version) != 4 or not all(x.isdigit() for x in version):
        raise ValueError('Expected a four-part assembly version')
    if not isinstance(manifest.get('DalamudApiLevel'), int):
        raise ValueError('Missing API level')
    fields = ('Author', 'Name', 'InternalName', 'AssemblyVersion', 'Description',
              'ApplicableVersion', 'DalamudApiLevel', 'MinimumDalamudVersion',
              'RepoUrl', 'IconUrl', 'ImageUrls', 'Punchline', 'Tags', 'Changelog')
    entry = {k: manifest[k] for k in fields if k in manifest}
    entry.update(DownloadLinkInstall=asset['browser_download_url'],
                 DownloadLinkUpdate=asset['browser_download_url'],
                 LastUpdate=str(int(datetime.datetime.fromisoformat(
                     release['published_at'].replace('Z', '+00:00')).timestamp())),
                 IsHide=False, IsTestingExclusive=False)
    return entry


def main():
    entries = []
    for source in json.loads((ROOT / 'sources.json').read_text()):
        url = 'https://api.github.com/repos/' + source['repository'] + '/releases/latest'
        try:
            release = json.loads(fetch(url, api=True))
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            # Distinguish an empty release list from a typo/deleted repository.
            fetch('https://api.github.com/repos/' + source['repository'], api=True)
            print('No published release yet:', source['repository'])
            continue
        if release['draft'] or release['prerelease']:
            raise ValueError('Expected a stable published release')
        assets = [a for a in release['assets'] if a['name'] == 'latest.zip' and a['state'] == 'uploaded']
        if len(assets) != 1:
            raise ValueError('Release must contain exactly one uploaded latest.zip: ' + source['repository'])
        asset = assets[0]
        entries.append(entry_from_zip(source, release, asset, fetch(asset['browser_download_url'])))
    # Only replace the old catalog when every source has been processed successfully.
    target = ROOT / 'pluginmaster.json'
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(target)
    print('Validated catalog entries:', len(entries))


if __name__ == '__main__':
    main()
