{ pkgs ? import <nixpkgs> { } }:
pkgs.mkShell {
  nativeBuildInputs = with pkgs; [
    (python3.withPackages (pyPkgs: [ pyPkgs.requests pyPkgs.pandas ]))
    nodejs_23

  ];
}
