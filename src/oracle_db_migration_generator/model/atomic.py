"""Commit a new sibling directory, tolerating short Windows sharing locks."""
import os
from pathlib import Path
import time


def rename_new_directory(source,destination):
    source=Path(source);destination=Path(destination)
    if source.parent.resolve()!=destination.parent.resolve():raise ValueError('ATOMIC_DIRECTORY_PARENT_MISMATCH')
    for attempt in range(5):
        if destination.exists():raise FileExistsError('OUTPUT_ALREADY_EXISTS')
        try:
            os.rename(source,destination)
            return
        except PermissionError as error:
            # Antivirus/indexer handles can briefly prevent a Windows rename.
            # Other permission errors and persistent locks still fail closed.
            if getattr(error,'winerror',None) not in {5,32} or attempt==4:raise
            time.sleep(.1*(attempt+1))
