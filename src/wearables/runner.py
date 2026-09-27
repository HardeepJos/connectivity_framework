from __future__ import annotations

import time
from collections.abc import Iterable

from .adapters import UnsupportedAdapterOperation
from .cases import ConnectivityTestCase
from .models import TestCaseResult, TestStatus


class TestRunner:
    def __init__(self, cases: Iterable[ConnectivityTestCase]) -> None:
        self.cases = list(cases)

    def run(self) -> list[TestCaseResult]:
        results: list[TestCaseResult] = []
        for case in self.cases:
            started = time.perf_counter()
            try:
                result = case.run()
            except UnsupportedAdapterOperation as error:
                result = TestCaseResult(case.name, TestStatus.SKIPPED, str(error))
            except Exception as error:  # adapters surface device errors as test failures
                result = TestCaseResult(case.name, TestStatus.FAILED, str(error))
            results.append(TestCaseResult(result.name, result.status, result.message, (time.perf_counter() - started) * 1000, result.details))
        return results