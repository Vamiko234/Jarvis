"""Skill behavior against the mock adapter."""

from jarvis.skills import files, productivity, system_control


def test_set_and_get_volume(ctx):
    assert "75%" in system_control.set_volume(75)
    assert system_control.get_volume() == "Volume is at 75%."
    # clamped to range
    system_control.set_volume(500)
    assert ctx.adapter.get_volume() == 100


def test_open_app_records_call(ctx):
    system_control.open_app("notepad")
    assert ("open_app", ("notepad",)) in ctx.adapter.calls


def test_notes_roundtrip(ctx):
    assert productivity.add_note("buy milk") == "Note saved."
    listed = productivity.list_notes()
    assert "buy milk" in listed


def test_get_time(ctx):
    assert productivity.get_time().startswith("It is")


def test_search_and_read_file(ctx, config, tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("hello world", encoding="utf-8")
    assert "hello.txt" in files.search_files("*.txt")
    assert "hello world" in files.read_file(str(f))


def test_read_file_outside_roots_denied(ctx):
    assert "Access denied" in files.read_file("/etc/passwd")
