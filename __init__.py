"""A simple pre-commit hook to check files for write permission """

from bzrlib import (
    branch,
    errors,
    help_topics,
    lazy_import,
    )

lazy_import.lazy_import(globals(), """
    import os
    from bzrlib import (
        globbing,
        osutils,
        trace,
        urlutils,
        )
    """)

__version__ = '0.1.0'
version_info = 0,1,0


class CheckPermissionError(errors.BzrError):

    _fmt = "%(qty)s %(files)s with insufficient permissions. Commit aborted."

    def __init__(self, qty):
        self.qty = qty
        self.files = 'file'
        if qty > 1:
            self.files += 's'


def parse_config_file(fobj):
    patterns = []
    for line in fobj.read().decode('utf8').split('\n'):
        line = line.rstrip('\r\n')
        if not line or line.startswith('#'):
            continue
        patterns.append(globbing.normalize_pattern(line))
    return patterns

def pre_commit_check_permission(local, master, old_revno, old_revid, future_revno, future_revid, tree_delta, future_tree):

    if local:
        br = local
    else:
        br = master
    base = urlutils.local_path_from_url(br.base)
    config = os.path.join(base, '.bzrReadOnly')
    if not osutils.isfile(config):
        print ("fyi: check permission plugin can't file config file:", config)
        return

    f = file(config, 'r')
    try:
        patterns = parse_config_file(f)
    finally:
        f.close()

    globster = globbing.Globster(patterns)

    result = set([])

    for path, file_id, kind in tree_delta.added:
        if (globster.match(path)):
          print("Added", path)
          result.add(path)

    for path, file_id, kind, text_modified, meta_modified in tree_delta.modified:
        if not text_modified:
            continue
        if (globster.match(path)):
          print("Modified", path)
          result.add(path)

    for (oldpath, newpath, file_id, kind, text_modified, meta_modified) in tree_delta.renamed:
        if (globster.match(oldpath) or globster.match(newpath)):
          print("Renamed ", oldpath, "->", newpath)
          result.add(oldpath)

    if result:
        # report and abort commit
        raise CheckPermissionError(len(result))


def install_hook():
    install_named_hook = getattr(branch.Branch.hooks, 'install_named_hook', None)
    if install_named_hook:
        install_named_hook('pre_commit', pre_commit_check_permission, 'Check Permission hook')
    else:
        branch.Branch.hooks.install_hook('pre_commit', pre_commit_check_permission)
        branch.Branch.hooks.name_hook(pre_commit_check_permission, 'Check Permission hook')

install_hook()
