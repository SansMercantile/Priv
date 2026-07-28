unit_path = "/etc/systemd/system/priv-backend.service"
lines = open("/tmp/whatsapp_env_lines.txt").read().strip().split("\n")
content = open(unit_path).read()

if "WHATSAPP_ACCESS_TOKEN" in content:
    print("ALREADY_PRESENT_SKIPPING")
else:
    marker = "Environment=DERIV_ACCOUNT_TYPE="
    idx = content.index(marker)
    end = content.index("\n", idx) + 1
    new_env_lines = "".join("Environment=" + l + "\n" for l in lines if l.strip())
    content = content[:end] + new_env_lines + content[end:]
    with open(unit_path, "w") as f:
        f.write(content)
    print("UNIT_PATCHED")
