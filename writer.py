# coding: utf-8
import csv
import json
import openpyxl
import aiofiles
from abc import ABC, abstractmethod
from typing import List, Dict, Any, IO
import logging
import os
import asyncio
from datetime import datetime
from filelock import FileLock
import hashlib
import gzip
from enum import Enum

# Enhanced logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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


class DataWriter:
    def __init__(self, formatter: Formatter, writer: Writer):
        self.formatter = formatter
        self.writer = writer

    async def write_data(self, file: IO, data: Any, mode: str = "w") -> None:
        formatted_data = self.formatter.format_data(data)
        await self.writer.write_data(file, formatted_data, mode)


# Example usage
async def main():
    formatter = JSONFormatter()
    writer = GzipFileWriter()
    data_writer = DataWriter(formatter, writer)
    filename = f"data_{datetime.now().strftime('%Y%m%d%H%M%S')}.json.gz"
    with open(filename, "w") as file:
        await data_writer.write_data(file, [{"name": "John", "age": 30}])


if __name__ == "__main__":
    asyncio.run(main())
