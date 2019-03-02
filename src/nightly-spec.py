#!/usr/bin/env python3
#
# nightly-spec.py: update an rpm spec file for nightly build
#

from datetime import date
import re
import subprocess
import sys


def main(filename):
    spec = Spec(filename)
    prev_release = spec['release']
    version, release = git_version_release(prev_release)
    spec['version'] = version
    spec['release'] = release + '%{?dist}'
    spec.prune_changelog(r'(?s)Aron.Griffis.*Nightly.build')
    spec.add_changelog(
        'Aron Griffis <aron@scampersand.com>',
        '- Nightly build from git master',
        release=release,  # avoid getting %{?dist}
    )
    spec.write()


def git_version_release(prev_release):
    git_tag = run('git tag').split('\n')[-1]
    git_commit = run('git rev-parse --short master')
    version = re.search(r'(?:^v|\b)(\d.*)', git_tag).group(1)
    release = str(int(re.search(r'^\d+', prev_release).group(0)) + 1)

    # https://serverfault.com/a/867567
    if '-' in version:
        version, release = version.split('-', 1)
        release = '0.' + release.replace('-', '.')

    # same format as https://github.com/pypingou/dgroc
    release = '{}.{:%Y%m%d}git{}'.format(release, date.today(), git_commit)

    return version, release


def run(cmd):
    return subprocess.check_output(cmd.split(), encoding='UTF-8').rstrip()


class Spec:
    def __init__(self, filename):
        self.filename = filename
        with open(filename, encoding='UTF-8') as f:
            self.spec = f.read()

    def patt(self, name):
        return r'(?im)^(' + re.escape(name) + r'\s*:\s*)(.*?)\s*?$'

    def __getitem__(self, key):
        match = re.search(self.patt(key), self.spec)
        if not match:
            print(self.spec)
            raise KeyError
        return match.group(2)

    def __setitem__(self, key, value):
        self.spec, n = re.subn(self.patt(key), lambda m: m.group(1) + value,
                               self.spec, 1)
        if not n:
            raise KeyError

    def add_changelog(self, name, entry, version=None, release=None):
        full_entry = '* {:%a %b %d %Y} {} - {}-{}\n{}'.format(
            date.today(),
            name,
            version or self['version'],
            release or self['release'],
            entry.rstrip())
        content, changelog = self.spec.split('%changelog\n', 1)
        self.spec = '{}%changelog\n{}\n\n{}'.format(
            content, full_entry, changelog)

    def prune_changelog(self, patt):
        content, changelog = self.spec.split('%changelog\n', 1)
        changes = changelog.split('\n\n', 1)
        if re.search(patt, changes[0]):
            changes = changes[1:]
        self.spec = '{}%changelog\n{}'.format(content, '\n\n'.join(changes))

    def write(self, filename=None):
        with open(filename or self.filename, 'w', encoding='UTF-8') as f:
            return f.write(self.spec)


if __name__ == '__main__':
    main(*sys.argv[1:])
