#writerer.py module
# coding: utf-8
import csv
import json
import openpyxl
import aiofiles
from abc import ABC, abstractmethod
from typing import List, Dict, Any, IO, Optional
import logging
import os

# Setting up logging configuration
logging.basicConfig(level=logging.INFO)

class DataWriterError(Exception):
    """Custom exception for DataWriter errors."""


class Writer(ABC):
    @abstractmethod
    async def write_data(self, file: IO, data: List[Dict[str, Any]], mode: str = "w") -> None:
        """Abstract method to write data."""


class DataWriter:
    def __init__(self, writer: Writer):
        self.writer = writer

    @staticmethod
    def create_writer(filename: str, **kwargs) -> "DataWriter":
        """Factory method to create appropriate writer based on file extension."""
        ext = filename.split(".")[-1]
        writers = {
            "csv": CSVDataWriter,
            "json": JSONDataWriter,
            "xlsx": ExcelDataWriter,
        }
        
        # Check if the required libraries are installed
        if ext == 'xlsx' and not openpyxl:
            raise DataWriterError("openpyxl library not found. Please install it.")
        
        return DataWriter(writers.get(ext, JSONDataWriter)(**kwargs))

    async def write_data(self, file: IO, data: List[Dict[str, Any]], mode: str = "w") -> None:
        """Write data to file using the selected writer."""
        if not os.access(file.name, os.W_OK):
            logging.error(f"Permission denied to write to {file.name}")
            raise DataWriterError(f"Permission denied to write to {file.name}")

        self._validate_data(data)
        await self.writer.write_data(file, data, mode)
        logging.info(f"Data written to {file.name}")

    def _validate_data(self, data: List[Dict[str, Any]]) -> None:
        """Validate data for empty content and inconsistent headers."""
        if not data or any(list(item.keys()) != list(data[0].keys()) for item in data):
            logging.error("Invalid data.")
            raise DataWriterError("Invalid data.")


class CSVDataWriter(Writer):
    """CSV writer class."""
    def __init__(self, dialect: Optional[str] = None, compression: Optional[str] = None):
        self.dialect = dialect
        self.compression = compression

    async def write_data(self, file: IO, data: List[Dict[str, Any]], mode: str = "w") -> None:
        """Write data to CSV file."""
        async with aiofiles.open(file.name, mode=mode) as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys(), dialect=self.dialect)
            writer.writeheader()
            writer.writerows(data)


class JSONDataWriter(Writer):
    """JSON writer class."""
    def __init__(self, indent: Optional[int] = None):
        self.indent = indent

    async def write_data(self, file: IO, data: List[Dict[str, Any]], mode: str = "w") -> None:
        """Write data to JSON file."""
        async with aiofiles.open(file.name, mode=mode) as f:
            await f.write(json.dumps(data, indent=self.indent))


class ExcelDataWriter(Writer):
    """Excel writer class."""
    async def write_data(self, file: IO, data: List[Dict[str, Any]], mode: str = "w") -> None:
        """Write data to Excel file."""
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        headers = list(data[0].keys())
        sheet.append(headers)
        for row in data:
            sheet.append([row[header] for header in headers])
        workbook.save(file.name)


# Example usage
import asyncio

async def main():
    writer = DataWriter.create_writer("data.json", indent=4)
    with open("data.json", "w") as file:
        await writer.write_data(file, [{"name": "John", "age": 30}])


# Uncomment the following line to run the example
# asyncio.run(main())
