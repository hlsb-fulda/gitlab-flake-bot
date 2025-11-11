{
  description = "GitLab bot to update NixOS Flakes";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

      in
      {
        packages = {
          gitlab-flake-bot = pkgs.python3.pkgs.callPackage ./package.nix { };
          default = self.packages.${system}.gitlab-flake-bot;
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.gitlab-flake-bot ];
          packages = [
            self.packages.${system}.gitlab-flake-bot.build-system
            pkgs.uv
            pkgs.mockoon
            pkgs.python3.pkgs.ruff
            pkgs.python3.pkgs.pytest
          ];
        };

        formatter = pkgs.nixfmt-tree;
      }
    );
}
