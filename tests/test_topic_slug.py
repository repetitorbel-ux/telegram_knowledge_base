from kb_bot.core.topic_slug import slugify_topic_name


def test_slugify_topic_name() -> None:
    assert slugify_topic_name("Neural Networks / AI") == "neural_networks_ai"
    assert slugify_topic_name("  Java  ") == "java"
    assert slugify_topic_name("!!!") == "topic"

