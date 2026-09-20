class TaskNameError(ValueError):
    """Raised when a root Task Scheduler task name is invalid."""


class TaskSchedulerError(RuntimeError):
    """Native scheduler failure with an unsigned HRESULT and operation name."""

    def __init__(self, message: str, hresult: int, operation: str) -> None:
        super().__init__(message)
        self.hresult = hresult
        self.operation = operation

    def __reduce__(self):
        return (type(self), (str(self), self.hresult, self.operation))


class TaskPermissionError(PermissionError):
    """Native access denial with an unsigned HRESULT and operation name."""

    def __init__(self, message: str, hresult: int, operation: str) -> None:
        super().__init__(message)
        self.hresult = hresult
        self.operation = operation

    def __reduce__(self):
        return (type(self), (str(self), self.hresult, self.operation))
