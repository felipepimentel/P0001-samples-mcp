from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Scheduler Tool Example")
scheduler = BackgroundScheduler()
scheduler.start()

scheduled_results = {}


@mcp.tool()
def schedule_message(message: str, delay_seconds: int = 10) -> str:
    """Schedule a message to be stored after delay_seconds"""
    run_time = datetime.now() + timedelta(seconds=delay_seconds)
    job_id = f"msg_{run_time.timestamp()}"

    def store():
        scheduled_results[job_id] = f"[{datetime.now()}] {message}"

    scheduler.add_job(store, "date", run_date=run_time, id=job_id)
    return f"Scheduled message for {run_time} (job_id={job_id})"


@mcp.resource("scheduler://result/{job_id}")
def get_scheduled_result(job_id: str) -> str:
    """Get the result of a scheduled message by job_id"""
    return scheduled_results.get(job_id, "Not ready or not found.")
