use pyo3::exceptions::{PyPermissionError, PyRuntimeError};
use pyo3::prelude::*;

#[cfg(windows)]
use windows::core::BSTR;

#[cfg(windows)]
use windows::Win32::Foundation::{ERROR_FILE_NOT_FOUND, ERROR_PATH_NOT_FOUND};

#[cfg(windows)]
use windows::Win32::System::Com::{
    CLSCTX_INPROC_SERVER, COINIT_MULTITHREADED, CoCreateInstance, CoInitializeEx, CoUninitialize,
};
#[cfg(windows)]
use windows::Win32::System::TaskScheduler::{
    ITaskService, TASK_CREATE_OR_UPDATE, TASK_LOGON_INTERACTIVE_TOKEN, TaskScheduler,
};
#[cfg(windows)]
use windows::Win32::System::Variant::VARIANT;

#[cfg(windows)]
struct ComGuard;

#[cfg(windows)]
impl ComGuard {
    fn initialize() -> PyResult<Self> {
        unsafe {
            CoInitializeEx(None, COINIT_MULTITHREADED)
                .map_err(|error| PyRuntimeError::new_err(error.to_string()))?;
        }
        Ok(Self)
    }
}

#[cfg(windows)]
impl Drop for ComGuard {
    fn drop(&mut self) {
        unsafe { CoUninitialize() };
    }
}

#[cfg(windows)]
fn connect_service() -> PyResult<(ComGuard, ITaskService)> {
    let com = ComGuard::initialize()?;
    let service = unsafe {
        CoCreateInstance::<_, ITaskService>(&TaskScheduler, None, CLSCTX_INPROC_SERVER)
            .map_err(|error| PyRuntimeError::new_err(error.to_string()))?
    };
    unsafe {
        service
            .Connect(
                VARIANT::default(),
                VARIANT::default(),
                VARIANT::default(),
                VARIANT::default(),
            )
            .map_err(|error| PyRuntimeError::new_err(error.to_string()))?;
    }
    Ok((com, service))
}

#[cfg(windows)]
fn map_windows_error(error: windows::core::Error) -> PyErr {
    if error.code().0 == -2147024891 {
        PyPermissionError::new_err(error.to_string())
    } else {
        PyRuntimeError::new_err(error.to_string())
    }
}

#[pyfunction]
fn register_xml(task_name: &str, xml_data: &str) -> PyResult<()> {
    #[cfg(windows)]
    {
        let (_com, service) = connect_service()?;
        let root = unsafe {
            service
                .GetFolder(&BSTR::from("\\"))
                .map_err(map_windows_error)?
        };
        unsafe {
            root.RegisterTask(
                &BSTR::from(task_name),
                &BSTR::from(xml_data),
                TASK_CREATE_OR_UPDATE.0,
                VARIANT::default(),
                VARIANT::default(),
                TASK_LOGON_INTERACTIVE_TOKEN,
                VARIANT::default(),
            )
            .map_err(map_windows_error)?;
        }
        Ok(())
    }
    #[cfg(not(windows))]
    {
        let _ = (task_name, xml_data);
        Err(PyRuntimeError::new_err(
            "wintask Task Scheduler support is only available on Windows",
        ))
    }
}

#[pyfunction]
fn delete_task(task_name: &str) -> PyResult<()> {
    #[cfg(windows)]
    {
        let (_com, service) = connect_service()?;
        let root = unsafe {
            service
                .GetFolder(&BSTR::from("\\"))
                .map_err(map_windows_error)?
        };
        unsafe {
            root.DeleteTask(&BSTR::from(task_name), 0)
                .map_err(map_windows_error)?;
        }
        Ok(())
    }
    #[cfg(not(windows))]
    {
        let _ = task_name;
        Err(PyRuntimeError::new_err(
            "wintask Task Scheduler support is only available on Windows",
        ))
    }
}

#[pyfunction]
fn run_task(task_name: &str) -> PyResult<()> {
    #[cfg(windows)]
    {
        let (_com, service) = connect_service()?;
        let root = unsafe {
            service
                .GetFolder(&BSTR::from("\\"))
                .map_err(map_windows_error)?
        };
        let task = unsafe {
            root.GetTask(&BSTR::from(task_name))
                .map_err(map_windows_error)?
        };
        unsafe {
            task.RunEx(VARIANT::default(), 0, 0, &BSTR::new())
                .map_err(map_windows_error)?;
        }
        Ok(())
    }
    #[cfg(not(windows))]
    {
        let _ = task_name;
        Err(PyRuntimeError::new_err(
            "wintask Task Scheduler support is only available on Windows",
        ))
    }
}

#[pyfunction]
fn task_exists(task_name: &str) -> PyResult<bool> {
    #[cfg(windows)]
    {
        let (_com, service) = connect_service()?;
        let root = unsafe {
            service
                .GetFolder(&BSTR::from("\\"))
                .map_err(map_windows_error)?
        };
        match unsafe { root.GetTask(&BSTR::from(task_name)) } {
            Ok(_) => Ok(true),
            Err(error)
                if error.code() == ERROR_FILE_NOT_FOUND.to_hresult()
                    || error.code() == ERROR_PATH_NOT_FOUND.to_hresult() =>
            {
                Ok(false)
            }
            Err(error) => Err(map_windows_error(error)),
        }
    }
    #[cfg(not(windows))]
    {
        let _ = task_name;
        Err(PyRuntimeError::new_err(
            "wintask Task Scheduler support is only available on Windows",
        ))
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
