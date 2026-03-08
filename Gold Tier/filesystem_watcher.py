# filesystem_watcher.py
# Monitors a drop folder and creates .md action files
# Install: pip install watchdog

import shutil
import logging
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VAULT_PATH = Path("./AI_Employee_Vault")
NEEDS_ACTION = VAULT_PATH / "Needs_Action"
DROP_FOLDER = Path("./Drop_Here")  # Put files here to trigger the watcher

class DropFolderHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        source = Path(event.src_path)
        logger.info(f"New file detected: {source.name}")
        
        # Copy file to Needs_Action
        dest = NEEDS_ACTION / f"FILE_{source.name}"
        NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        
        # Create metadata .md file
        meta_path = NEEDS_ACTION / f"FILE_{source.stem}.md"
        meta_path.write_text(f"""---
type: file_drop
original_name: {source.name}
size: {source.stat().st_size} bytes
received: {datetime.now().isoformat()}
status: pending
---

## File Dropped for Processing
A new file has arrived and needs to be processed.

## Suggested Actions
- [ ] Review file contents
- [ ] Determine appropriate action
- [ ] Move to /Done when complete
""")
        logger.info(f"Action file created for: {source.name}")

def main():
    DROP_FOLDER.mkdir(exist_ok=True)
    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
    
    handler = DropFolderHandler()
    observer = Observer()
    observer.schedule(handler, str(DROP_FOLDER), recursive=False)
    observer.start()
    
    logger.info(f"File System Watcher started. Monitoring: {DROP_FOLDER.resolve()}")
    logger.info("Drop any file into the 'Drop_Here' folder to trigger an action.")
    
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
