import json
import re
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

REQUIRED = [
    ".hermes/autoforge/app_spec.md",
    ".hermes/autoforge/system_view.md",
    ".hermes/autoforge/design_reference.md",
    ".hermes/autoforge/visual_parity_checklist.md",
    ".hermes/autoforge/features.yaml",
    ".hermes/autoforge/review_policy.md",
    ".hermes/autoforge/worker_prompt.md",
    ".hermes/autoforge/approval.json",
    ".hermes/autoforge/status.json",
]

REQUIRED_APPROVAL_FLAGS = [
    "spec_approved",
    "design_reference_approved",
    "kanban_imported",
    "implementation_allowed",
]

REQUIRED_APP_SPEC_SECTIONS = [
    "Project name",
    "Product goal",
    "Target users",
    "Core user journeys",
    "Pages/screens/routes",
    "Data model and persistence",
    "Authentication, privacy, and permissions",
    "Integrations",
    "Design direction",
    "Non-goals",
    "Success criteria",
]

REQUIRED_SYSTEM_VIEW_SECTIONS = [
    "System boundary",
    "Main elements",
    "Component diagram",
    "Data flow",
    "Integration points",
    "Architectural constraints",
]


def load_yaml(path: Path):
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text)
    # Sample-contract fallback: enough for the repository examples when PyYAML
    # is unavailable, not a general YAML parser.
    features = []
    current = None
    in_depends_on = False
    in_acceptance = False
    in_verification = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- id:"):
            current = {"id": stripped.split(":", 1)[1].strip(), "depends_on": [], "acceptance": [], "verification": []}
            features.append(current)
            in_depends_on = in_acceptance = in_verification = False
        elif current and stripped.startswith("title:"):
            current["title"] = stripped.split(":", 1)[1].strip()
        elif current and stripped.startswith("depends_on:"):
            in_depends_on, in_acceptance, in_verification = True, False, False
        elif current and stripped.startswith("acceptance:"):
            in_depends_on, in_acceptance, in_verification = False, True, False
        elif current and stripped.startswith("verification:"):
            in_depends_on, in_acceptance, in_verification = False, False, True
        elif current and stripped.startswith("- "):
            value = stripped[2:].strip()
            if in_depends_on:
                current["depends_on"].append(value)
            elif in_acceptance:
                current["acceptance"].append(value)
            elif in_verification:
                current["verification"].append(value)
    return {"features": features}


def fail(lines: list[str]) -> int:
    print("FAIL")
    for line in lines:
        print(" -", line)
    return 1


def dependency_cycle_errors(features) -> list[str]:
    graph = {f.get("id"): list(f.get("depends_on") or []) for f in features if f.get("id")}
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []
    cycles: list[str] = []

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            start = stack.index(node) if node in stack else 0
            cycles.append("dependency cycle: " + " -> ".join(stack[start:] + [node]))
            return
        visiting.add(node)
        stack.append(node)
        for dep in graph.get(node, []):
            if dep in graph:
                visit(dep)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    return cycles


def feature_list_errors(features) -> list[str]:
    errors: list[str] = []
    ids = [f.get("id") for f in features]
    if len(ids) != len(set(ids)):
        errors.append("duplicate feature ids")
    id_set = set(ids)
    for f in features:
        fid = f.get("id") or "<missing id>"
        if not f.get("title"):
            errors.append(f"{fid} has no title")
        if not f.get("acceptance"):
            errors.append(f"{fid} has no acceptance criteria")
        if not f.get("verification"):
            errors.append(f"{fid} has no verification steps")
        for dep in f.get("depends_on") or []:
            if dep not in id_set:
                errors.append(f"{fid} depends on unknown dependency {dep}")
    errors.extend(dependency_cycle_errors(features))
    return errors


def app_spec_errors(path: Path) -> list[str]:
    return markdown_heading_errors(path, REQUIRED_APP_SPEC_SECTIONS, "app_spec.md")


def system_view_errors(path: Path) -> list[str]:
    errors = markdown_heading_errors(path, REQUIRED_SYSTEM_VIEW_SECTIONS, "system_view.md")
    text = path.read_text(encoding="utf-8")
    mermaid_blocks = re.findall(r"```mermaid\s*(.*?)```", text, flags=re.DOTALL)
    if not mermaid_blocks:
        errors.append("system_view.md must include at least one Mermaid diagram fence")
    if any("==>" in block for block in mermaid_blocks):
        errors.append("system_view.md must use --> arrows, not ==> arrows")
    if not any("classDef" in block for block in mermaid_blocks):
        errors.append("system_view.md Mermaid diagrams must include classDef style tokens")
    return errors


def markdown_heading_errors(path: Path, required_sections: list[str], label: str) -> list[str]:
    text = path.read_text(encoding="utf-8")
    headings = {
        match.group(1).strip().lower()
        for match in re.finditer(r"^#{1,6}\s+(.+?)\s*$", text, flags=re.MULTILINE)
    }
    return [
        f"{label} missing section heading: {section}"
        for section in required_sections
        if section.lower() not in headings
    ]


def status_errors(path: Path, feature_count: int) -> list[str]:
    try:
        status = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"status.json is invalid JSON: {exc}"]
    errors: list[str] = []
    if status.get("status") != "complete":
        errors.append("status.json is not complete")
    if status.get("feature_count") != feature_count:
        errors.append(f"status.json feature_count {status.get('feature_count')!r} does not match {feature_count}")
    files_written = set(status.get("files_written") or [])
    missing_written = sorted(set(REQUIRED) - files_written)
    if missing_written:
        errors.append("status.json files_written missing: " + ", ".join(missing_written))
    return errors




def approval_errors(path: Path) -> list[str]:
    try:
        approval = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"approval.json is invalid JSON: {exc}"]
    errors: list[str] = []
    for flag in REQUIRED_APPROVAL_FLAGS:
        if flag not in approval:
            errors.append(f"approval.json missing {flag}")
        elif not isinstance(approval[flag], bool):
            errors.append(f"approval.json {flag} must be boolean")
    return errors


def design_reference_errors(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for required in ["Approved visual source", "Do not redesign", "Do not simplify visible UI"]:
        if required not in text:
            errors.append(f"design_reference.md must include: {required}")
    return errors


def visual_parity_errors(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8").lower()
    errors: list[str] = []
    for required in ["reference screenshot", "candidate screenshot", "visible differences", "user approval"]:
        if required not in text:
            errors.append(f"visual_parity_checklist.md must require {required}")
    return errors

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    missing = [p for p in REQUIRED if not (root / p).exists()]
    if missing:
        return fail(["missing files:"] + missing)

    features_path = root / ".hermes/autoforge/features.yaml"
    data = load_yaml(features_path) or {}
    features = data.get("features") or []
    if not features:
        return fail(["no features found"])

    errors: list[str] = []
    errors.extend(feature_list_errors(features))
    errors.extend(app_spec_errors(root / ".hermes/autoforge/app_spec.md"))
    errors.extend(system_view_errors(root / ".hermes/autoforge/system_view.md"))
    errors.extend(design_reference_errors(root / ".hermes/autoforge/design_reference.md"))
    errors.extend(visual_parity_errors(root / ".hermes/autoforge/visual_parity_checklist.md"))
    errors.extend(approval_errors(root / ".hermes/autoforge/approval.json"))
    errors.extend(status_errors(root / ".hermes/autoforge/status.json", len(features)))
    if errors:
        return fail(errors)

    print(f"PASS {root} has {len(features)} AutoForge-style features and valid dependencies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
