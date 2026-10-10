#!/usr/bin/env python3
"""Offline first-run formatter for Agent-reviewed annotations; no source access or writes."""
from __future__ import annotations
import argparse
import json
import re
from urllib.parse import urlsplit

from native_history import reconcile_claims


class ResultError(ValueError):
    pass


IDENTITY = (("name", "称呼"), ("introduction", "简介"),
            ("skills", "技能或经历"), ("resources", "资源与协作"))
LABELS = dict(IDENTITY, current_problem="当前问题", representative_experience="代表性经历", time_resources="可用时间资源")
GAPS = (
    ("current_problem", "说一个你现在最想解决的问题", "帮助助手选准本轮优先问题",
     "口述或粘贴一句话：我现在想解决……，完成时希望看到……"),
    ("representative_experience", "提供一个有代表性的经历或作品片段", "让能力判断有具体依据",
     "口述你做过什么、负责哪部分，或粘贴一段允许整理的作品说明"),
    ("time_resources", "说一下这件事可用的时间和资源", "把建议缩成现在能做的一步",
     "口述或粘贴大致可用时间、已有工具或可求助的人；无需敏感明细"),
)


def nonempty(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ResultError(label + " must be nonempty text")
    return value.strip()


def build_result(data):
    """Validate structure/provenance grade, not raw-text truth or live Page permissions.

    Callers supply already reviewed canonical claims, actual entry status and advice.
    Recommendations never change input claims or become facts.
    """
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        raise ResultError("claims list required")
    for claim in data["claims"]:
        if not isinstance(claim, dict):
            raise ResultError("claim object required")
        nonempty(claim.get("value"), "claim value")
    reconciled = reconcile_claims(data["claims"])
    known = {f["key"]: f for f in reconciled["facts"] if f["status"] == "known"}

    def evidence(key):
        f = known[key]
        current = next(v for v in f["values"] if v["value"] == f["current_value"])
        return {"key": key, "value": f["current_value"],
                "source_ids": list(dict.fromkeys(s["source_id"] for s in current["sources"])),
                "source_notes": list(dict.fromkeys(s["source_id"] + " / " + (
                    "已存记忆摘要" if s["source_kind"] == "memory" else
                    "用户原话" if s["author_role"] == "user" and s["evidence_tier"] == "direct" else
                    "用户自存资料" if s["author_role"] == "user" and s["evidence_tier"] == "saved" else
                    "助手说法" if s["author_role"] == "assistant" else
                    "第三方说法" if s["author_role"] == "third_party" else "摘要或作者未核实资料"
                ) for s in current["sources"]))}

    entry = data.get("entry")
    if not isinstance(entry, dict) or entry.get("status") not in ("verified", "pending", "unavailable"):
        raise ResultError("actual entry status required")
    entry = dict(entry)
    if entry["status"] == "verified":
        url = nonempty(entry.get("url"), "actual root URL")
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password \
                or any(c.isspace() or c in "<>\\[]" for c in url) or parsed.query or parsed.fragment:
            raise ResultError("entry must be a plain HTTPS root URL without credentials/query")
        entry["url"] = url
    else:
        if entry.get("url"):
            raise ResultError("unverified entry cannot present a working root URL")
        entry["reason"] = nonempty(entry.get("reason"), "entry gap")

    supplied = data.get("recommendations", [])
    if not isinstance(supplied, list) or len(supplied) > 3:
        raise ResultError("at most three recommendations")
    actions = []
    for recommendation in supplied:
        if not isinstance(recommendation, dict):
            raise ResultError("recommendation object required")
        keys = recommendation.get("basis_keys")
        if not isinstance(keys, list) or not keys or any(not isinstance(k, str) or k not in known for k in keys):
            raise ResultError("recommendation needs known source-backed basis keys")
        actions.append({"kind": "recommendation", "label": nonempty(recommendation.get("label"), "recommendation"),
                        "basis": [evidence(k) for k in dict.fromkeys(keys)],
                        "first_step": nonempty(recommendation.get("first_step"), "first step"),
                        "confirmation_condition": nonempty(recommendation.get("confirmation_condition"), "confirmation condition")})
    missing = [gap for gap in GAPS if gap[0] not in known]
    # Missing high-value context has priority over extra advice. Total first-round
    # actions stays <=3; do not consume all slots with advice and hide missing inputs.
    reserved = min(3, len(missing))
    actions = actions[:3 - reserved]
    for key, what, why, how in missing[:reserved]:
        actions.append({"kind": "information_action", "key": key, "label": what,
                        "basis": "尚无足够已读依据：" + LABELS[key], "what": what, "why": why,
                        "how": how, "first_step": how,
                        "confirmation_condition": "只整理你愿意提供并允许保存的普通资料"})
    if not actions:
        raise ResultError("known context requires at least one executable recommendation")
    coverage = data.get("coverage_gaps", [])
    if not isinstance(coverage, list) or any(not isinstance(s, str) or not s.strip() for s in coverage):
        raise ResultError("coverage gaps must be text list")
    return {"entry": entry,
            "identity": [{"key": k, "label": label, "fact": evidence(k) if k in known else None} for k, label in IDENTITY],
            "priority": {"kind": "recommendation", "fact": evidence("current_problem") if "current_problem" in known else None},
            "actions": actions, "coverage_gaps": list(coverage),
            "unresolved_keys": list(dict.fromkeys(f["key"] for f in reconciled["facts"] if f["status"] != "known"))}


def literal(text):
    """Render annotations as literal prose, not embedded instructions/Markdown."""
    text = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"([\\`*_{}\[\]()#+.!|~\-])", r"\\\1", " ".join(text.split()))


def cite(fact):
    return literal(fact["value"]) + "（来源：" + "、".join(literal(s) for s in fact["source_notes"]) + "）"


def render_result(result):
    lines = ["# 你是谁＋下一步怎么做", ""]
    entry = result["entry"]
    if entry["status"] == "verified":
        # URL parentheses would break a regular Markdown destination; angle form is safe.
        lines += ["知识库：[打开实际根页](<" + entry["url"] + ">)", ""]
    else:
        lines += ["知识库入口尚未确认：" + literal(entry["reason"]), ""]
    lines += ["## 你是谁", "", "以下为已读来源中的用户自述；未知保留未知。", ""]
    for row in result["identity"]:
        lines.append("- " + row["label"] + "：" + (cite(row["fact"]) if row["fact"] else "未知，尚无足够已读依据"))
    lines += ["", "## 优先问题（建议）", ""]
    priority = result["priority"]["fact"]
    lines.append("建议先围绕这个已知问题行动：" + cite(priority) if priority else
                 "当前最想解决的问题未知；建议先补这一项，再决定具体方案。")
    lines += ["", "## 下一步（建议，不是你的承诺）", ""]
    for number, action in enumerate(result["actions"], 1):
        lines.append(str(number) + ". " + literal(action["label"]))
        basis = "；".join(cite(f) for f in action["basis"]) if isinstance(action["basis"], list) else literal(action["basis"])
        lines += ["   - 依据：" + basis, "   - 第一步：" + literal(action["first_step"]),
                  "   - 需要确认的条件：" + literal(action["confirmation_condition"])]
        if action["kind"] == "information_action":
            lines += ["   - 提供什么：" + literal(action["what"]), "   - 为什么：" + literal(action["why"]),
                      "   - 怎么提供：" + literal(action["how"])]
    lines += ["", "## 覆盖缺口", ""]
    lines += ["- " + literal(s) for s in result["coverage_gaps"]] or ["- 本次未提供覆盖说明，不能推断全量已读。"]
    if result["unresolved_keys"]:
        lines += ["", "仍待核对的摘要、冲突或未确认项：" + "、".join(literal(LABELS.get(k, k)) for k in result["unresolved_keys"])]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="private JSON of reviewed claims, actual entry and advice")
    args = parser.parse_args()
    with open(args.input, encoding="utf-8") as handle:
        data = json.load(handle)
    print(render_result(build_result(data)), end="")


if __name__ == "__main__":
    main()
