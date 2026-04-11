#!/usr/bin/env python3
"""Integration Abstraction Layer — Adapter pattern for external tools.

Wraps every external dependency (Pandoc, XeLaTeX, OpenAI, Gemini) behind
stable interfaces so that swapping a tool requires changing only the adapter,
not the pipeline code.

Design principles:
    - Each adapter implements a Protocol (structural typing)
    - Factory functions select the concrete adapter at runtime
    - Version requirements are declared per-adapter, checked at init
    - All subprocess calls have timeouts and structured error reporting

Usage::

    from scripts.integration_adapters import get_document_converter, get_ai_client

    # Document conversion
    converter = get_document_converter()
    converter.to_pdf("manuscript.md", "book.pdf")
    converter.to_epub("manuscript.md", "book.epub")

    # AI style analysis (privacy-safe: only anonymized data)
    ai = get_ai_client("openai")
    result = ai.analyze_style("anonymized prose excerpt...")
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# Common types
# ============================================================================


@dataclass
class ToolVersion:
    """Parsed version of an external tool."""

    raw: str
    major: int = 0
    minor: int = 0
    patch: int = 0

    def __post_init__(self) -> None:
        """Parse version string into components."""
        parts = self.raw.strip().split(".")
        try:
            self.major = int(parts[0]) if len(parts) > 0 else 0
            self.minor = int(parts[1]) if len(parts) > 1 else 0
            self.patch = int(parts[2]) if len(parts) > 2 else 0
        except ValueError:
            pass

    def satisfies(self, minimum: str, maximum: str | None = None) -> bool:
        """Check if this version is within [minimum, maximum)."""
        min_v = ToolVersion(raw=minimum)
        if (self.major, self.minor, self.patch) < (min_v.major, min_v.minor, min_v.patch):
            return False
        if maximum:
            max_v = ToolVersion(raw=maximum)
            if (self.major, self.minor, self.patch) >= (max_v.major, max_v.minor, max_v.patch):
                return False
        return True


@dataclass
class ConversionResult:
    """Result of a document conversion operation."""

    success: bool
    output_path: str | None = None
    error: str | None = None
    warnings: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class AIResponse:
    """Result from an AI model call."""

    success: bool
    content: str = ""
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    error: str | None = None


# ============================================================================
# Document Converter — Abstract Interface
# ============================================================================


class DocumentConverter(ABC):
    """Abstract interface for document format conversion.

    Concrete implementations can use Pandoc, WeasyPrint, Prince, or any
    other tool. The pipeline code only depends on this interface.
    """

    @abstractmethod
    def check_available(self) -> tuple[bool, str]:
        """Check if the converter is installed and functional.

        Returns:
            (available, message) tuple.
        """

    @abstractmethod
    def get_version(self) -> ToolVersion | None:
        """Return the installed version of the converter."""

    @abstractmethod
    def to_pdf(
        self,
        input_path: str,
        output_path: str,
        *,
        template: str | None = None,
        extra_args: list[str] | None = None,
    ) -> ConversionResult:
        """Convert a markdown file to PDF."""

    @abstractmethod
    def to_epub(
        self,
        input_path: str,
        output_path: str,
        *,
        css: str | None = None,
        metadata: dict[str, Any] | None = None,
        extra_args: list[str] | None = None,
    ) -> ConversionResult:
        """Convert a markdown file to EPUB."""


# ============================================================================
# Pandoc Adapter
# ============================================================================


class PandocConverter(DocumentConverter):
    """Document converter using Pandoc + XeLaTeX.

    Version requirements:
        - Pandoc >= 3.1.0, < 4.0
        - XeLaTeX from TeX Live 2024+ (for PDF output)
    """

    MIN_VERSION = "3.1.0"
    MAX_VERSION = "4.0.0"
    DEFAULT_TIMEOUT = 300  # seconds

    def __init__(self, project_dir: str = ".") -> None:
        self._project_dir = os.path.abspath(project_dir)

    def check_available(self) -> tuple[bool, str]:
        """Check Pandoc and XeLaTeX availability."""
        issues = []

        # Check pandoc
        pandoc_path = shutil.which("pandoc")
        if not pandoc_path:
            issues.append("pandoc not found. Install with: brew install pandoc")
        else:
            version = self.get_version()
            if version and not version.satisfies(self.MIN_VERSION, self.MAX_VERSION):
                issues.append(
                    f"pandoc version {version.raw} outside required range "
                    f"[{self.MIN_VERSION}, {self.MAX_VERSION})"
                )

        # Check xelatex
        xelatex_path = shutil.which("xelatex")
        if not xelatex_path:
            issues.append(
                "xelatex not found. Install with: brew install --cask mactex"
            )

        if issues:
            return False, "; ".join(issues)
        return True, f"pandoc {self.get_version().raw if self.get_version() else '?'}, xelatex available"

    def get_version(self) -> ToolVersion | None:
        """Parse Pandoc version from CLI output."""
        try:
            result = subprocess.run(
                ["pandoc", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                first_line = result.stdout.strip().split("\n")[0]
                # "pandoc 3.1.9" -> "3.1.9"
                version_str = first_line.split()[-1] if first_line else "0.0.0"
                return ToolVersion(raw=version_str)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return None

    def to_pdf(
        self,
        input_path: str,
        output_path: str,
        *,
        template: str | None = None,
        extra_args: list[str] | None = None,
    ) -> ConversionResult:
        """Convert markdown to PDF using Pandoc + XeLaTeX."""
        import time

        start = time.monotonic()

        cmd = [
            "pandoc",
            input_path,
            "-o", output_path,
            "--pdf-engine=xelatex",
            "--toc",
            "--toc-depth=1",
            "--top-level-division=chapter",
            "--number-sections=false",
            "--wrap=auto",
        ]

        if template:
            cmd.extend([f"--template={template}"])
        else:
            default_template = os.path.join(self._project_dir, "templates", "memoir.latex")
            if os.path.isfile(default_template):
                cmd.extend([f"--template={default_template}"])

        cmd.extend([
            "-V", "documentclass=memoir",
            "-V", "classoption=12pt,a5paper,oneside,openany",
        ])

        if extra_args:
            cmd.extend(extra_args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self._project_dir,
                timeout=self.DEFAULT_TIMEOUT,
            )
            elapsed = time.monotonic() - start

            if result.returncode != 0:
                return ConversionResult(
                    success=False,
                    error=result.stderr[:2000],
                    duration_seconds=elapsed,
                )

            warnings = [
                line for line in result.stderr.split("\n")
                if "warning" in line.lower()
            ]

            return ConversionResult(
                success=True,
                output_path=output_path,
                warnings=warnings,
                duration_seconds=elapsed,
            )

        except subprocess.TimeoutExpired:
            return ConversionResult(
                success=False,
                error=f"PDF build timed out after {self.DEFAULT_TIMEOUT}s",
                duration_seconds=self.DEFAULT_TIMEOUT,
            )
        except FileNotFoundError:
            return ConversionResult(
                success=False,
                error="pandoc not found. Install with: brew install pandoc",
            )

    def to_epub(
        self,
        input_path: str,
        output_path: str,
        *,
        css: str | None = None,
        metadata: dict[str, Any] | None = None,
        extra_args: list[str] | None = None,
    ) -> ConversionResult:
        """Convert markdown to EPUB using Pandoc."""
        import time

        start = time.monotonic()

        cmd = [
            "pandoc",
            input_path,
            "-o", output_path,
            "--toc",
            "--toc-depth=1",
            "--top-level-division=chapter",
            "--number-sections=false",
            "--wrap=auto",
            "--epub-chapter-level=1",
        ]

        if css:
            cmd.extend(["--css", css])
        else:
            default_css = os.path.join(self._project_dir, "templates", "epub.css")
            if os.path.isfile(default_css):
                cmd.extend(["--css", default_css])

        if metadata and metadata.get("cover-image"):
            cover = metadata["cover-image"]
            cover_full = os.path.join(self._project_dir, cover)
            if os.path.isfile(cover_full):
                cmd.extend(["--epub-cover-image", cover])

        if extra_args:
            cmd.extend(extra_args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self._project_dir,
                timeout=120,
            )
            elapsed = time.monotonic() - start

            if result.returncode != 0:
                return ConversionResult(
                    success=False,
                    error=result.stderr[:2000],
                    duration_seconds=elapsed,
                )

            return ConversionResult(
                success=True,
                output_path=output_path,
                duration_seconds=elapsed,
            )

        except subprocess.TimeoutExpired:
            return ConversionResult(
                success=False,
                error="EPUB build timed out after 120s",
                duration_seconds=120,
            )
        except FileNotFoundError:
            return ConversionResult(
                success=False,
                error="pandoc not found. Install with: brew install pandoc",
            )


# ============================================================================
# AI Client — Abstract Interface
# ============================================================================


class AIClient(ABC):
    """Abstract interface for AI model interactions.

    Used ONLY for non-sensitive tasks (style analysis, comparative review).
    Raw interview data and PII must NEVER be sent through these clients.
    See privacy-strategy.md for the data classification matrix.
    """

    @abstractmethod
    def check_available(self) -> tuple[bool, str]:
        """Check if the AI service is accessible."""

    @abstractmethod
    def analyze_style(self, text: str, instructions: str = "") -> AIResponse:
        """Analyze writing style of anonymized text."""

    @abstractmethod
    def compare_passages(self, passage_a: str, passage_b: str) -> AIResponse:
        """Compare two anonymized passages for stylistic consistency."""


# ============================================================================
# OpenAI Adapter
# ============================================================================


class OpenAIClient(AIClient):
    """AI client using OpenAI API.

    Requires: OPENAI_API_KEY in Keychain or environment.
    Model: gpt-4o (configurable)
    """

    DEFAULT_MODEL = "gpt-4o"

    def __init__(self, model: str | None = None) -> None:
        self._model = model or self.DEFAULT_MODEL
        self._api_key: str | None = None

    def _get_key(self) -> str | None:
        """Retrieve API key via CredentialManager."""
        if self._api_key:
            return self._api_key
        try:
            from scripts.credential_manager import CredentialManager

            cm = CredentialManager()
            self._api_key = cm.get("openai")
        except ImportError:
            self._api_key = os.environ.get("OPENAI_API_KEY")
        return self._api_key

    def check_available(self) -> tuple[bool, str]:
        """Check OpenAI API availability."""
        key = self._get_key()
        if not key:
            return False, "OpenAI API key not found"

        try:
            import openai

            client = openai.OpenAI(api_key=key)
            # Minimal API call to verify connectivity
            client.models.list()
            return True, f"OpenAI API connected (model: {self._model})"
        except ImportError:
            return False, "openai package not installed. Run: pip install openai"
        except Exception as e:
            return False, f"OpenAI API error: {e}"

    def analyze_style(self, text: str, instructions: str = "") -> AIResponse:
        """Analyze writing style using OpenAI."""
        key = self._get_key()
        if not key:
            return AIResponse(success=False, error="OpenAI API key not found")

        try:
            import openai

            client = openai.OpenAI(api_key=key)

            system_prompt = (
                "You are a literary style analyst. Analyze the writing style of the "
                "following text. Focus on: sentence structure, vocabulary level, "
                "tone, rhythm, use of literary devices, and voice consistency. "
                "Return a structured JSON analysis."
            )
            if instructions:
                system_prompt += f"\n\nAdditional instructions: {instructions}"

            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.3,
                max_tokens=2000,
            )

            choice = response.choices[0]
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            }

            return AIResponse(
                success=True,
                content=choice.message.content or "",
                model=self._model,
                usage=usage,
            )

        except ImportError:
            return AIResponse(success=False, error="openai package not installed")
        except Exception as e:
            return AIResponse(success=False, error=str(e))

    def compare_passages(self, passage_a: str, passage_b: str) -> AIResponse:
        """Compare two passages for voice consistency using OpenAI."""
        key = self._get_key()
        if not key:
            return AIResponse(success=False, error="OpenAI API key not found")

        try:
            import openai

            client = openai.OpenAI(api_key=key)

            prompt = (
                "Compare these two passages for stylistic consistency. "
                "Score from 0-10 and identify specific differences.\n\n"
                f"--- PASSAGE A ---\n{passage_a}\n\n"
                f"--- PASSAGE B ---\n{passage_b}"
            )

            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a literary style consistency analyst. "
                            "Return structured JSON with: consistency_score, "
                            "differences[], similarities[], recommendations[]"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
            )

            choice = response.choices[0]
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            }

            return AIResponse(
                success=True,
                content=choice.message.content or "",
                model=self._model,
                usage=usage,
            )

        except ImportError:
            return AIResponse(success=False, error="openai package not installed")
        except Exception as e:
            return AIResponse(success=False, error=str(e))


# ============================================================================
# Gemini Adapter
# ============================================================================


class GeminiClient(AIClient):
    """AI client using Google Gemini API.

    Requires: GEMINI_API_KEY in Keychain or environment.
    Model: gemini-2.0-flash (configurable)
    """

    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(self, model: str | None = None) -> None:
        self._model = model or self.DEFAULT_MODEL
        self._api_key: str | None = None

    def _get_key(self) -> str | None:
        """Retrieve API key via CredentialManager."""
        if self._api_key:
            return self._api_key
        try:
            from scripts.credential_manager import CredentialManager

            cm = CredentialManager()
            self._api_key = cm.get("gemini")
        except ImportError:
            self._api_key = os.environ.get("GEMINI_API_KEY")
        return self._api_key

    def check_available(self) -> tuple[bool, str]:
        """Check Gemini API availability."""
        key = self._get_key()
        if not key:
            return False, "Gemini API key not found"

        try:
            from google import genai

            client = genai.Client(api_key=key)
            # Minimal call to verify connectivity
            client.models.list()
            return True, f"Gemini API connected (model: {self._model})"
        except ImportError:
            return False, "google-genai package not installed. Run: pip install google-genai"
        except Exception as e:
            return False, f"Gemini API error: {e}"

    def analyze_style(self, text: str, instructions: str = "") -> AIResponse:
        """Analyze writing style using Gemini."""
        key = self._get_key()
        if not key:
            return AIResponse(success=False, error="Gemini API key not found")

        try:
            from google import genai

            client = genai.Client(api_key=key)

            prompt = (
                "You are a literary style analyst. Analyze the writing style of the "
                "following text. Focus on: sentence structure, vocabulary level, "
                "tone, rhythm, use of literary devices, and voice consistency. "
                "Return a structured JSON analysis.\n\n"
            )
            if instructions:
                prompt += f"Additional instructions: {instructions}\n\n"
            prompt += f"Text to analyze:\n{text}"

            response = client.models.generate_content(
                model=self._model,
                contents=prompt,
            )

            return AIResponse(
                success=True,
                content=response.text or "",
                model=self._model,
                usage={
                    "prompt_tokens": getattr(
                        getattr(response, "usage_metadata", None), "prompt_token_count", 0
                    )
                    or 0,
                    "completion_tokens": getattr(
                        getattr(response, "usage_metadata", None), "candidates_token_count", 0
                    )
                    or 0,
                },
            )

        except ImportError:
            return AIResponse(
                success=False, error="google-genai package not installed"
            )
        except Exception as e:
            return AIResponse(success=False, error=str(e))

    def compare_passages(self, passage_a: str, passage_b: str) -> AIResponse:
        """Compare two passages using Gemini."""
        key = self._get_key()
        if not key:
            return AIResponse(success=False, error="Gemini API key not found")

        try:
            from google import genai

            client = genai.Client(api_key=key)

            prompt = (
                "You are a literary style consistency analyst. "
                "Compare these two passages for stylistic consistency. "
                "Return structured JSON with: consistency_score (0-10), "
                "differences[], similarities[], recommendations[]\n\n"
                f"--- PASSAGE A ---\n{passage_a}\n\n"
                f"--- PASSAGE B ---\n{passage_b}"
            )

            response = client.models.generate_content(
                model=self._model,
                contents=prompt,
            )

            return AIResponse(
                success=True,
                content=response.text or "",
                model=self._model,
            )

        except ImportError:
            return AIResponse(
                success=False, error="google-genai package not installed"
            )
        except Exception as e:
            return AIResponse(success=False, error=str(e))


# ============================================================================
# Factory Functions
# ============================================================================


def get_document_converter(
    backend: str = "pandoc",
    project_dir: str = ".",
) -> DocumentConverter:
    """Create a DocumentConverter instance.

    Args:
        backend: Which converter to use. Currently only "pandoc" is supported.
        project_dir: Project root directory for locating templates.

    Returns:
        A DocumentConverter instance.

    Raises:
        ValueError: If the backend is unknown.
    """
    backends: dict[str, type[DocumentConverter]] = {
        "pandoc": PandocConverter,
    }

    if backend not in backends:
        msg = f"Unknown converter backend '{backend}'. Available: {list(backends.keys())}"
        raise ValueError(msg)

    return backends[backend](project_dir=project_dir)


def get_ai_client(
    provider: str,
    model: str | None = None,
) -> AIClient:
    """Create an AIClient instance.

    Args:
        provider: Which AI provider ("openai" or "gemini").
        model: Override the default model for the provider.

    Returns:
        An AIClient instance.

    Raises:
        ValueError: If the provider is unknown.
    """
    providers: dict[str, type[AIClient]] = {
        "openai": OpenAIClient,
        "gemini": GeminiClient,
    }

    if provider not in providers:
        msg = f"Unknown AI provider '{provider}'. Available: {list(providers.keys())}"
        raise ValueError(msg)

    return providers[provider](model=model)


# ============================================================================
# CLI — quick check
# ============================================================================


def main() -> None:
    """Print availability status of all adapters."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=== Integration Adapter Status ===\n")

    # Document converter
    converter = get_document_converter()
    available, msg = converter.check_available()
    status = "OK" if available else "FAIL"
    print(f"  [{status}] Document Converter (Pandoc): {msg}")

    version = converter.get_version()
    if version:
        print(f"         Version: {version.raw}")

    # AI clients
    for provider in ("openai", "gemini"):
        try:
            client = get_ai_client(provider)
            available, msg = client.check_available()
            status = "OK" if available else "FAIL"
            print(f"  [{status}] AI Client ({provider}): {msg}")
        except Exception as e:
            print(f"  [FAIL] AI Client ({provider}): {e}")

    print()


if __name__ == "__main__":
    main()
