{
  description = "Development environment for helm-charts-updater";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Python environment
            python313
            poetry

            # Required by the application
            helm-docs
            git

            # Development tools
            mypy
          ];

          shellHook = ''
            echo "helm-charts-updater development environment"
            echo "Python: $(python --version)"
            echo "Poetry: $(poetry --version)"
            echo "helm-docs: $(helm-docs --version)"
            echo ""
            echo "Run 'poetry install' to install dependencies"
          '';
        };
      }
    );
}
