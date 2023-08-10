from collections import defaultdict
import subprocess
from tempfile import NamedTemporaryFile as Temp

from . import data


def compare_trees(*trees: dict):
    entries = defaultdict(lambda: [None] * len(trees))
    for i, tree in enumerate(trees):
        for path, oid in tree.items():
            entries[path][i] = oid
    
    for path, oids in entries.items():
        yield (path, *oids)


def iter_changed_files(t_from: dict, t_to: dict):
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
            action = ("new file" if not o_from else
                      "deleted" if not o_to else
                      "modified")
            yield path, action


def diff_trees(t_from: dict, t_to: dict) -> str:
    output = b""
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
            output += diff_blobs(o_from, o_to, path)
    return output


def diff_blobs(o_from, o_to, path="blob") -> str:
    with Temp() as f_form, Temp() as f_to:
        for oid, f in ((o_from, f_form), (o_to, f_to)):
            if oid:
                f.write(data.get_object(oid))
                f.flush()

        with subprocess.Popen(
            [
                "diff",
                "--unified",
                "--show-c-function",
                "--label",
                f"a/{path}",
                f_form.name,
                "--label",
                f"b/{path}",
                f_to.name,
            ],
            stdout=subprocess.PIPE
        ) as proc:
            output, _ = proc.communicate()
        
        return output
