import yaml
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago, timedelta, timezone
from airflow.utils.task_group import TaskGroup

CURRENT_MONTH = timezone.utcnow().month
CURRENT_YEAR = timezone.utcnow().year

# [DEFINE DAG]
default_args = {
    "owner": "veil",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

scraper_dag = DAG(
    "scraper_dag",
    default_args=default_args,
    description="The DAG control all the tasks for the project",
    schedule_interval="@monthly",
    start_date=days_ago(1),
    max_active_tasks=3,
)


with open("/app/config.yml", "r") as file:
    laptopshop_names = yaml.safe_load(file)["main"]

with TaskGroup("laptop_scraping_tasks", dag=scraper_dag) as laptop_scraping_tasks:
    for name in laptopshop_names:
        task = BashOperator(
            task_id=f"scrape_{name}",
            bash_command=f"cd /app/scraper && scrapy crawl {name}_spider -O ../temp/{name}_data.json",
            pool="default_pool",
            do_xcom_push=False,
            dag=scraper_dag,
        )

with TaskGroup(
    "specifications_scraping_tasks", dag=scraper_dag
) as specifications_scraping_tasks:
    cpu_scrape_task = BashOperator(
        task_id="cpu_scrape_task",
        bash_command="cd /app/scraper && scrapy crawl cpu_spider -O ../temp/cpu_data.json",
        pool="default_pool",
        do_xcom_push=False,
        dag=scraper_dag,
    )

    gpu_scrape_task = BashOperator(
        task_id="gpu_scrape_task",
        bash_command="cd /app/scraper && scrapy crawl gpu_spider -O ../temp/gpu_data.json",
        pool="default_pool",
        do_xcom_push=False,
        dag=scraper_dag,
    )


# [DEFINE DIRECTED ACYCLIC GRAPH]
