from collections import defaultdict


def compare_trees(*trees: dict):
    entries = defaultdict(lambda: [None] * len(trees))
    for i, tree in enumerate(trees):
        for path, oid in tree.items():
            entries[path][i] = oid
    
    for path, oids in entries.items():
        yield (path, *oids)


def diff_tries(t_from: dict, t_to: dict) -> str:
    output = ""
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
            output += f"changed: {path}\n"
    return output
