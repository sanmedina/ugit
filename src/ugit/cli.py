import argparse
import os
import subprocess
import sys
import textwrap

from . import base, data, diff, remote


def main() -> None:
    with data.change_git_dir("."):
        args = parse_args()
        args.func(args)


def parse_args() -> None:
    parser = argparse.ArgumentParser()

    commands = parser.add_subparsers(dest="command")
    commands.required = True

    oid = base.get_oid

    init_parser = commands.add_parser("init")
    init_parser.set_defaults(func=init)

    hash_object_parser = commands.add_parser("hash-object")
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument("file")

    cat_file_parser = commands.add_parser("cat-file")
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument("object", type=oid)

    write_tree_parser = commands.add_parser("write-tree")
    write_tree_parser.set_defaults(func=write_tree)

    read_tree_parser = commands.add_parser("read-tree")
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument("tree", type=oid)

    commit_parser = commands.add_parser("commit")
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument("-m", "--message", required=True)

    log_parser = commands.add_parser("log")
    log_parser.set_defaults(func=log)
    log_parser.add_argument("oid", default="@", type=oid, nargs="?")

    show_parser = commands.add_parser("show")
    show_parser.set_defaults(func=show)
    show_parser.add_argument("oid", default="@", type=oid, nargs="?")

    diff_parser = commands.add_parser("diff")
    diff_parser.set_defaults(func=_diff)
    diff_parser.add_argument("--cached", action="store_true")
    diff_parser.add_argument("commit", nargs="?")

    checkout_parser = commands.add_parser("checkout")    
    checkout_parser.set_defaults(func=checkout)
    checkout_parser.add_argument("commit")

    tag_parser = commands.add_parser("tag")
    tag_parser.set_defaults(func=tag)
    tag_parser.add_argument("name")
    tag_parser.add_argument("oid", default="@", type=oid, nargs="?")

    k_parser = commands.add_parser("k")
    k_parser.set_defaults(func=k)
    k_parser.add_argument("-o", "--output", default="Tx11")

    branch_parser = commands.add_parser("branch")
    branch_parser.set_defaults(func=branch)
    branch_parser.add_argument("name", nargs="?")
    branch_parser.add_argument("start_point", default="@", type=oid, nargs="?")

    status_parser = commands.add_parser("status")
    status_parser.set_defaults(func=status)

    reset_parser = commands.add_parser("reset")
    reset_parser.set_defaults(func=reset)
    reset_parser.add_argument("commit", type=oid)

    merge_parser = commands.add_parser("merge")
    merge_parser.set_defaults(func=merge)
    merge_parser.add_argument("commit", type=oid)

    merge_base_parser = commands.add_parser("merge-base")
    merge_base_parser.set_defaults(func=merge_base)
    merge_base_parser.add_argument("commit1", type=oid)
    merge_base_parser.add_argument("commit2", type=oid)

    fetch_parser = commands.add_parser("fetch")
    fetch_parser.set_defaults(func=fetch)
    fetch_parser.add_argument("remote")

    push_parser = commands.add_parser("push")
    push_parser.set_defaults(func=push)
    push_parser.add_argument("remote")
    push_parser.add_argument("branch")

    add_parser = commands.add_parser("add")
    add_parser.set_defaults(func=add)
    add_parser.add_argument("files", nargs="+")

    return parser.parse_args()


def init(args: argparse.Namespace) -> None:
    base.init()
    print(f"Initializated empty ugit reposiroty in {os.getcwd()}/{data.GIT_DIR}")


def hash_object(args: argparse.Namespace) -> None:
    with open(args.file, "rb") as f:
        print(data.hash_object(f.read()))


def cat_file(args: argparse.Namespace) -> None:
    sys.stdout.flush()
    sys.stdout.buffer.write(data.get_object(args.object, exptected=None))


def write_tree(args: argparse.Namespace) -> None:
    print(base.write_tree())


def read_tree(args: argparse.Namespace) -> None:
    base.read_tree(args.tree)


def commit(args: argparse.Namespace) -> None:
    print(base.commit(args.message))


def _print_commit(oid: str, commit: str, refs: str = None) -> None:
    refs_str = f' ({", ".join (refs)})' if refs else ''
    print (f'commit {oid}{refs_str}\n')
    print (textwrap.indent (commit.message, '    '))
    print ('')


def log(args: argparse.Namespace) -> None:
    refs = {}
    for refname, ref in data.iter_refs():
        refs.setdefault(ref.value, []).append(refname)

    for oid in base.iter_commits_and_parents({args.oid}):
        commit = base.get_commit(oid)
        _print_commit(oid, commit, refs.get(oid))


def show(args: argparse.Namespace) -> None:
    if not args.oid:
        return
    commit = base.get_commit(args.oid)
    parent_tree = None
    if commit.parents:
        parent_tree = base.get_commit(commit.parents[0]).tree 

    _print_commit(args.oid, commit)
    result = diff.diff_trees(
        base.get_tree(parent_tree), base.get_tree(commit.tree)
    )
    sys.stdout.flush()
    sys.stdout.buffer.write(result)


def _diff(args: argparse.Namespace) -> None:
    oid = args.commit and base.get_oid(args.commit)

    if args.commit:
        # If a commit was provided explicitly, diff rom it
        tree_from = base.get_tree(oid and base.get_commit(oid).tree)

    if args.cached:
        tree_to = base.get_index_tree()
        if not args.commit:
            # If no commit was provided, diff from HEAD
            oid = base.get_commit("@")
            tree_from = base.get_tree(oid and base.get_commit(oid).tree)
    else:
        tree_to = base.get_working_tree()
        if not args.commit:
            # If no commit was provided, diff from HEAD
            tree_from = base.get_index_tree()

    result = diff.diff_trees(tree_from, tree_to)
    sys.stdout.flush()
    sys.stdout.buffer.write(result)


def checkout(args: argparse.Namespace) -> None:
    base.checkout(args.commit)


def tag(args: argparse.Namespace) -> None:
    oid = args.oid
    base.create_tag(args.name, oid)


def branch(args: argparse.Namespace) -> None:
    if args.name:
        base.create_branch(args.name, args.start_point)
        print(f"Branch {args.name} created at {args.start_point[:10]}")
    else:
        current = base.get_branch_name()
        for branch in base.iter_branch_names():
            prefix = "*" if branch == current else " "
            print(f"{prefix} {branch}")


def k(args: argparse.Namespace) -> None:
    dot = "digraph commits {\n"

    oids = set()
    for refname, ref in data.iter_refs():
        dot += f'"{refname}" [shape=note]\n'
        dot += f'"{refname}" -> "{ref.value}"\n'
        if not ref.symbolic:
            oids.add(ref.value)

    for oid in base.iter_commits_and_parents(oids):
        commit = base.get_commit(oid)
        dot += f'"{oid}" [shape=box style=filled label="{oid[:10]}"]\n'
        for parent in commit.parents:
            dot += f'"{oid}" -> "{parent}"\n'

    dot += "}"
    print(dot)

    with subprocess.Popen(["dot", f"-{args.output}", "/dev/stdin"], stdin=subprocess.PIPE) as proc:
        proc.communicate(dot.encode())


def status(args: argparse.Namespace) -> None:
    HEAD = base.get_oid("@")
    branch = base.get_branch_name()
    if branch:
        print(f"On branch {branch}")
    else:
        print(f"HEAD detached at {HEAD[:10]}")

    MERGE_HEAD = data.get_ref("MERGE_HEAD").value
    if MERGE_HEAD:
        print(f"Merging with {MERGE_HEAD[:10]}")

    print("\nChanges to be committed:\n")
    HEAD_tree = HEAD and base.get_commit(HEAD).tree
    for path, action in diff.iter_changed_files(
        base.get_tree(HEAD_tree),
        base.get_index_tree()
    ):
        print(f"{action:>12}: {path}")

    print(f"\nChanges not staged for commit:\n")
    for path, action in diff.iter_changed_files(
        base.get_index_tree(),
        base.get_working_tree()
    ):
        print(f"{action:>12}: {path}")


def reset(args: argparse.Namespace) -> None:
    base.reset(args.commit)


def merge(args: argparse.Namespace) -> None:
    base.merge(args.commit)


def merge_base(args: argparse.Namespace) -> None:
    print(base.get_merge_base(args.commit1, args.commit2))


def fetch(args: argparse.Namespace) -> None:
    remote.fetch(args.remote)


def push(args: argparse.Namespace) -> None:
    remote.push(args.remote, f"refs/heads/{args.branch}")


def add(args: argparse.Namespace) -> None:
    base.add(args.files)
