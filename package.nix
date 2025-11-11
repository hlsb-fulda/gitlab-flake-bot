{
  buildPythonApplication,
  hatchling,
  pydantic,
  prometheus-client,
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
      pydantic
      prometheus-client
    ];

  pythonImportsCheck = [ "gitlab-flake-bot" ];

  doCheck = true;

  nativeCheckInputs = [
    pytestCheckHook
  ];
}
