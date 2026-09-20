#[cfg(not(windows))]
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;

#[cfg(windows)]
mod native {
    use windows::Win32::Foundation::{
        E_ACCESSDENIED, ERROR_FILE_NOT_FOUND, ERROR_PATH_NOT_FOUND, RPC_E_CHANGED_MODE,
    };
    use windows::Win32::System::Com::{
        CLSCTX_INPROC_SERVER, COINIT_MULTITHREADED, CoCreateInstance, CoInitializeEx,
        CoUninitialize,
    };
    use windows::Win32::System::TaskScheduler::{
        ITaskFolder, ITaskService, TASK_CREATE_OR_UPDATE, TASK_LOGON_INTERACTIVE_TOKEN,
        TaskScheduler,
    };
    use windows::Win32::System::Variant::VARIANT;
    use windows::core::{BSTR, Error, HRESULT};

    #[derive(Debug)]
    pub struct Failure {
        pub hresult: u32,
        pub message: String,
        pub operation: &'static str,
    }

    impl Failure {
        fn new(error: Error, operation: &'static str) -> Self {
            Self {
                hresult: error.code().0 as u32,
                message: error.to_string(),
                operation,
            }
        }

        pub fn exception_name(&self) -> &'static str {
            if self.hresult == E_ACCESSDENIED.0 as u32 {
                "TaskPermissionError"
            } else {
                "TaskSchedulerError"
            }
        }
    }

    trait Context<T> {
        fn context(self, operation: &'static str) -> Result<T, Failure>;
    }

    impl<T> Context<T> for windows::core::Result<T> {
        fn context(self, operation: &'static str) -> Result<T, Failure> {
            self.map_err(|error| Failure::new(error, operation))
        }
    }

    struct ComGuard {
        owned: bool,
    }

    impl ComGuard {
        fn initialize() -> Result<Self, Failure> {
            // An existing STA belongs to the caller. Use it without balancing
            // its initialization. Both S_OK and S_FALSE acquire our own count.
            match unsafe { CoInitializeEx(None, COINIT_MULTITHREADED) } {
                Ok(()) => Ok(Self { owned: true }),
                Err(error) if error.code() == RPC_E_CHANGED_MODE => Ok(Self { owned: false }),
                Err(error) => Err(Failure::new(error, "CoInitializeEx")),
            }
        }
    }

    impl Drop for ComGuard {
        fn drop(&mut self) {
            if self.owned {
                unsafe { CoUninitialize() };
            }
        }
    }

    // Field order ensures COM interfaces are released before our COM count.
    struct Connection {
        root: ITaskFolder,
        _service: ITaskService,
        _com: ComGuard,
    }

    fn connect() -> Result<Connection, Failure> {
        let com = ComGuard::initialize()?;
        let service = unsafe {
            CoCreateInstance::<_, ITaskService>(&TaskScheduler, None, CLSCTX_INPROC_SERVER)
                .context("CoCreateInstance")?
        };
        unsafe {
            service
                .Connect(
                    VARIANT::default(),
                    VARIANT::default(),
                    VARIANT::default(),
                    VARIANT::default(),
                )
                .context("Connect")?;
        }
        let root = unsafe { service.GetFolder(&BSTR::from("\\")).context("GetFolder")? };
        Ok(Connection {
            root,
            _service: service,
            _com: com,
        })
    }

    pub fn register(name: &str, xml: &str) -> Result<(), Failure> {
        let connection = connect()?;
        unsafe {
            connection
                .root
                .RegisterTask(
                    &BSTR::from(name),
                    &BSTR::from(xml),
                    TASK_CREATE_OR_UPDATE.0,
                    VARIANT::default(),
                    VARIANT::default(),
                    TASK_LOGON_INTERACTIVE_TOKEN,
                    VARIANT::default(),
                )
                .context("RegisterTask")?;
        }
        Ok(())
    }

    pub fn delete(name: &str) -> Result<(), Failure> {
        let connection = connect()?;
        unsafe {
            connection
                .root
                .DeleteTask(&BSTR::from(name), 0)
                .context("DeleteTask")
        }
    }

    pub fn run(name: &str) -> Result<(), Failure> {
        let connection = connect()?;
        let task = unsafe {
            connection
                .root
                .GetTask(&BSTR::from(name))
                .context("GetTask")?
        };
        unsafe {
            task.RunEx(VARIANT::default(), 0, 0, &BSTR::new())
                .context("RunEx")?;
        }
        Ok(())
    }

    fn is_missing(code: HRESULT) -> bool {
        code == ERROR_FILE_NOT_FOUND.to_hresult() || code == ERROR_PATH_NOT_FOUND.to_hresult()
    }

    pub fn exists(name: &str) -> Result<bool, Failure> {
        let connection = connect()?;
        // Only GetTask absence means false: connection/folder errors propagate.
        match unsafe { connection.root.GetTask(&BSTR::from(name)) } {
            Ok(_) => Ok(true),
            Err(error) if is_missing(error.code()) => Ok(false),
            Err(error) => Err(Failure::new(error, "GetTask")),
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;
        use windows::Win32::Foundation::SCHED_E_ACCOUNT_INFORMATION_NOT_SET;
        const RPC_UNAVAILABLE: HRESULT = HRESULT::from_win32(1722);

        #[test]
        fn only_missing_task_codes_mean_absence() {
            assert!(is_missing(ERROR_FILE_NOT_FOUND.to_hresult()));
            assert!(is_missing(ERROR_PATH_NOT_FOUND.to_hresult()));
            for code in [
                E_ACCESSDENIED,
                SCHED_E_ACCOUNT_INFORMATION_NOT_SET,
                RPC_UNAVAILABLE,
            ] {
                assert!(!is_missing(code));
            }
        }

        #[test]
        fn failures_preserve_hresult_context_and_permission_classification() {
            for operation in [
                "CoInitializeEx",
                "CoCreateInstance",
                "Connect",
                "GetFolder",
                "GetTask",
                "RegisterTask",
                "RunEx",
                "DeleteTask",
            ] {
                for (code, class) in [
                    (E_ACCESSDENIED, "TaskPermissionError"),
                    (RPC_UNAVAILABLE, "TaskSchedulerError"),
                ] {
                    let error = Failure::new(Error::from(code), operation);
                    assert_eq!(error.hresult, code.0 as u32);
                    assert_eq!(error.operation, operation);
                    assert_eq!(error.exception_name(), class);
                }
            }
        }
    }
}

#[cfg(windows)]
fn map_failure(py: Python<'_>, error: native::Failure) -> PyErr {
    let instance = py
        .import("wintask.errors")
        .and_then(|module| module.getattr(error.exception_name()))
        .and_then(|class| class.call1((error.message, error.hresult, error.operation)));
    match instance {
        Ok(instance) => PyErr::from_value(instance),
        Err(error) => error,
    }
}

#[cfg(not(windows))]
fn unsupported() -> PyErr {
    PyRuntimeError::new_err("wintask Task Scheduler support is only available on Windows")
}

#[pyfunction]
fn register_xml(py: Python<'_>, task_name: &str, xml_data: &str) -> PyResult<()> {
    #[cfg(windows)]
    {
        py.detach(|| native::register(task_name, xml_data))
            .map_err(|error| map_failure(py, error))
    }
    #[cfg(not(windows))]
    {
        let _ = (py, task_name, xml_data);
        Err(unsupported())
    }
}

#[pyfunction]
fn delete_task(py: Python<'_>, task_name: &str) -> PyResult<()> {
    #[cfg(windows)]
    {
        py.detach(|| native::delete(task_name))
            .map_err(|error| map_failure(py, error))
    }
    #[cfg(not(windows))]
    {
        let _ = (py, task_name);
        Err(unsupported())
    }
}

#[pyfunction]
fn run_task(py: Python<'_>, task_name: &str) -> PyResult<()> {
    #[cfg(windows)]
    {
        py.detach(|| native::run(task_name))
            .map_err(|error| map_failure(py, error))
    }
    #[cfg(not(windows))]
    {
        let _ = (py, task_name);
        Err(unsupported())
    }
}

#[pyfunction]
fn task_exists(py: Python<'_>, task_name: &str) -> PyResult<bool> {
    #[cfg(windows)]
    {
        py.detach(|| native::exists(task_name))
            .map_err(|error| map_failure(py, error))
    }
    #[cfg(not(windows))]
    {
        let _ = (py, task_name);
        Err(unsupported())
    }
}

#[pymodule]
fn _wintask_backend(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(register_xml, m)?)?;
    m.add_function(wrap_pyfunction!(delete_task, m)?)?;
    m.add_function(wrap_pyfunction!(run_task, m)?)?;
    m.add_function(wrap_pyfunction!(task_exists, m)?)?;
    Ok(())
}
