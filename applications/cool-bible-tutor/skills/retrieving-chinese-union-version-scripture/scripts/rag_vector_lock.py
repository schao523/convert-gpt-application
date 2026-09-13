import os
from pathlib import Path
import time


class VectorFileBusyError(RuntimeError):
    pass


class VectorFileLock:
    """Advisory lock shared by this project's JSON ingestion and metadata sync."""

    def __init__(self, vector_path: Path, timeout: float = 5.0):
        self.path = Path(str(Path(vector_path)) + ".lock")
        self.timeout = timeout
        self.handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a+b")
        self.handle.seek(0, os.SEEK_END)
        if self.handle.tell() == 0:
            self.handle.write(b"0")
            self.handle.flush()
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self._acquire()
                return self
            except OSError as error:
                if time.monotonic() >= deadline:
                    self.handle.close()
                    self.handle = None
                    raise VectorFileBusyError("The JSON vector store is busy") from error
                time.sleep(0.05)

    def _acquire(self):
        self.handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.handle is None:
            return
        try:
            self.handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        finally:
            self.handle.close()
            self.handle = None
