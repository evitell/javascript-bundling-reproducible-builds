import json
import sys

def extract_diff(filepath_in,filepath_out):
    with open(filepath1) as f:
        czcli = json.load(f)
    
    print(type(czcli))
    print(czcli.keys())
    diff = czcli["diff"]
    print(type(diff))
    print(diff.keys())
    with open(filepath_out,"w") as f:
        json.dump(diff,f)

def diff_recurse(d,joined_path=""):
    res = []
    if d["unified_diff"]:
        res_d = {"joined_path" :joined_path }
        
        for k in ("source1","source2","unified_diff" ):
            res_d [k] = d [k]
        # res_d["joined_path"] = joined_path + "--" + res_d["source1"]
        res.append(res_d)
    if "details" in d.keys():
        for dd in d["details"]:
            res += diff_recurse(dd,joined_path=joined_path + "--" + dd["source1"] )
    return res

def diff(filepath_in):
    with open(filepath_in) as f:
        data = json.load(f)
    
    print(data.keys())

    res = diff_recurse(data)
    for d in res:
        for k in d.keys():
            print(f"{k}: {d[k]}")
        print()

def main():
    # example for the cz-cli gh repo, which shows interesting result
    extract_diff("data/github_projects/298_cz-cli.json","298.diff.json")
    diff("298.diff.json")

if __name__ == "__main__":
    main()