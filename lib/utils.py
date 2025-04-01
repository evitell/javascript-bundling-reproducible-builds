
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
            relative_path = os.path.relpath(full_path, rootdir)
            res[f] = relative_path
        for d in dirs:
            # This may not be necessary, but hypothetically a package could create an empty directory
            full_path = os.path.join(rootdir, d)

            if full_path in res:
                raise Exception(
                    f"Tried to insert path {full_path} that already exists")
            res[d] = None
    return res


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

    install_log = subprocess.run(
        ["npm", "install"]+shell_args, check=True, cwd=builddir, capture_output=True, env=env)
    build_log = subprocess.run(
        ["npm", "run"] + shell_args + ["build"], check=True, cwd=builddir, env=env)

    output_dir = os.path.join(builddir, "dist")
    hashes = gen_hashes(output_dir)
    hash = single_hash(hashes)
    return {
        "builddir": builddir,
        "install_log": install_log,
        "build_log": build_log,
        "hashes": hashes,
        "hash": hash,
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
