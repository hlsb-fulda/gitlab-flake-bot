{
  buildPythonApplication,
  hatchling,
  structlog,
  pydantic,
  pydantic-settings,
  python-gitlab,
  sh,
  munch,
  pytimeparse2,
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
      pydantic-settings
      python-gitlab
      sh
      munch
      pytimeparse2
    ];

  pythonImportsCheck = [ "gitlab_flake_bot" ];

  doCheck = true;

  nativeCheckInputs = [
  ];
}
