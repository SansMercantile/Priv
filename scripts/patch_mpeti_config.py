p1 = "/home/mpeti/workspace/constellation/mpeti/core/config.py"
with open(p1, "r", encoding="utf-8") as f:
    lines = f.readlines()

out = []
found_compute_backend = False
found_bedrock_model = False
found_llm_provider = False
for line in lines:
    if "COMPUTE_BACKEND: ComputeBackend = ComputeBackend.GCP_CLOUD_RUN" in line:
        line = line.replace(
            "COMPUTE_BACKEND: ComputeBackend = ComputeBackend.GCP_CLOUD_RUN",
            "COMPUTE_BACKEND: ComputeBackend = ComputeBackend.AWS_BEDROCK",
        )
        found_compute_backend = True
    if 'AWS_BEDROCK_MODEL_ID:   Optional[str] = None' in line:
        line = line.replace(
            'AWS_BEDROCK_MODEL_ID:   Optional[str] = None',
            'AWS_BEDROCK_MODEL_ID:   Optional[str] = "us.anthropic.claude-sonnet-5"',
        )
        found_bedrock_model = True
    if 'LLM_DEFAULT_PROVIDER: str = "vertex"' in line:
        line = line.replace(
            'LLM_DEFAULT_PROVIDER: str = "vertex"',
            'LLM_DEFAULT_PROVIDER: str = "bedrock"',
        )
        found_llm_provider = True
    out.append(line)

if not (found_compute_backend and found_bedrock_model and found_llm_provider):
    raise SystemExit(
        f"CONFIG_PATCH_INCOMPLETE backend={found_compute_backend} "
        f"model={found_bedrock_model} provider={found_llm_provider}"
    )

with open(p1, "w", encoding="utf-8") as f:
    f.writelines(out)
print("CONFIG_PATCH_OK")

# --- keep the BedrockProvider's own internal fallback default in sync ---
p2 = "/home/mpeti/workspace/constellation/mpeti/llm_client_wrapper.py"
with open(p2, "r", encoding="utf-8") as f:
    content2 = f.read()

old = '''self.model_id = config.get("model_id", "us.anthropic.claude-sonnet-4-6")'''
new = '''self.model_id = config.get("model_id", "us.anthropic.claude-sonnet-5")'''
if old not in content2:
    raise SystemExit("WRAPPER_PATCH_MARKER_NOT_FOUND")
content2 = content2.replace(old, new, 1)
with open(p2, "w", encoding="utf-8") as f:
    f.write(content2)
print("WRAPPER_PATCH_OK")

# --- keep the test in sync so it reflects the intended default, not a stale one ---
p3 = "/home/mpeti/workspace/constellation/mpeti/tests/unit_core/test_bedrock_defaults.py"
with open(p3, "r", encoding="utf-8") as f:
    content3 = f.read()

old3 = 'assert settings.AWS_BEDROCK_MODEL_ID == "us.anthropic.claude-sonnet-4-6"'
new3 = 'assert settings.AWS_BEDROCK_MODEL_ID == "us.anthropic.claude-sonnet-5"'
if old3 not in content3:
    raise SystemExit("TEST_PATCH_MARKER_NOT_FOUND")
content3 = content3.replace(old3, new3, 1)
with open(p3, "w", encoding="utf-8") as f:
    f.write(content3)
print("TEST_PATCH_OK")
