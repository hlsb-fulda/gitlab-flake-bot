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

  pythonImportsCheck = [ "gitlab_flake_bot" ];

  doCheck = true;

  nativeCheckInputs = [
  ];
}
