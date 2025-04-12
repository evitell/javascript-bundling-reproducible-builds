{pkgs ? import <nixpkgs> {}  }: 
pkgs.mkShell {
	nativeBuildInputs = with pkgs; [
		pkgs.python3
		pkgs.nodejs_22
		
	]	;
}
