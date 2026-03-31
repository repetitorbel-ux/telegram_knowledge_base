from kb_bot.core.topic_parsing import parse_topic_add_command, parse_topic_delete_command, parse_topic_rename_command


def test_parse_topic_add_root_mode() -> None:
    cmd = parse_topic_add_command("/topic_add Learning")
    assert cmd.parent_topic_id is None
    assert cmd.parent_selector is None
    assert cmd.name == "Learning"


def test_parse_topic_add_nested_mode() -> None:
    cmd = parse_topic_add_command("/topic_add 123e4567-e89b-12d3-a456-426614174000 Prompt Engineering")
    assert str(cmd.parent_topic_id) == "123e4567-e89b-12d3-a456-426614174000"
    assert cmd.parent_selector is None
    assert cmd.name == "Prompt Engineering"


def test_parse_topic_add_nested_mode_with_parent_selector() -> None:
    cmd = parse_topic_add_command('/topic_add parent="Neural Networks / AI" Codex')
    assert cmd.parent_topic_id is None
    assert cmd.parent_selector == "Neural Networks / AI"
    assert cmd.name == "Codex"


def test_parse_topic_add_nested_mode_with_arrow_syntax() -> None:
    cmd = parse_topic_add_command('/topic_add "Neural Networks / AI" -> Codex')
    assert cmd.parent_topic_id is None
    assert cmd.parent_selector == "Neural Networks / AI"
    assert cmd.name == "Codex"


def test_parse_topic_rename_command() -> None:
    cmd = parse_topic_rename_command("/topic_rename 123e4567-e89b-12d3-a456-426614174000 AI Core")
    assert str(cmd.topic_id) == "123e4567-e89b-12d3-a456-426614174000"
    assert cmd.new_name == "AI Core"


def test_parse_topic_delete_uuid_command() -> None:
    cmd = parse_topic_delete_command("/topic_delete 123e4567-e89b-12d3-a456-426614174000")
    assert str(cmd.topic_id) == "123e4567-e89b-12d3-a456-426614174000"
    assert cmd.topic_selector is None


def test_parse_topic_delete_selector_command() -> None:
    cmd = parse_topic_delete_command('/topic_delete "Neural Networks / AI.Codex"')
    assert cmd.topic_id is None
    assert cmd.topic_selector == "Neural Networks / AI.Codex"
