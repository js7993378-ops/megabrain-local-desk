"""judge_client.py — The client every seat uses to reach the judge."""

import os
import requests

URL = os.environ["JUDGE_URL"]
SECRET = os.environ["DESK_SECRET"]


def judge(question_set: str, state: dict) -> dict:
    """One call per token, never one per question."""
    r = requests.post(
        URL,
        timeout=30,
        headers={"Authorization": f"Bearer {SECRET}"},
        json={"question_set": question_set, "state": state}
    )
    if r.status_code == 422:
        raise RuntimeError(f"malformed question: {r.text}")
    r.raise_for_status()
    return r.json()


# Rules baked into those forty lines:
# 1. ONE CALL PER TOKEN, never one per question. State is tokenized once.
# 2. STATE IS A NAMED OBJECT, never a blob. Send only fields the questions read.
# 3. ANSWERS GO BACK RAW. The caller owns the threshold, the judge does not.
# 4. THRESHOLDS settles which. DO NOT TRANSFER between primitives. A choice is relative
#    and a noul is absolute and can be low for all of them.
# 5. LOG THE MODEL ID from the response. Aliases move when a release ships.
# 6. ARITHMETIC STAYS IN CODE. Compute it, pass the result in as a field.
# 7. 401 bad key, 422 bad question, 429 rate limit, 529 overloaded. Back off on 429 and 529.
#    Never retry a 422, the question is wrong and will stay wrong.