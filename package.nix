{
  buildPythonApplication,
  hatchling,
  structlog,
  pydantic,
  python-gitlab,
  sh,
  munch,
  pytimeparse2,
  typer,
  pytestCheckHook,
  git,
  nix,
  ...
}:

buildPythonApplication {
  pname = "gitlab-flake-bot";
  version = "0.1.0";

  src = ./.;

  pyproject = true;
  build-system = [ hatchling ];

  dependencies =
    [
      structlog
      pydantic
      python-gitlab
      sh
      munch
      pytimeparse2
      typer
    ];

  makeWrapperArgs = [
    "--prefix PATH : ${git}/bin"
    "--prefix PATH : ${nix}/bin"
  ];

  pythonImportsCheck = [ "gitlab_flake_bot" ];

  doCheck = true;

  nativeCheckInputs = [
  ];
}
