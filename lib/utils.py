
import os
import subprocess
import hashlib
import json


def decode_or_none(output):
    if output:
        return output.decode()
    return None


def get_shellpath() -> str:
    shelldir = os.path.dirname(__file__)
    shellpath = os.path.join(shelldir, "wrapped-shell.sh")
    return shellpath


def copy_dict(d: dict) -> dict:
    # not exact copy but environment variables are just strings anyway
    return json.loads(json.dumps(d))


def gen_hashes(root: str) -> dict[str, str]:
    res = {}
    for rootdir, dirs, files in os.walk(root):

        for f in files:

            full_path = os.path.join(rootdir, f)
            with open(full_path, 'rb') as tmpf:
                h = hashlib.sha256(tmpf.read()).hexdigest()
            if full_path in res:
                raise Exception(
                    f"Tried to insert path {full_path} that already exists")
            relative_path = os.path.relpath(full_path, root)
            res[relative_path] = h
        for d in dirs:
            # This may not be necessary, but hypothetically a package could create an empty directory
            full_path = os.path.join(rootdir, d)

            if full_path in res:
                raise Exception(
                    f"Tried to insert path {full_path} that already exists")
            relative_path = os.path.relpath(full_path, root)
            res[relative_path] = None
    return res


def compare_dirs(d1: dict[str, str], d2: dict[str, str]) -> dict[str, list[str]]:
    removed = []  # only in d2
    equal = []  # same in d1 and d2
    changed = []  # exists in both d1 and in d2 but has different content
    added = []  # only in d2
    for k1 in d1.keys():
        if k1 in d2.keys():
            if d1[k1] == d2[k1]:
                equal.append(k1)
            else:
                changed.append(k1)
        else:
            removed.append(k1)
    for k2 in d2.keys():
        if not k2 in d1.keys():
            added.append(k2)
    return {
        "removed": removed,
        "equal": equal,
        "changed": changed,
        "added": added,
    }


def startswith_any(s: str, arr: list[str]):
    for si in arr:
        if s.startswith(si):
            return True
    return False


def display_diff(diff: dict[str, list[str]], ignore=None):
    if ignore is None:
        ignore = []
    print("Removed:")
    for r in diff["removed"]:
        if not startswith_any(r, ignore):
            print(f"\t{r}")

    print("Changed:")
    for c in diff["changed"]:
        if not startswith_any(c, ignore):
            print(f"\t{c}")

    print("Added:")
    for a in diff["added"]:
        if not startswith_any(a, ignore):
            print(f"\t{a}")


def single_hash(hashes: dict) -> str:
    l = []
    for k in hashes:
        s = hashlib.sha256(k.encode()).hexdigest()
        if hashes[k]:
            s += f"-{hashes[k]}"

        l.append(s)
    l = sorted(l)
    s = ''.join([si+"--" for si in l])
    h = hashlib.sha256(s.encode()).hexdigest()
    return h


def checkout(url: str, workdir: str, commit: str = None):

    subprocess.run(["git", "clone", url, "build"], check=True, cwd=workdir)
    if not (commit is None):
        subprocess.run(["git", "checkout", commit], check=True,
                       cwd=os.path.join(workdir, "build"))


def build_in_workdir(workdir: str, log_shell: bool = False, verbose: bool = True) -> dict:
    builddir = os.path.join(workdir, "build")
    if log_shell:
        shell = get_shellpath()
        shell_args = [f"--script-shell={shell}"]
    else:
        shell_args = []

    env = {}
    for k in os.environ.keys():
        env[k] = copy_dict(os.environ[k])
    if verbose:
        # https://stackoverflow.com/questions/36276011/node-command-line-verbose-output
        env["NODE_DEBUG"] = "cluster,net,http,fs,tls,module,timers"

    install_cmd = "install-clean"
    has_lockfile = os.path.isfile(os.path.join(builddir, "package-lock.json"))
    if not has_lockfile:
        # TODO: perhaps the package should be skipped altogether in this case?
        install_cmd = "install"
    preinstall_hashes = gen_hashes(builddir)
    install_log = subprocess.run(
        ["npm", install_cmd]+shell_args, check=False, cwd=builddir, capture_output=True, env=env)
    if install_log.returncode != 0:
        print(install_log.stdout.decode())
        print(install_log.stderr.decode())
        raise subprocess.CalledProcessError(
            returncode=install_log.returncode, cmd=install_log.args)

    script_out = subprocess.run(
        ["npm", "run"] + shell_args + [], check=False, capture_output=True, cwd=builddir)
    if script_out.returncode != 0:
        print(script_out.stdout.decode())
        print(script_out.stderr.decode())
        raise subprocess.CalledProcessError(
            returncode=script_out.returncode, cmd=script_out.args)

    scripts = []
    for elem in script_out.stdout.decode().split("\n"):
        if elem.startswith("available via"):
            continue
        print(f"elem[:5]={elem[:5]}")
        if elem[0:2] == ' '*2 and elem[3] != ' ':
            tmp = elem[2:].split(' ')
            script = tmp[0]
            scripts.append(script)

    if "build" in scripts:
        build_log = subprocess.run(
            ["npm", "run"] + shell_args + ["build"], check=True, capture_output=True, cwd=builddir, env=env)

        if build_log.returncode != 0:
            print(build_log.stdout.decode())
            print(build_log.stderr.decode())
            raise subprocess.CalledProcessError(
                returncode=build_log.returncode, cmd=build_log.args)
        prebuild_hashes = gen_hashes(workdir)

    else:
        print("no build script found, skipping")
        build_log = None
        prebuild_hashes = None

    output_dir = os.path.join(builddir, "dist")
    post_hashes = gen_hashes(builddir)
    hashes = gen_hashes(output_dir)
    hash = single_hash(hashes)
    return {
        "builddir": builddir,
        "scripts": scripts,
        "has_lockfile": has_lockfile,
        "install_log": install_log,
        "build_log": build_log,
        "hashes": hashes,
        "hash": hash,
        "stage_hashes": {
            "preinstall_hashes": preinstall_hashes,
            "prebuild_hashes": prebuild_hashes,
            "post_hashes": post_hashes,
        }
    }


def build(url: str, commit: str = None, rmwork=True, log_shell=False, verbose: bool = True) -> dict:
    tmpdir = subprocess.run(
        ["mktemp", "-d"], capture_output=True, check=True).stdout.decode().split("\n")[0]
    print(tmpdir)
    checkout(url, tmpdir, commit)
    res = build_in_workdir(tmpdir, log_shell=log_shell, verbose=verbose)
    if rmwork:
        subprocess.run(["rm", "-rf", tmpdir], check=True)
    return res


if __name__ == "__main__":
    d = copy_dict({"hello": 1})
    print(d)
