class OcigoatError(Exception):
    pass


class ManifestError(OcigoatError):
    pass


class ConfigError(OcigoatError):
    pass


class ScenarioNotFoundError(OcigoatError):
    pass


class InstanceExistsError(OcigoatError):
    pass


class InstanceNotFoundError(OcigoatError):
    pass


class TerraformError(OcigoatError):
    def __init__(self, message, returncode):
        super().__init__(message)
        self.returncode = returncode


class CredentialError(OcigoatError):
    pass
