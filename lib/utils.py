
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
    cmd1 = ["git", "clone",]
    if commit is None:
        cmd1.append("--depth=1")
        # "--depth=1",
    cmd1 += [
        url,
        "build"]
    cmd1_s = ' '.join(cmd1)
    print(f"running \"{cmd1_s}\"")
    try:
        subprocess.run(cmd1, check=True, cwd=workdir)
    except Exception as e:
        # TODO
        raise e
    if not (commit is None):
        cmd2 = ["git", "checkout", commit]
        cmd2_s = ' '.join(cmd2)
        print(f"running {cmd2}")
        try:
            subprocess.run(cmd2, check=True,
                           cwd=os.path.join(workdir, "build"))
        except Exception as e:
            # TODO
            raise e


def fetch_github_archive(url, workdir, commit):
    # zb https://github.com/debug-js/debug/archive/33330fa8616b9b33f29f7674747be77266878ba6.zip
    url = f"{url}/archive/{commit}.tar.gz"


def run_build_command_with_nix(nix_shell, command, builddir, env=None, verbose=False):
    # command = command.split()
    # print("env", env)
    print("(nix) running command:", command)
    print("(nix) in builddir:", builddir)

    args = ["nix-shell", nix_shell,
            # "--keep-failed",
            "-vvvvv",
            "--pure", ]
    if verbose:
        args += []

    capture_output = True
    out = subprocess.run(
        args +
        ["--run",  f"{command}"], check=False, cwd=builddir, capture_output=capture_output)
    if out.returncode != 0:
        print("WARNING, nix-shell failed",
              out.stdout.decode(), out.stderr.decode())
    return out


def run_build_command_with_podman(container_id, command, builddir, env=None, verbose=False):
    # command = command.split()
    # print("env", env)
    print("command", command)
    print("builddir", builddir)

    args = ["podman", "run",
            "--rm", "-it",
            "--network", "host",
            container_id,
            "-v", f"{builddir}:{builddir}"
            ]
    if verbose:
        args += []
    out = subprocess.run(
        args +
        [f"{command}"], check=False, cwd=builddir, capture_output=True)
    return out


def build_in_workdir(workdir: str, log_shell: bool = False, verbose: bool = True, nix_shell_path: str = None) -> dict:
    if nix_shell_path is None:
        nix_shell_path = os.path.join(os.path.abspath("."), "shell1.nix")
    builddir = os.path.join(workdir, "build")
    if log_shell:
        shell = get_shellpath()
        shell_args = [f"--script-shell={shell}"]
    else:
        shell_args = []

    shell_args.append("--verbose")

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

    git_log_out_bin = subprocess.run(
        ["git", "log", "-p"], capture_output=True, check=True, cwd=builddir).stdout
    try:
        git_log_out = git_log_out_bin.decode(errors="ignore")
    except Exception as e:
        print("could not decode", git_log_out_bin)
        raise e
    commit = git_log_out.split()[1]

    # install_log = subprocess.run(
    #    ["npm", install_cmd]+shell_args, check=False, cwd=builddir, capture_output=True, env=env)
    nix_install_cmd = f"npm {install_cmd} {' '.join(shell_args)}"
    install_log = run_build_command_with_nix(
        nix_shell=nix_shell_path, command=nix_install_cmd, builddir=builddir, env=env)

    if install_log.returncode != 0:
        print(install_log.stdout.decode())
        print(install_log.stderr.decode())
        raise subprocess.CalledProcessError(
            returncode=install_log.returncode, cmd=install_log.args)

    install_log_out = install_log.stdout.decode()
    install_log_err = install_log.stderr.decode()

    # script_out = subprocess.run(
    #     ["npm", "run"] + shell_args + [], check=False, capture_output=True, cwd=builddir, env=env)
    nix_npm_run_command = f"npm run {' '.join(shell_args)}"
    script_out = run_build_command_with_nix(
        nix_shell=nix_shell_path, command=nix_npm_run_command, builddir=builddir, env=env)

    if script_out.returncode != 0:
        print(script_out.stdout.decode())
        print(script_out.stderr.decode())
        raise subprocess.CalledProcessError(
            returncode=script_out.returncode, cmd=script_out.args)

    scripts = []
    for elem in script_out.stdout.decode().split("\n"):
        if elem.startswith("available via"):
            continue
        # print(f"elem[:5]={elem[:5]}")
        if elem[0:2] == ' '*2 and elem[3] != ' ':
            tmp = elem[2:].split(' ')
            script = tmp[0]
            scripts.append(script)

    if "build" in scripts:
        # build_log = subprocess.run(
        #    ["npm", "run"] + shell_args + ["build"], check=True, capture_output=True, cwd=builddir, env=env)
        nix_build_command = f"npm run {' '.join(shell_args)}"
        build_log = run_build_command_with_nix(
            nix_shell=nix_shell_path, command=nix_build_command, builddir=builddir, env=env)

        if build_log.returncode != 0:
            print(build_log.stdout.decode())
            print(build_log.stderr.decode())
            raise subprocess.CalledProcessError(
                returncode=build_log.returncode, cmd=build_log.args)
        prebuild_hashes = gen_hashes(workdir)
        build_log_out = build_log.stdout.decode()
        build_log_err = build_log.stderr.decode()

    else:
        print("no build script found, skipping")
        build_log = None
        build_log_out = None
        build_log_err = None
        prebuild_hashes = None

    output_dir = os.path.join(builddir, "dist")
    post_hashes = gen_hashes(builddir)
    hashes = gen_hashes(output_dir)
    hash = single_hash(hashes)

    dev_deps = None
    deps = None
    pkg_json = f"{builddir}/package.json"

    has_pkg_json = os.path.isfile(pkg_json)
    if has_pkg_json:
        with open(pkg_json, encoding="utf-8") as f:
            pkg_json_data = json.load(f)
            if "devDependencies" in pkg_json_data.keys():
                dev_deps = pkg_json_data["devDependencies"]

            if "dependencies" in pkg_json_data.keys():
                deps = pkg_json_data["dependencies"]
    else:
        pkg_json_data = None

    return {
        "builddir": builddir,
        "commit": commit,
        "scripts": scripts,
        "has_lockfile": has_lockfile,
        "has_pkg_json": has_pkg_json,
        # "dependencies": deps,
        # "dev_dependencies": dev_deps,
        "package_json": pkg_json_data,
        "install_log": install_log,
        "install_log_out": install_log_out,
        "install_log_err": install_log_err,
        "build_log": build_log,
        "build_log_out": build_log_out,
        "build_log_err": build_log_err,
        "hashes": hashes,
        "hash": hash,
        "stage_hashes": {
            "preinstall_hashes": preinstall_hashes,
            "prebuild_hashes": prebuild_hashes,
            "post_hashes": post_hashes,
        }
    }


def mktemp() -> str:
    tmpdir = subprocess.run(
        ["mktemp", "-d"
         # "-p", "/tmp"
         ], capture_output=True, check=True).stdout.decode().split("\n")[0]
    return tmpdir


def build(url: str, commit: str = None, rmwork=True, log_shell=False, verbose: bool = True, tmpdir=None, nix_shell_path=None, ignore_completed_process=False) -> dict:
    if tmpdir is None:
        tmpdir = mktemp()
    checkout(url, tmpdir, commit)
    res = build_in_workdir(tmpdir, log_shell=log_shell,
                           verbose=verbose, nix_shell_path=nix_shell_path)
    if rmwork:
        print(f"Removig {tmpdir}")
        subprocess.run(["rm", "-rf", tmpdir], check=True)
        if os.path.exists(tmpdir):
            raise Exception(f"failed to remove {tmpdir}")
    res["tmpdir"] = tmpdir
    if ignore_completed_process:
        res["build_log"] = None
        res["install_log"] = None
    return res


def diffoscope_compare(builddir1: str, builddir2: str) -> dict:
    cmd = ["diffoscope", builddir1, builddir2,
           "--exclude=node_modules", "--exclude=.git",
           # seems to detailed, TODO: look up if others use metadata
           "--exclude-directory-metadata=yes",
           "--json", "-"]
    capture_output = True
    check = False  # seems to return 0 only if same
    try:

        out = subprocess.run(cmd, check=check, capture_output=capture_output)

    except subprocess.CalledProcessError as e:
        print(f"failed to run command {cmd}")
        try:
            print("stdout", out.stdout.decode())
            print("stderr", out.stderr.decode())
        except:
            pass
        print(e)
        raise e
        raise Exception
    res_str = out.stdout.decode()
    if res_str is None:
        return {}
    elif res_str == "":
        return {}
    try:
        data = json.loads(res_str)
    except json.decoder.JSONDecodeError as e:
        print(f"failed to load \"{res_str}\"")
        raise e
        raise Exception
    return data


if __name__ == "__main__":
    d = copy_dict({"hello": 1})
    print(d)
