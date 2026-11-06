"""Shared runtime for the GPU creative engine.

One place that knows how to: reach the AWS GPU box over SSM, run shell there,
push/pull files via S3, and ask the MusicGen box for a track. Everything else
(cartoon / doodle / presenter) builds on this so there is exactly one AWS
footprint and one place credentials live.

No third-party creative APIs. Compute runs on our own EC2 GPU; the only AWS
services touched are SSM (run commands), S3 (file shuttle) and the boxes
themselves.
"""
import base64
import os
import time

import boto3

REGION = os.environ.get("PRIV_GPU_REGION", "us-east-1")

# --- the fleet -------------------------------------------------------------
# Video/avatar box (A10G, 23GB) -- cartoon, doodle, presenter all render here.
GPU_INSTANCE = os.environ.get("PRIV_GPU_INSTANCE", "i-0f5aaebf6d440da5c")
GPU_PY = os.environ.get("PRIV_GPU_PY", "/opt/pytorch/bin/python")
# MuseTalk runs in its own Python 3.11 venv -- it pins numpy 1.23 / tensorflow
# 2.12 and mmpose won't build on the box's bleeding-edge Python 3.13.
GPU_MUSETALK_PY = os.environ.get("PRIV_GPU_MUSETALK_PY",
                                 "/opt/priv/venv-musetalk/bin/python")
GPU_WORK = os.environ.get("PRIV_GPU_WORK", "/opt/priv/work")

# Music box (T4) -- already serving MusicGen in a docker container on :8080.
# The GPU box must reach it over the PRIVATE IP: the shared security group only
# opens :8080 to the VPC CIDR, so the public IP times out. Resolved dynamically
# (instance id) so it survives instance replacement; PRIV_MUSIC_HOST overrides.
MUSIC_INSTANCE = os.environ.get("PRIV_MUSIC_INSTANCE", "i-085cf8321ddb43e94")
MUSIC_PORT = int(os.environ.get("PRIV_MUSIC_PORT", "8080"))


def _music_host():
    """Private IP of the music box (dynamic; falls back to the env/known IP)."""
    if os.environ.get("PRIV_MUSIC_HOST"):
        return os.environ["PRIV_MUSIC_HOST"]
    try:
        ec2 = boto3.client("ec2", region_name=REGION)
        r = ec2.describe_instances(InstanceIds=[MUSIC_INSTANCE])
        ip = r["Reservations"][0]["Instances"][0].get("PrivateIpAddress")
        if ip:
            return ip
    except Exception:
        pass
    return "172.31.0.142"

# File shuttle bucket. The GPU box's role can write here and our local
# credentials can read; probed live -- the Lambda bucket is NOT writable by
# the box, so do not point this back at pr-growth-agent.
BUCKET = os.environ.get("PRIV_GPU_BUCKET", "sans-mercantile-mezzo-embodiment")
PREFIX = os.environ.get("PRIV_GPU_PREFIX", "creative")

MODELS = "/opt/priv/models"


def _ssm():
    return boto3.client("ssm", region_name=REGION)


def _s3():
    return boto3.client("s3", region_name=REGION)


def _transient(exc):
    """True for the intermittent AWS network failures this host hits: DNS
    resolution blips and dropped connections to SSM/S3 endpoints. Retrying
    these is correct; only a genuine failure should abort a render."""
    s = str(exc).lower()
    return any(k in s for k in (
        "getaddrinfo failed", "name or service not known", "endpointconnectionerror",
        "connection was closed", "connect timeout", "read timeout", "timed out",
        "connection aborted", "remote end closed connection",
    ))


def run(cmd, timeout=600, poll=5, retries=12):
    """Run a shell command on the GPU box; return (status, stdout, stderr).

    Retries transient AWS network failures (this host drops to us-east-1
    intermittently, sometimes for a minute or two) instead of aborting a long
    render on a momentary blip. The backoff rides out those outages.
    """
    last = None
    for attempt in range(retries + 1):
        try:
            r = _ssm().send_command(InstanceIds=[GPU_INSTANCE],
                                    DocumentName="AWS-RunShellScript",
                                    Parameters={"commands": [cmd]},
                                    TimeoutSeconds=timeout)
            cid = r["Command"]["CommandId"]
            deadline = time.time() + timeout
            while time.time() < deadline:
                time.sleep(poll)
                out = _ssm().get_command_invocation(CommandId=cid, InstanceId=GPU_INSTANCE)
                if out["Status"] not in ("Pending", "InProgress", "Delayed"):
                    return out["Status"], out.get("StandardOutputContent", ""), \
                        out.get("StandardErrorContent", "")
            return "TimedOut", "", f"command exceeded {timeout}s"
        except Exception as e:                    # noqa: BLE001
            last = e
            if not _transient(e) or attempt == retries:
                raise
            wait = min(8 * (attempt + 1), 45)
            print(f"  [net] transient AWS failure, retry {attempt + 1}/{retries} "
                  f"in {wait}s...")
            time.sleep(wait)
    raise last


def run_checked(cmd, timeout=600, poll=5, log=print):
    status, out, err = run(cmd, timeout=timeout, poll=poll)
    if status != "Success":
        tail = (err or out)[-1500:]
        raise RuntimeError(f"GPU command failed ({status}):\n{tail}")
    if log and out.strip():
        log(out.strip()[-1500:])
    return out


def b64(text):
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def write_file(path, text):
    """Write a local-text file to an absolute path on the GPU box."""
    return run(f"mkdir -p {os.path.dirname(path)} && "
               f"echo '{b64(text)}' | base64 -d > {path}")


def push(local_path, key, content_type=None):
    extra = {}
    if content_type:
        extra["ContentType"] = content_type
    for attempt in range(13):
        try:
            _s3().upload_file(local_path, BUCKET, key, ExtraArgs=extra)
            return f"s3://{BUCKET}/{key}"
        except Exception as e:                    # noqa: BLE001
            if not _transient(e) or attempt == 12:
                raise
            time.sleep(min(8 * (attempt + 1), 45))


def pull(key, local_path):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    for attempt in range(13):
        try:
            _s3().download_file(BUCKET, key, local_path)
            return local_path
        except Exception as e:                    # noqa: BLE001
            if not _transient(e) or attempt == 12:
                raise
            time.sleep(min(8 * (attempt + 1), 45))


def stage_up(local_path, name):
    """Local file -> S3 -> box. Returns the path on the box."""
    key = f"{PREFIX}/in/{name}"
    push(local_path, key)
    dest = f"{GPU_WORK}/in/{name}"
    run_checked(f"mkdir -p {os.path.dirname(dest)} && "
                f"aws s3 cp s3://{BUCKET}/{key} {dest}", log=None)
    return dest


def stage_down(box_path, name, local_path):
    """Box file -> S3 -> local. Returns the local path."""
    key = f"{PREFIX}/out/{name}"
    run_checked(f"aws s3 cp {box_path} s3://{BUCKET}/{key}", log=None)
    return pull(key, local_path)


def presign(key, expires=86400):
    return _s3().generate_presigned_url(
        "get_object", Params={"Bucket": BUCKET, "Key": key},
        ExpiresIn=expires)


def public_url(key):
    """HTTPS URL if the object is public; else a 24h presigned URL."""
    try:
        _s3().get_object_acl(Bucket=BUCKET, Key=key)
        return f"https://{BUCKET}.s3.amazonaws.com/{key}"
    except Exception:
        return presign(key)


def music(prompt, seconds, out_wav):
    """Ask the MusicGen box for a track. Returns the local wav path.

    The box is a SageMaker-style TorchServe endpoint (crazyjam-musicgen-large)
    on the musicgen-dedicated T4. It serves `POST /invocations` with
    `{"prompt","duration_seconds",...}` and returns raw WAV bytes. It is not
    reachable from off-box, so we proxy the request through an SSM command on
    the GPU video box (same VPC) and pull the WAV back via S3.

    Generation takes ~4s per second of audio on the T4, so we budget
    accordingly.
    """
    seconds = max(1, int(seconds))
    host = _music_host()
    key = f"{PREFIX}/music/{os.path.basename(out_wav)}"
    box_out = f"{GPU_WORK}/music/{os.path.basename(out_wav)}"
    body = base64.b64encode(
        __import__("json").dumps({
            "prompt": prompt,
            "duration_seconds": seconds,
            "guidance_scale": 3,
            "do_sample": True,
        }).encode()
    ).decode("ascii")
    cmd = (
        f"mkdir -p {GPU_WORK}/music && "
        f"echo '{body}' | base64 -d > /tmp/mq.json && "
        f"curl -s -X POST http://{host}:{MUSIC_PORT}/invocations "
        f"-H 'Content-Type: application/json' --data-binary @/tmp/mq.json "
        f"--output {box_out} --max-time {seconds * 6 + 120} && "
        f"aws s3 cp {box_out} s3://{BUCKET}/{key}"
    )
    status, out, err = run(cmd, timeout=seconds * 6 + 150)
    if status != "Success":
        raise RuntimeError(f"music generation failed: {err or out}")
    return pull(key, out_wav)
