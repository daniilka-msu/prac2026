import os
import sys
import zlib

def list_branches(repo_path):
    heads_path = os.path.join(repo_path, ".git", "refs", "heads")
    if not os.path.isdir(heads_path):
        print("Не найден репозиторий Git:", repo_path)
        return
    for name in os.listdir(heads_path):
        print(name)

def read_git_object(repo_path, sha):
    obj_path = os.path.join(repo_path, ".git", "objects", sha[:2], sha[2:])
    if not os.path.exists(obj_path):
        print(f"Объект {sha} не найден")
        return None, None
    with open(obj_path, "rb") as f:
        compressed = f.read()
    raw = zlib.decompress(compressed)
    header, _, body = raw.partition(b'\x00')
    kind, _ = header.split()
    return kind.decode(), body

def parse_tree(body):
    entries = []
    pos = 0
    while pos < len(body):
        mode_end = body.find(b' ', pos)
        if mode_end == -1:
            break
        mode = body[pos:mode_end].decode()
        pos = mode_end + 1
        name_end = body.find(b'\x00', pos)
        if name_end == -1:
            break
        name = body[pos:name_end].decode('utf-8', errors='replace')
        pos = name_end + 1
        if pos + 20 > len(body):
            break
        sha = body[pos:pos+20].hex()
        pos += 20
        obj_type = "blob" if mode.startswith("100") else "tree"
        entries.append((obj_type, sha, name))
    return entries

def show_commit_history(repo_path, commit_sha):
    kind, body = read_git_object(repo_path, commit_sha)
    if kind != "commit":
        return
    commit_lines = body.decode('utf-8', errors='replace').split('\n')
    tree_line = next((line for line in commit_lines if line.startswith('tree ')), None)
    if not tree_line:
        return
    tree_sha = tree_line.split()[1]
    print(f"TREE for commit {commit_sha}")
    kind, tree_body = read_git_object(repo_path, tree_sha)
    if kind != "tree":
        return
    entries = parse_tree(tree_body)
    for obj_type, sha, name in entries:
        print(f"{obj_type} {sha}    {name}")
    parent_line = next((line for line in commit_lines if line.startswith('parent ')), None)
    if parent_line:
        print()
        parent_sha = parent_line.split()[1]
        show_commit_history(repo_path, parent_sha)

def show_last_commit(repo_path, branch):
    ref_path = os.path.join(repo_path, ".git", "refs", "heads", branch)
    if not os.path.exists(ref_path):
        print(f"Ветка '{branch}' не найдена")
        return
    with open(ref_path, "r") as f:
        commit_sha = f.read().strip()
    kind, body = read_git_object(repo_path, commit_sha)
    if kind != "commit":
        return
    print(body.decode('utf-8', errors='replace').strip())
    tree_line = next((line for line in body.decode('utf-8', errors='replace').split('\n') if line.startswith('tree ')), None)
    if not tree_line:
        return
    tree_sha = tree_line.split()[1]
    kind, tree_body = read_git_object(repo_path, tree_sha)
    if kind != "tree":
        return
    entries = parse_tree(tree_body)
    for obj_type, sha, name in entries:
        print("\n" f"{obj_type} {sha}    {name}", end = '\n\n')
    show_commit_history(repo_path, commit_sha)

if len(sys.argv) < 2:
    print("Нет пути к репозиторию")
elif len(sys.argv) == 2:
    repo_path = sys.argv[1]
    list_branches(repo_path)
else:
    repo_path = sys.argv[1]
    branch = sys.argv[2]
    show_last_commit(repo_path, branch)