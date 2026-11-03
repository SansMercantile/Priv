"""Package and deploy the Priv growth agent to AWS.

    python deploy_growth.py            # zip + create/update + schedule
    python deploy_growth.py --no-rule  # skip the EventBridge wiring
    python deploy_growth.py --invoke   # do a dry first run after deploy

Creates/updates:
    Lambda  pr-growth-agent   python3.12  handler=lambda_function.handler
    S3      pr-growth-agent   (ledger + run reports)
    Rule    pr-growth-agent-schedule  rate(12 hours)
"""
import argparse
import datetime
import json
import os
import shutil
import sys
import tempfile
import zipfile

import boto3

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = HERE
FUNCTION = "pr-growth-agent"
BUCKET = "pr-growth-agent"
RULE = "pr-growth-agent-schedule"
ROLE = "arn:aws:iam::363234578752:role/sans-mercantile-clickup-monitor-role"
REGION = os.environ.get("AWS_REGION", "us-east-1")
HANDLER = "lambda_function.handler"
RUNTIME = "python3.12"
SCHEDULE = "rate(12 hours)"

ENV = {
    "DRY_RUN": "false",
    "CH_OWNED": "publish",
    "CH_SOCIAL": "prepare",
    "CH_PAID": "prepare",
    "CH_OUTREACH": "prepare",
    "GROWTH_BUCKET": BUCKET,
    "GROWTH_S3": "auto",
    "GROWTH_PREFIX": "public/growth",
    "GROWTH_BASE_URL": "https://www.sansmercantile.com/growth",
    "GROWTH_LEDGER": "/tmp/growth-ledger.json",
    "GROWTH_PAGES_OUT": "/tmp/growth-pages",
    "GROWTH_OUTBOX": "/tmp/growth-outbox",
}


def build_zip(dest=None):
    dest = dest or os.path.join(tempfile.gettempdir(), f"{FUNCTION}.zip")
    src = os.path.join(BUILD, "growth")
    if not os.path.isdir(src):
        sys.exit(f"missing {src}")
    if os.path.exists(dest):
        os.remove(dest)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _dirs, files in os.walk(src):
            for fn in files:
                if fn.endswith((".pyc", ".pyo")) or fn == "__pycache__":
                    continue
                full = os.path.join(root, fn)
                arc = os.path.relpath(full, BUILD).replace("\\", "/")
                z.write(full, arc)
        z.write(os.path.join(BUILD, "growth", "lambda_function.py"),
                "lambda_function.py")
    size = os.path.getsize(dest)
    print(f"zip: {dest}  ({size/1024:.1f} KB)")
    return dest


def ensure_bucket(s3):
    try:
        s3.head_bucket(Bucket=BUCKET)
        print(f"s3: {BUCKET} exists")
    except Exception:
        kwargs = dict(Bucket=BUCKET)
        if REGION != "us-east-1":
            kwargs["CreateBucketConfiguration"] = {"LocationConstraint": REGION}
        s3.create_bucket(**kwargs)
        s3.put_public_access_block(
            Bucket=BUCKET,
            PublicAccessBlockConfiguration=dict(
                BlockPublicAcls=True, IgnorePublicAcls=True,
                BlockPublicPolicy=True, RestrictPublicBuckets=True))
        print(f"s3: created {BUCKET}")


def deploy_function(zip_path, lam):
    with open(zip_path, "rb") as fh:
        code = fh.read()
    try:
        cfg = lam.get_function_configuration(FunctionName=FUNCTION)
    except lam.exceptions.ResourceNotFoundException:
        cfg = None
    if cfg is None:
        lam.create_function(
            FunctionName=FUNCTION, Runtime=RUNTIME, Role=ROLE, Handler=HANDLER,
            Code={"ZipFile": code}, Timeout=900, MemorySize=512,
            Description="Priv growth agent: create -> launch -> scale (Zeely playbook)",
            Environment={"Variables": ENV},
            Tags={"project": "priv", "component": "growth-agent"})
        print("lambda: created")
    else:
        lam.update_function_code(FunctionName=FUNCTION, ZipFile=code)
        lam.get_waiter("function_updated").wait(FunctionName=FUNCTION)
        lam.update_function_configuration(FunctionName=FUNCTION, Runtime=RUNTIME,
                                          Handler=HANDLER, Timeout=900,
                                          MemorySize=512, Role=ROLE,
                                          Environment={"Variables": ENV})
        lam.get_waiter("function_updated").wait(FunctionName=FUNCTION)
        print("lambda: updated")
    print(f"lambda: {FUNCTION}  {RUNTIME}  {HANDLER}")


def wire_rule(events, lam):
    events.put_rule(Name=RULE, ScheduleExpression=SCHEDULE, State="ENABLED",
                    Description="Priv growth agent create/launch/scale cycle")
    arn = lam.get_function(FunctionName=FUNCTION)["Configuration"]["FunctionArn"]
    events.put_targets(Rule=RULE, Targets=[{
        "Id": "pr-growth-agent", "Arn": arn,
        "Input": json.dumps({"source": "eventbridge", "hydrate": True})}])
    try:
        lam.add_permission(FunctionName=FUNCTION,
                           StatementId=f"{RULE}-invoke",
                           Action="lambda:InvokeFunction",
                           Principal="events.amazonaws.com",
                           SourceArn=f"arn:aws:events:{REGION}:363234578752:rule/{RULE}")
    except lam.exceptions.ResourceConflictException:
        pass
    print(f"rule: {RULE} -> {SCHEDULE} (ENABLED)")


def ensure_role_policy(iam):
    """The shared Lambda role only allows S3 on an unrelated bucket."""
    doc = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow",
             "Action": ["s3:GetObject", "s3:PutObject"],
             "Resource": f"arn:aws:s3:::{BUCKET}/*"},
            {"Effect": "Allow", "Action": ["s3:ListBucket", "s3:HeadBucket"],
             "Resource": f"arn:aws:s3:::{BUCKET}"},
        ],
    }
    iam.put_role_policy(RoleName=ROLE.rsplit("/", 1)[-1],
                        PolicyName="growth-agent-s3",
                        PolicyDocument=json.dumps(doc))
    print(f"iam: growth-agent-s3 -> {BUCKET}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-rule", action="store_true")
    ap.add_argument("--invoke", action="store_true")
    ap.add_argument("--dry", action="store_true",
                    help="deploy with DRY_RUN=true (nothing publishes)")
    a = ap.parse_args()

    lam = boto3.client("lambda", region_name=REGION)
    s3 = boto3.client("s3", region_name=REGION)
    events = boto3.client("events", region_name=REGION)
    iam = boto3.client("iam", region_name=REGION)

    zip_path = build_zip()
    ensure_bucket(s3)
    ensure_role_policy(iam)
    deploy_function(zip_path, lam)
    if a.dry:
        lam.update_function_configuration(
            FunctionName=FUNCTION,
            Environment={"Variables": dict(ENV, DRY_RUN="true")})
        # the config change is asynchronous -- wait, or a fast --invoke will
        # still see the previous environment.
        lam.get_waiter("function_updated").wait(FunctionName=FUNCTION)
        print("env: DRY_RUN=true")
    if not a.no_rule:
        wire_rule(events, lam)
    if a.invoke:
        r = lam.invoke(FunctionName=FUNCTION,
                       InvocationType="RequestResponse",
                       Payload=json.dumps({"dry": True}))
        out = json.loads(r["Payload"].read())
        print("invoke:", json.dumps(out, indent=1)[:1500])
    print("done", datetime.datetime.now(datetime.timezone.utc).isoformat())


if __name__ == "__main__":
    main()
