
import os
import subprocess
import hashlib


def gen_hashes(root: str) -> dict[str, str]:
    res = {}
    for rootdir, dirs, files in os.walk(root):
        for f in files:
            full_path = os.path.join(rootdir, f)
            with open(full_path, 'rb') as f:
                h = hashlib.sha256(f.read()).hexdigest()
            if full_path in res:
                raise Exception(
                    f"Tried to insert path {full_path} that already exists")
            res[full_path] = h
        for d in dirs:
            # This may not be necessary, but hypothetically a package could create an empty directory
            full_path = os.path.join(rootdir, d)

            if full_path in res:
                raise Exception(
                    f"Tried to insert path {full_path} that already exists")
            res[full_path] = None
    return res


def checkout(url: str, workdir, commit: str = None):

    subprocess.run(["git", "clone", url, "build"], check=True, cwd=workdir)
    if not (commit is None):
        subprocess.run(["git", "checkout", commit], check=True,
                       cwd=os.path.join(workdir, "build"))


def build_in_workdir(workdir):
    builddir = os.path.join(workdir, "build")
    install_log = subprocess.run(
        ["npm", "install"], check=True, cwd=builddir, capture_output=True)
    build_log = subprocess.run(
        ["npm", "run", "build"], check=True, cwd=builddir)

    output_dir = os.path.join(builddir, "dist")
    hashes = gen_hashes(output_dir)
    return {
        "install_log": install_log,
        "build_log": build_log,
        "hashes": hashes
    }


def build(url: str, commit: str = None,rmwork=True):
    tmpdir = subprocess.run(["mktemp", "-d"], capture_output=True, check=True).stdout.decode().split("\n")[0 ]
    print(tmpdir)
    checkout(url,tmpdir,commit)
    res = build_in_workdir(tmpdir)
    if rmwork:
        subprocess.run(["rm","-rf",tmpdir],check=True)
    return res



if __name__ == "__main__":
    # print(gen_hashes("."))

    d = build("https://github.com/lodash/lodash")
    for elem in d:
        print(elem, d[elem])
