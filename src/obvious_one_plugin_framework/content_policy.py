"""Exact content-policy resolution and canonical file writing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .contract import ContentRule, DistributionContract


class ContentPolicyError(ValueError):
    """Raised when content cannot be classified or canonicalized safely."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code if not detail else f"{code}: {detail}")
        self.code = code


@dataclass(frozen=True)
class ResolvedContentPolicy:
    path: str
    classification: str
    canonicalization: str
    rule_id: str


def resolve_content_policies(
    contract: DistributionContract,
    paths: tuple[str, ...] | list[str],
) -> Mapping[str, ResolvedContentPolicy]:
    """Resolve exactly one application-owned rule for every relative path."""

    ordered = tuple(sorted(paths))
    casefolded: dict[str, str] = {}
    for relative in ordered:
        previous = casefolded.setdefault(relative.casefold(), relative)
        if previous != relative:
            raise ContentPolicyError(
                "casefold_path_collision",
                f"{previous}, {relative}",
            )

    resolved: dict[str, ResolvedContentPolicy] = {}
    unclassified: list[str] = []
    for relative in ordered:
        matches = [rule for rule in contract.content_rules if _matches(rule, relative)]
        if not matches:
            unclassified.append(relative)
            continue
        if len(matches) != 1:
            raise ContentPolicyError("ambiguous_file_classification", relative)
        rule = matches[0]
        resolved[relative] = ResolvedContentPolicy(
            path=relative,
            classification=rule.classification,
            canonicalization="utf8-lf" if rule.classification == "text" else "exact",
            rule_id=rule.rule_id,
        )
    if unclassified:
        raise ContentPolicyError("unclassified_files", ", ".join(unclassified))
    return resolved


def write_canonical_file(
    source: Path,
    destination: Path,
    policy: ResolvedContentPolicy,
) -> None:
    """Write a file using the resolved deterministic byte policy."""

    raw = source.read_bytes()
    if policy.classification == "binary":
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        return
    if policy.classification not in {"text", "framework-runtime"}:
        raise ContentPolicyError("unsupported_content_classification", policy.classification)
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ContentPolicyError("text_bom_forbidden", policy.path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContentPolicyError("text_invalid_utf8", policy.path) from exc
    canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(canonical)


def _matches(rule: ContentRule, relative: str) -> bool:
    return relative in rule.paths or any(
        relative.startswith(prefix.rstrip("/") + "/") for prefix in rule.prefixes
    )
