import csv
import json
import openpyxl
import aiofiles
from abc import ABC, abstractmethod
from typing import List, Dict, Any, IO, Callable
import logging
import os
import asyncio
from tqdm import tqdm
import io
import gzip
from datetime import datetime
from filelock import FileLock
import shutil
import hashlib
from colorlog import ColoredFormatter
from prettytable import PrettyTable

# Enhanced logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(reset)s %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red',
    }
)
ch.setFormatter(formatter)
logger.addHandler(ch)


class DataWriterError(Exception):
    """Custom exception for DataWriter errors."""


class Formatter(ABC):
    @abstractmethod
    def format_data(self, data: List[Dict[str, Any]]) -> Any:
        """Abstract method to format data."""


class CSVFormatter(Formatter):
    def format_data(self, data: List[Dict[str, Any]]) -> str:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()


class JSONFormatter(Formatter):
    def format_data(self, data: Any) -> str:
        return json.dumps(data, indent=4)


class ExcelFormatter(Formatter):
    def format_data(self, data: List[Dict[str, Any]]) -> openpyxl.Workbook:
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        headers = list(data[0].keys())
        sheet.append(headers)
        for row in data:
            sheet.append([row[header] for header in headers])
        return workbook


class Writer(ABC):
    @abstractmethod
    async def write_data(self, file: IO, formatted_data: Any, mode: str = "w") -> None:
        pass


class FileWriter(Writer):
    CHUNK_SIZE = 1024 * 1024  # 1 MB

    @lru_cache(maxsize=10)  # Simple caching for recent writes
    async def write_data(self, file: IO, formatted_data: Any, mode: str = "w") -> None:
        # Chunked writing
        start = 0
        end = self.CHUNK_SIZE
        while start < len(formatted_data):
            chunk = formatted_data[start:end]
            async with aiofiles.open(file.name, mode=mode) as f:
                await f.write(chunk)
            start = end
            end += self.CHUNK_SIZE

        logger.info(f"Data successfully written to {file.name}")


class GzipFileWriter(FileWriter):
    async def write_data(self, file: IO, formatted_data: Any, mode: str = "w") -> None:
        with gzip.open(file.name, mode) as f:
            f.write(formatted_data.encode())
        logger.info(f"Compressed data successfully written to {file.name}")


class ExcelFileWriter(Writer):
    async def write_data(self, file: IO, formatted_data: openpyxl.Workbook, mode: str = "w") -> None:
        formatted_data.save(file.name)
        logger.info(f"Data successfully written to {file.name}")


class FileAccessor:
    METADATA_CACHE = {}

    @staticmethod
    def exists(filename: str) -> bool:
        return os.path.exists(filename)

    @staticmethod
    def rename(src: str, dest: str) -> None:
        os.rename(src, dest)

    @staticmethod
    def delete(filename: str) -> None:
        os.remove(filename)

    @staticmethod
    def merge_files(target_file: str, *files: str, order=None, remove_duplicates=False) -> None:
        if order:
            files = sorted(files, key=lambda x: order.index(x) if x in order else float('inf'))

        seen = set()
        with open(target_file, 'w') as outfile:
            for fname in files:
                with open(fname) as infile:
                    for line in infile:
                        if remove_duplicates:
                            if line in seen:
                                continue
                            seen.add(line)
                        outfile.write(line)

    @staticmethod
    def copy(src: str, dest: str) -> None:
        shutil.copy(src, dest)

    @staticmethod
    def move(src: str, dest: str) -> None:
        shutil.move(src, dest)

    @staticmethod
    def get_file_metadata(filename: str) -> dict:
        if filename not in FileAccessor.METADATA_CACHE:
            FileAccessor.METADATA_CACHE[filename] = {
                'size': os.path.getsize(filename),
                'modified_time': os.path.getmtime(filename),
                'created_time': os.path.getctime(filename)
            }
        return FileAccessor.METADATA_CACHE[filename]

    @staticmethod
    def set_permissions(filename: str, mode: int) -> None:
        os.chmod(filename, mode)

    @staticmethod
    def validate_checksum(filename: str, expected_checksum: str) -> bool:
        with open(filename, 'rb') as f:
            file_hash = hashlib.md5()
            while chunk := f.read(8192):
                file_hash.update(chunk)
        return file_hash.hexdigest() == expected_checksum

    # Additional methods like incremental sync, etc., can be added here


class FileManager:
    def __init__(self, accessor=FileAccessor):
        self.accessor = accessor

    def handle_file_operations(self, *args, **kwargs):
        # This method can be expanded to handle various file operations
        pass


class DataWriter:
    def __init__(self, formatter: Formatter, writer: Writer, filename_formatter=None, version_threshold=None, pre_write_callback=None, post_write_callback=None, file_accessor=FileAccessor):
        self.formatter = formatter
        self.writer = writer
        self.filename_formatter = filename_formatter or (lambda base: f"{base}_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        self.version_threshold = version_threshold
        self.pre_write_callback = pre_write_callback
        self.post_write_callback = post_write_callback
        self.accessor = file_accessor

    def validate_data(self, data: Any) -> bool:
        # Placeholder validation logic
        return bool(data)

    async def write_data(self, file: IO, data: Any, mode: str = "w") -> None:
        # Pre-write callback
        if self.pre_write_callback:
            self.pre_write_callback(file)

        # Data validation
        if not self.validate_data(data):
            logger.error("Data validation failed.")
            return

        # Handle versioning and threshold
        if self.accessor.exists(file.name) and mode == "w":
            versioned_name = f"{file.name}.v{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.accessor.rename(file.name, versioned_name)
            logger.info(f"Versioned existing file to {versioned_name}")

            if self.version_threshold:
                versions = sorted([f for f in os.listdir() if f.startswith(file.name) and f != file.name])
                while len(versions) > self.version_threshold:
                    self.accessor.delete(versions.pop(0))

        # Handle race conditions using file locks and potential write errors
        try:
            with FileLock(f"{file.name}.lock"):
                formatted_data = self.formatter.format_data(data)
                await self.writer.write_data(file, formatted_data, mode)
        except Exception as e:
            logger.error(f"Error writing data: {e}. Attempting rollback...")
            # Rollback logic
            if self.accessor.exists(f"{file.name}.v{datetime.now().strftime('%Y%m%d%H%M%S')}"):
                self.accessor.copy(f"{file.name}.v{datetime.now().strftime('%Y%m%d%H%M%S')}", file.name)
            else:
                logger.error("Rollback failed. No previous version found.")

        # Post-write callback
        if self.post_write_callback:
            self.post_write_callback(file)

    def merge_files(self, target_file: str, *files: str, order=None, remove_duplicates=False) -> None:
        self.accessor.merge_files(target_file, *files, order=order, remove_duplicates=remove_duplicates)

    def get_filename(self, base_name: str) -> str:
        return self.filename_formatter(base_name)


# Example usage
async def main():
    def custom_filename_formatter(base: str) -> str:
        return f"{base}_custom_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    formatter = JSONFormatter()
    writer = GzipFileWriter()
    data_writer = DataWriter(formatter, writer, filename_formatter=custom_filename_formatter, version_threshold=5)
    filename = data_writer.get_filename("data") + ".json.gz"
    with open(filename, "w") as file:
        await data_writer.write_data(file, [{"name": "John", "age": 30}])


if __name__ == "__main__":
    asyncio.run(main())
