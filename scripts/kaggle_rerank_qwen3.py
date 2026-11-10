"""Score the frozen item 21 reranker requests with Qwen3-Reranker-0.6B on a GPU notebook.

Run this on Kaggle or Colab with a GPU, not on the project laptop. It reads
reranker_requests.json (development split only, produced by
`python -m scripts.run_reranker_experiment export-requests`) and writes
reranker_results.json, which `import-results` reads. It follows the model card's
transformers usage; the instruction below is fixed before the run and is not tuned.
"""

from __future__ import annotations

import glob
import json
import os
import time

import torch
import transformers
from huggingface_hub import model_info
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
INSTRUCTION = (
    "Given a question about a software repository, retrieve code chunks that answer the question"
)
MAX_LENGTH = 8192
DTYPE = "float16"

_FOUND = glob.glob("/kaggle/input/*/reranker_requests.json") + glob.glob(
    "/content/reranker_requests.json"
)
REQUESTS_PATH = os.environ.get("REQUESTS_PATH") or (_FOUND[0] if _FOUND else "")
OUT_PATH = os.environ.get("OUT_PATH") or (
    "/kaggle/working/reranker_results.json"
    if os.path.isdir("/kaggle/working")
    else "/content/reranker_results.json"
)

PREFIX = (
    "<|im_start|>system\nJudge whether the Document meets the requirements based on the "
    'Query and the Instruct provided. Note that the answer can only be "yes" or "no".'
    "<|im_end|>\n<|im_start|>user\n"
)
SUFFIX = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"


def main() -> None:
    assert torch.cuda.is_available(), "Turn on a GPU in the notebook settings first."
    assert REQUESTS_PATH and os.path.isfile(REQUESTS_PATH), "reranker_requests.json not found"
    with open(REQUESTS_PATH, encoding="utf-8") as handle:
        requests = json.load(handle)
    assert requests.get("format") == "reranker_requests_v1", "unexpected requests format"
    items = requests["items"]

    revision = model_info(MODEL_ID).sha
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=revision, padding_side="left")
    model = (
        AutoModelForCausalLM.from_pretrained(MODEL_ID, revision=revision, torch_dtype=torch.float16)
        .cuda()
        .eval()
    )
    token_false_id = tokenizer.convert_tokens_to_ids("no")
    token_true_id = tokenizer.convert_tokens_to_ids("yes")
    assert isinstance(token_false_id, int) and isinstance(token_true_id, int)
    assert token_false_id != token_true_id
    prefix_tokens = tokenizer.encode(PREFIX, add_special_tokens=False)
    suffix_tokens = tokenizer.encode(SUFFIX, add_special_tokens=False)

    def format_pair(query: str, document: str) -> str:
        return f"<Instruct>: {INSTRUCTION}\n<Query>: {query}\n<Document>: {document}"

    def process_inputs(pairs: list[str]):
        inputs = tokenizer(
            pairs,
            padding=False,
            truncation="longest_first",
            return_attention_mask=False,
            max_length=MAX_LENGTH - len(prefix_tokens) - len(suffix_tokens),
        )
        for index, ids in enumerate(inputs["input_ids"]):
            inputs["input_ids"][index] = prefix_tokens + ids + suffix_tokens
        inputs = tokenizer.pad(inputs, padding=True, return_tensors="pt", max_length=MAX_LENGTH)
        return {key: value.to(model.device) for key, value in inputs.items()}

    @torch.no_grad()
    def score(pairs: list[str]) -> tuple[list[float], int]:
        inputs = process_inputs(pairs)
        logits = model(**inputs).logits[:, -1, :]
        two_way = torch.stack([logits[:, token_false_id], logits[:, token_true_id]], dim=1)
        probabilities = torch.nn.functional.log_softmax(two_way.float(), dim=1)[:, 1].exp()
        return probabilities.tolist(), int(inputs["attention_mask"].sum().item())

    first = items[0]
    score([format_pair(first["query"], text) for text in first["documents"]])  # warm-up, not timed
    torch.cuda.synchronize()

    results = []
    for number, item in enumerate(items, start=1):
        pairs = [format_pair(item["query"], text) for text in item["documents"]]
        torch.cuda.synchronize()
        started = time.perf_counter()
        scores, token_count = score(pairs)
        torch.cuda.synchronize()
        latency_ms = (time.perf_counter() - started) * 1000
        assert len(scores) == len(item["documents"])
        results.append(
            {
                "key": item["key"],
                "scores": scores,
                "latency_ms": round(latency_ms, 3),
                "token_count": token_count,
            }
        )
        if number % 8 == 0 or number == len(items):
            print(f"{number}/{len(items)} questions scored")

    output = {
        "format": "reranker_results_v1",
        "model_identifier": MODEL_ID,
        "model_revision": revision,
        "instruction": INSTRUCTION,
        "max_length": MAX_LENGTH,
        "dtype": DTYPE,
        "batch_size": 20,
        "hardware": torch.cuda.get_device_name(0),
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "requests_candidate_sets_sha256": requests.get("candidate_sets_sha256"),
        "items": results,
    }
    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(output, handle, indent=2)
        handle.write("\n")
    print("wrote", OUT_PATH)


if __name__ == "__main__":
    main()
