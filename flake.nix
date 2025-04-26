{
  description = "I/O Communication Library";
  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      rec {
        ahio = pythonPkgs: pythonPkgs.buildPythonPackage {
          format = "pyproject";
          name = "ahio";
          src = ./.;
          propagatedBuildInputs = with pythonPkgs; [
            hatchling
            pymodbus
            pyserial
            python-snap7
          ];
        };
        packages.default = ahio pkgs.python311Packages;
      });
}
