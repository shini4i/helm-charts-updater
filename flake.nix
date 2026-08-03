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
            python314
            uv

            # Required by the application
            helm-docs
            git

            # Development tools
            go-task
            pre-commit
          ];

          shellHook = ''
            echo "helm-charts-updater development environment"
            echo "Python: $(python --version)"
            echo "uv: $(uv --version)"
            echo "helm-docs: $(helm-docs --version)"
            echo ""
            echo "Run 'uv sync' to install dependencies"
          '';
        };
      }
    );
}
