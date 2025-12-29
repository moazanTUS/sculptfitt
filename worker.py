import os
import json
import tempfile

import boto3
import pymysql

from backend.analyzers.squat_analyzer import SquatAnalyzer
from backend.analyzers.pushup_analyzer import PushupAnalyzer
from backend.analyzers.shoulder_press_analyzer import ShoulderPressAnalyzer


ANALYZERS = {
    "squats": SquatAnalyzer,
    "pushups": PushupAnalyzer,
    "shoulder_press": ShoulderPressAnalyzer,
}

sqs = boto3.client("sqs")
s3 = boto3.client("s3")

QUEUE_URL = os.environ["QUEUE_URL"]
UPLOAD_BUCKET = os.environ["UPLOAD_BUCKET"]
OUT_BUCKET = os.environ["OUT_BUCKET"]

DB_HOST = os.environ["DB_HOST"]
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]
DB_NAME = os.environ["DB_NAME"]


def db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        connect_timeout=10
    )


def set_status(job_id, status, **fields):
    con = db()
    with con.cursor() as cur:
        sets = ["status=%s"]
        vals = [status]

        for k, v in fields.items():
            sets.append(f"{k}=%s")
            vals.append(v)

        vals.append(job_id)
        cur.execute(f"UPDATE jobs SET {', '.join(sets)} WHERE job_id=%s", vals)

    con.commit()
    con.close()


def get_job(job_id):
    con = db()
    with con.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute("SELECT * FROM jobs WHERE job_id=%s", (job_id,))
        row = cur.fetchone()
    con.close()
    return row


def parse_s3_key_from_message(msg_body: dict) -> str:
    # S3->SQS notifications usually wrap the record(s)
    if "Records" in msg_body:
        return msg_body["Records"][0]["s3"]["object"]["key"]
    # fallback if you ever publish simple messages yourself
    if "s3Key" in msg_body:
        return msg_body["s3Key"]
    raise ValueError("Cannot find s3 key in SQS message")


def main():
    print("Worker started. Polling SQS...")

    while True:
        print("Polling SQS...")
        resp = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20
        )

        msgs = resp.get("Messages", [])
        if not msgs:
            continue

        msg = msgs[0]
        receipt = msg["ReceiptHandle"]

        try:
            body = json.loads(msg["Body"])
            s3_key = parse_s3_key_from_message(body)

            # expected key: uploads/<user>/<jobId>.mp4
            job_id = os.path.splitext(os.path.basename(s3_key))[0]

            job = get_job(job_id)
            if not job:
                print(f"Job not found in DB: {job_id}. Deleting message.")
                sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt)
                continue

            exercise = job["exercise"]
            Analyzer = ANALYZERS.get(exercise)
            if not Analyzer:
                raise ValueError(f"Unknown exercise in DB: {exercise}")

            print(f"Processing job {job_id} ({exercise}) from {s3_key}")
            set_status(job_id, "PROCESSING")

            with tempfile.TemporaryDirectory() as d:
                in_path = os.path.join(d, "input.mp4")
                s3.download_file(UPLOAD_BUCKET, s3_key, in_path)

                # IMPORTANT: your analyzers must be headless (no cv2.imshow)
                analyzer = Analyzer(in_path)
                report = analyzer.analyze()

                out_key = f"outputs/{job.get('user_id','user')}/{job_id}_annotated.mp4"
                s3.upload_file(report["annotated_video"], OUT_BUCKET, out_key)

                set_status(
                    job_id,
                    "DONE",
                    output_s3_key=out_key,
                    result_json=json.dumps(report)
                )

            print(f"Done job {job_id}")

        except Exception as e:
            print("FAILED:", str(e))
            # best-effort: update job if we can parse job_id
            try:
                if "job_id" in locals():
                    set_status(job_id, "FAILED", error_message=str(e))
            except Exception:
                pass

        # always delete message to avoid infinite retry loops while debugging
        sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt)


if __name__ == "__main__":
    main()
