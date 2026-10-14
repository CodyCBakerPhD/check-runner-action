import json
import pathlib
import re
import subprocess

import pytest
import yaml

_REPOSITORY_ROOT = pathlib.Path(__file__).parent.parent
_ACTION_PATH = _REPOSITORY_ROOT / "action.yml"
_SCRIPT_PATH = _REPOSITORY_ROOT / "check_runner.sh"
_README_PATH = _REPOSITORY_ROOT / "README.md"
_VERSION_PATH = _REPOSITORY_ROOT / "VERSION"
_ANY_SELF_REFERENCE_PATTERN = re.compile(r"CodyCBakerPhD/check-runner-action@([\w.-]+)")

# The tag this tree is meant to be published under. Every reference to this repository must name it,
# and the release workflow takes the tag from it.
_MAJOR_TAG = _VERSION_PATH.read_text(encoding="utf-8").strip()

# Stands in for the GitHub CLI: records its arguments and prints a canned response, one page per line.
_GH_STUB = """#!/bin/bash
echo "$@" >> "$GH_STUB_LOG"
[ "${GH_STUB_EXIT:-0}" -eq 0 ] || exit "$GH_STUB_EXIT"
cat "$GH_STUB_RESPONSE"
"""


def _action() -> dict:
    return yaml.safe_load(_ACTION_PATH.read_text(encoding="utf-8"))


def _runner(*labels: str, status: str = "online") -> dict:
    return {"status": status, "labels": [{"name": label} for label in labels]}


def _check(
    tmp_path: pathlib.Path, scope: str, labels: str, pages: list[list[dict]], exit_code: int = 0,
) -> subprocess.CompletedProcess:
    stub_directory = tmp_path / "bin"
    stub_directory.mkdir()
    stub_path = stub_directory / "gh"
    stub_path.write_text(_GH_STUB, encoding="utf-8")
    stub_path.chmod(0o755)
    response_path = tmp_path / "response.json"
    response_path.write_text(
        "".join(json.dumps({"total_count": len(page), "runners": page}) for page in pages), encoding="utf-8",
    )

    environment = {
        "PATH": f"{stub_directory}:/usr/bin:/bin",
        "GH_STUB_LOG": str(tmp_path / "gh.log"),
        "GH_STUB_RESPONSE": str(response_path),
        "GH_STUB_EXIT": str(exit_code),
    }
    return subprocess.run(  # noqa: S603
        ["/bin/bash", str(_SCRIPT_PATH), scope, labels],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )


@pytest.mark.ai_generated
def test_online_runner_with_every_label_is_found(tmp_path: pathlib.Path) -> None:
    result = _check(tmp_path, "owner/repo", "typhon,dandi", [[_runner("self-hosted", "typhon", "dandi")]])

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "true"


@pytest.mark.ai_generated
def test_offline_runner_is_not_found(tmp_path: pathlib.Path) -> None:
    result = _check(tmp_path, "owner/repo", "typhon,dandi", [[_runner("typhon", "dandi", status="offline")]])

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "false"


@pytest.mark.ai_generated
def test_runner_missing_a_label_is_not_found(tmp_path: pathlib.Path) -> None:
    result = _check(tmp_path, "owner/repo", "typhon,dandi", [[_runner("typhon", "ember")]])

    assert result.stdout.strip() == "false"


@pytest.mark.ai_generated
def test_labels_must_match_whole(tmp_path: pathlib.Path) -> None:
    """A label is never satisfied by a longer one that contains it."""
    result = _check(tmp_path, "owner/repo", "typhon,dandi", [[_runner("typhon", "dandi-old")]])

    assert result.stdout.strip() == "false"


@pytest.mark.ai_generated
def test_spaces_around_labels_are_ignored(tmp_path: pathlib.Path) -> None:
    result = _check(tmp_path, "owner/repo", "typhon, dandi", [[_runner("typhon", "dandi")]])

    assert result.stdout.strip() == "true"


@pytest.mark.ai_generated
def test_runner_on_a_later_page_is_found(tmp_path: pathlib.Path) -> None:
    pages = [[_runner("typhon", "ember")], [_runner("typhon", "dandi")]]
    result = _check(tmp_path, "my-organization", "typhon,dandi", pages)

    assert result.stdout.strip() == "true"
    assert "--paginate" in (tmp_path / "gh.log").read_text(encoding="utf-8")


@pytest.mark.ai_generated
@pytest.mark.parametrize(
    ("scope", "endpoint"),
    [("owner/repo", "repos/owner/repo/actions/runners"), ("my-organization", "orgs/my-organization/actions/runners")],
)
def test_scope_selects_the_endpoint(tmp_path: pathlib.Path, scope: str, endpoint: str) -> None:
    _check(tmp_path, scope, "typhon", [[]])

    assert (tmp_path / "gh.log").read_text(encoding="utf-8").split() == ["api", "--paginate", endpoint]


@pytest.mark.ai_generated
def test_failed_listing_is_an_error_rather_than_offline(tmp_path: pathlib.Path) -> None:
    result = _check(tmp_path, "owner/repo", "typhon", [[_runner("typhon")]], exit_code=1)

    assert result.returncode != 0
    assert result.stdout.strip() == ""


@pytest.mark.ai_generated
def test_missing_arguments_are_a_usage_error(tmp_path: pathlib.Path) -> None:
    result = _check(tmp_path, "owner/repo", "", [[]])

    assert result.returncode == 2  # noqa: PLR2004


@pytest.mark.ai_generated
def test_action_is_composite_with_a_default_for_every_optional_input() -> None:
    action = _action()

    assert action["runs"]["using"] == "composite"
    for name, specification in action["inputs"].items():
        assert specification["required"] is True or "default" in specification, name


@pytest.mark.ai_generated
def test_scope_defaults_to_the_calling_repository() -> None:
    """Runners registered to the repository need no `scope`, which is the common case."""
    assert _action()["inputs"]["scope"]["default"] == "${{ github.repository }}"


@pytest.mark.ai_generated
def test_action_keeps_expressions_out_of_run_bodies() -> None:
    """
    Inputs reach `run:` bodies through `env:`.

    Interpolating an input into a `run:` body lets its value rewrite the script, and would place the token in the
    command GitHub echoes.
    """
    for step in _action()["runs"]["steps"]:
        assert "${{" not in step.get("run", ""), step["name"]


@pytest.mark.ai_generated
def test_token_reaches_the_cli_as_gh_token() -> None:
    (step,) = _action()["runs"]["steps"]

    assert step["env"]["GH_TOKEN"] == "${{ inputs.token }}"  # noqa: S105


@pytest.mark.ai_generated
def test_action_runs_the_script_it_ships() -> None:
    (step,) = _action()["runs"]["steps"]

    assert f'"$GITHUB_ACTION_PATH/{_SCRIPT_PATH.name}"' in step["run"]


@pytest.mark.ai_generated
def test_every_self_reference_names_the_version_being_published() -> None:
    """
    Nothing in the repository may point at a tag other than the one `VERSION` names.

    A reference left on the previous tag resolves and runs, so neither a workflow run nor a test of the
    files against each other catches it.
    """
    references = set(_ANY_SELF_REFERENCE_PATTERN.findall(_README_PATH.read_text(encoding="utf-8")))

    assert references == {_MAJOR_TAG}


@pytest.mark.ai_generated
def test_readme_documents_every_input() -> None:
    readme = _README_PATH.read_text(encoding="utf-8")

    for name in _action()["inputs"]:
        assert f"| `{name}` |" in readme, name


@pytest.mark.ai_generated
def test_version_file_names_a_major_tag() -> None:
    """`VERSION` is compared against the release tag, so it has to be shaped like one."""
    assert re.fullmatch(r"v\d+", _MAJOR_TAG) is not None, _MAJOR_TAG
