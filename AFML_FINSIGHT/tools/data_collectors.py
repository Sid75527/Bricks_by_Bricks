"""Data collection tools for FinSight."""
from __future__ import annotations

import json
from typing import Any, Dict

import pandas as pd
import yfinance as yf
import requests
from fredapi import Fred
from sec_edgar_api import EdgarClient

class MarketDataCollector:
    """Fetches market and macro data from yfinance and FRED."""

    def __init__(self, fred_api_key: str) -> None:
        if not fred_api_key:
            raise ValueError("FRED API key must be provided for MarketDataCollector")
        self.fred = Fred(api_key=fred_api_key)

    def get_stock_history(self, ticker: str, period: str = "2y") -> pd.DataFrame:
        data = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if data.empty:
            raise RuntimeError(f"No market data returned for {ticker}")
        return data

    def get_fred_series(self, series_id: str) -> pd.Series:
        series = self.fred.get_series(series_id)
        if series is None or series.empty:
            raise RuntimeError(f"No FRED data for series {series_id}")
        return series


class SECFilingCollector:
    """Retrieves SEC filings for a given ticker."""

    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent
        self.client = EdgarClient(user_agent=user_agent)
        self._ticker_cache: Dict[str, str] = {}

    def _lookup_cik(self, ticker: str) -> str:
        ticker = ticker.upper()
        if ticker in self._ticker_cache:
            return self._ticker_cache[ticker]

        url = "https://www.sec.gov/files/company_tickers.json"
        response = requests.get(url, headers={"User-Agent": self.user_agent}, timeout=30)
        if response.status_code != 200:
            raise RuntimeError("Failed to download SEC company tickers mapping")

        mapping: Dict[str, Any] = response.json()
        for entry in mapping.values():
            if entry.get("ticker", "").upper() == ticker:
                cik = str(entry.get("cik_str", "")).strip().zfill(10)
                self._ticker_cache[ticker] = cik
                return cik

        raise RuntimeError(f"Ticker {ticker} not found in SEC company ticker list")

    def get_latest_10k(self, ticker: str, truncate: int = 100000) -> Dict[str, Any]:
        try:
            submission = self.client.get_submissions(ticker)
        except ValueError:
            cik = self._lookup_cik(ticker)
            submission = self.client.get_submissions(cik)
        filings = submission.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        accession_numbers = filings.get("accessionNumber", [])
        primary_docs = filings.get("primaryDocument", [])

        target_index = None
        for idx, form in enumerate(forms):
            if form == "10-K":
                target_index = idx
                break

        if target_index is None:
            raise RuntimeError(f"No 10-K filing found for {ticker}")

        accession = accession_numbers[target_index]
        primary_doc = primary_docs[target_index]
        cik = submission.get("cik")
        if not (accession and primary_doc and cik):
            raise RuntimeError(f"Incomplete filing metadata for {ticker}")

        accession_path = accession.replace("-", "")
        url = (
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_path}/{primary_doc}"
        )

        response = requests.get(url, headers={"User-Agent": self.user_agent}, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to download 10-K document for {ticker}: {response.status_code}")

        content = response.text
        return {"text": content[:truncate], "source_url": url}


class StructuredArtifact:
    """Helper for storing collected artifacts with metadata."""

    def __init__(self, name: str, content: Any, metadata: Dict[str, Any] | None = None) -> None:
        self.name = name
        self.content = content
        self.metadata = metadata or {}

    def to_variable_payload(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "content": self.content,
            "metadata": self.metadata,
        }
