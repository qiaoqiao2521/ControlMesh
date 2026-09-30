"""Offline scope/projection checks; no official CLI or account is contacted."""

import copy
import json
from pathlib import Path
import runpy
import subprocess
import sys
from unittest.mock import patch

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/paperclip/lark-cm436"
POLICY_FILTER = 'select((.event.message // .message // .) as $m | ($m.chat_type == "p2p") or ($m.chat_type == "group" and ($m.chat_id == "oc_xxxxxxxxxxxx")))'


def wrapper_args(args):
    with patch.object(sys, "argv", [str(SCRIPT), *args]), patch.object(
        Path, "read_text", return_value=json.dumps({"filter": POLICY_FILTER})
    ), patch("os.execv") as execute:
        runpy.run_path(str(SCRIPT), run_name="lark_cm436_test")
    execute.assert_called_once()
    return execute.call_args.args[1][1:]


@pytest.fixture(scope="module")
def jq_filter():
    args = wrapper_args(["event", "+subscribe", "--compact"])
    assert args[:2] == ["event", "+subscribe"]
    assert "--compact" not in args
    assert args.count("--jq") == 1
    result = args[args.index("--jq") + 1]
    assert POLICY_FILTER in result
    return result


def project(jq_filter, events):
    result = subprocess.run(
        ["jq", "-c", jq_filter],
        input="".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events),
        text=True, capture_output=True, timeout=5,
    )
    assert result.returncode == 0, result.stderr
    return [json.loads(line) for line in result.stdout.splitlines()]


def event(content, message_type="post", chat_type="p2p", location="event"):
    message = {
        "message_type": message_type,
        "chat_type": chat_type,
        "chat_id": "oc_xxxxxxxxxxxx",
        "message_id": "om_offline_fixture",
        "content": content,
        "mentions": [{"key": "@_user_1", "name": "张三", "id": {"open_id": "ou_fixture"}}],
    }
    if location == "event":
        return {"header": {"event_type": "im.message.receive_v1"}, "event": {"message": message, "sender": {"sender_type": "user"}}}
    if location == "message":
        return {"message": message}
    return message


def assert_only_text_added(original, projected, expected):
    assert projected["text"] == expected
    projected_raw = copy.deepcopy(projected)
    if "text" in original:
        projected_raw["text"] = original["text"]
    else:
        projected_raw.pop("text")
    assert projected_raw == original


@pytest.mark.parametrize("as_json", [False, True])
@pytest.mark.parametrize("location", ["event", "message", "root"])
def test_plain_text_string_or_object_at_supported_raw_locations(jq_filter, as_json, location):
    content = {"text": "第一行\n第二行"}
    original = event(json.dumps(content) if as_json else content, "text", location=location)
    output = project(jq_filter, [original])
    assert len(output) == 1
    assert_only_text_added(original, output[0], "第一行\n第二行")


@pytest.mark.parametrize("as_json", [False, True])
@pytest.mark.parametrize("localized", [False, True])
def test_post_title_paragraphs_links_and_mentions(jq_filter, as_json, localized):
    post = {
        "title": "讨论标题",
        "content": [
            [{"tag": "text", "text": "第一段 "}, {"tag": "a", "text": "链接名称", "href": "https://example.invalid/"}],
            [],
            [{"tag": "at", "user_name": "张三", "user_id": "ou_fixture"}, {"tag": "text", "text": " 请看\n内嵌换行"}],
            [{"tag": "at", "text": "@李四", "user_id": "ou_other"}],
            [{"tag": "img", "image_key": "img_fixture"}, {"tag": "text", "text": "图片说明"}],
        ],
    }
    content = {"zh_cn": post, "en_us": {"title": "Do not duplicate", "content": []}} if localized else post
    original = event(json.dumps(content) if as_json else content)
    output = project(jq_filter, [original])
    assert len(output) == 1
    assert_only_text_added(original, output[0], "讨论标题\n第一段 链接名称\n\n@张三 请看\n内嵌换行\n@李四\n图片说明")


def test_real_content_and_content_v2_shape_does_not_duplicate(jq_filter):
    # Captured body shape provided by the coordinating agent, with no account data.
    content = {
        "title": "",
        "content": [[{"tag": "text", "text": "只回复：436迁移验收通过", "style": []}]],
        "content_v2": [[{"tag": "text", "text": "只回复：436迁移验收通过", "style": []}]],
    }
    original = event(json.dumps(content, ensure_ascii=False))
    output = project(jq_filter, [original])
    assert len(output) == 1
    assert_only_text_added(original, output[0], "只回复：436迁移验收通过")


def test_nonempty_root_text_is_preserved_and_projection_is_idempotent(jq_filter):
    original = event({"title": "Different", "content": [[{"tag": "text", "text": "body"}]]})
    original["text"] = "Already extracted\nkeep exactly"
    assert project(jq_filter, [original]) == [original]
    without_text = copy.deepcopy(original)
    without_text.pop("text")
    first = project(jq_filter, [without_text])
    assert project(jq_filter, first) == first


def test_empty_root_text_can_be_filled(jq_filter):
    original = event({"text": "actual text"}, "text")
    original["text"] = ""
    assert_only_text_added(original, project(jq_filter, [original])[0], "actual text")


@pytest.mark.parametrize("message_type,content", [
    ("image", {"text": "Not a text message", "image_key": "img_fixture"}),
    ("interactive", {"title": "Not a supported post", "content": [[{"tag": "text", "text": "do not infer"}]]}),
    ("post", {"content": [[{"tag": "img", "image_key": "img_fixture"}, {"tag": "unknown", "text": "do not infer"}, {"tag": "at", "user_id": "ou_no_visible_name"}]]}),
    ("post", {"content": [[{"tag": "img", "image_key": "img_fixture"}], [{"tag": "unknown", "text": "do not infer"}]]}),
    ("text", "{invalid JSON"),
    ("post", "[]"),
    (None, {"text": "No declared message type"}),
])
def test_unknown_or_malformed_content_does_not_invent_text(jq_filter, message_type, content):
    original = event(content, message_type)
    assert project(jq_filter, [original]) == [original]


def test_msg_type_alias(jq_filter):
    original = event({"title": "", "content": [[{"tag": "text", "text": "mget shape"}]]})
    message = original["event"]["message"]
    message["msg_type"] = message.pop("message_type")
    assert_only_text_added(original, project(jq_filter, [original])[0], "mget shape")


def test_existing_scope_is_unchanged_and_each_allowed_event_emits_once(jq_filter):
    private = event({"text": "private"}, "text")
    allowed = event({"text": "allowed group"}, "text", "group")
    stranger = copy.deepcopy(allowed)
    stranger["event"]["message"]["chat_id"] = "oc_stranger"
    missing_type = copy.deepcopy(private)
    missing_type["event"]["message"].pop("chat_type")
    non_message = {"header": {"event_type": "application.bot.menu_v6"}, "event": {"event_key": "menu"}}
    output = project(jq_filter, [private, allowed, stranger, missing_type, non_message])
    assert len(output) == 2
    assert_only_text_added(private, output[0], "private")
    assert_only_text_added(allowed, output[1], "allowed group")


def test_other_commands_remain_untouched():
    args = ["api", "GET", "/offline", "--compact", "--jq", ".data"]
    assert wrapper_args(args) == args


@pytest.mark.parametrize("flag", ["--jq", "-q"])
def test_subscribe_still_refuses_a_second_filter(flag):
    with pytest.raises(SystemExit, match="filter is already present"):
        wrapper_args(["event", "+subscribe", flag, "."])
