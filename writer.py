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
    def format_data(self, data: List[Dict[str, Any]]) -> str:
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
        """Abstract method to write data."""


class FileWriter(Writer):
    async def write_data(self, file: IO, formatted_data: Any, mode: str = "w") -> None:
        async with aiofiles.open(file.name, mode=mode) as f:
            await f.write(formatted_data)


class ExcelFileWriter(Writer):
    async def write_data(self, file: IO, formatted_data: openpyxl.Workbook, mode: str = "w") -> None:
        formatted_data.save(file.name)


class DataWriter:
    def __init__(self, formatter: Formatter, writer: Writer):
        self.formatter = formatter
        self.writer = writer

    async def write_data(self, file: IO, data: List[Dict[str, Any]], mode: str = "w") -> None:
        formatted_data = self.formatter.format_data(data)
        await self.writer.write_data(file, formatted_data, mode)


# Example usage
import asyncio

async def main():
    formatter = JSONFormatter()
    writer = FileWriter()
    data_writer = DataWriter(formatter, writer)
    with open("data.json", "w") as file:
        await data_writer.write_data(file, [{"name": "John", "age": 30}])


# Uncomment the following line to run the example
# asyncio.run(main())
