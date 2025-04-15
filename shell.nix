{ pkgs ? import <nixpkgs> { } }:
pkgs.mkShell {
  nativeBuildInputs = with pkgs; [
    (pkgs.python3.withPackages (pyPkgs: [ pyPkgs.requests pyPkgs.pandas ]))
    pkgs.nodejs_22

  ];
}
