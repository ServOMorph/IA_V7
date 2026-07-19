from ia_v7.services.chat import DELIVERABLE_INSTRUCTION


def test_deliverable_instruction_uses_real_newlines():
    assert "```livrable\n...\n```" in DELIVERABLE_INSTRUCTION
    assert "```livrable\\n...\\n```" not in DELIVERABLE_INSTRUCTION
