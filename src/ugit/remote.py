import os

from . import base, data

REMOTE_REFS_BASE = "refs/heads/"
LOCAL_REFS_BASE = "refs/remote/"


def fetch(remote_path: str) -> None:
    # Get refs from server
    refs = _get_remote_refs(remote_path, REMOTE_REFS_BASE)

    # Fetch missing objects by iterating and fetching on demand
    for oid in base.iter_objects_in_commits(refs.values()):
        data.fetch_object_if_missing(oid, remote_path)

    # Update local refs to match server
    for remote_name, value in refs.items():
        refname = os.path.relpath(remote_name, REMOTE_REFS_BASE)
        data.update_ref(f"{LOCAL_REFS_BASE}/{refname}", data.RefValue(symbolic=False, value=value))
    

def push(remote_path: str, refname: str) -> None:
    # Get refs data
    local_ref = data.get_ref(refname).value
    assert local_ref

    objects_to_push = base.iter_objects_in_commits({local_ref})

    # Push all objects
    for oid in objects_to_push:
        data.push_object(oid, remote_path)

    # Update server ref to our value
    with data.change_git_dir(remote_path):
        data.update_ref(refname, data.RefValue(symbolic=False, value=local_ref))


def _get_remote_refs(remote_path: str, prefix: str = "") -> None:
    with data.change_git_dir(remote_path):
        return {refname: ref.value for refname, ref in data.iter_refs(prefix)}