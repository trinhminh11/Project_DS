import yaml
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.dates import days_ago, timedelta, timezone
from airflow.utils.task_group import TaskGroup
from database.integrity_check import check_integrity_all
from database.sql_helper import (
    get_create_cpu_specs_table_sql,
    get_create_gpu_specs_table_sql,
    get_create_laptop_specs_table_sql,
    get_insert_into_cpu_specs_table_sql,
    get_insert_into_gpu_specs_table_sql,
    get_insert_into_laptop_specs_table_sql,
)

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

dag = DAG(
    "run_all_dag",
    default_args=default_args,
    description="The DAG control all the tasks for the project",
    schedule_interval="@monthly",
    start_date=days_ago(1),
    max_active_tasks=3,
)


with open("/app/config.yml", "r") as file:
    laptopshop_names = yaml.safe_load(file)["main"]

with TaskGroup("laptop_scraping_tasks", dag=dag) as laptop_scraping_tasks:
    for name in laptopshop_names:
        task = BashOperator(
            task_id=f"scrape_{name}",
            bash_command="cd /app/scraper && scrapy crawl {}_spider -O ../temp/{}_data.json".format(
                name, name
            ),
            pool="default_pool",
            do_xcom_push=False,
            dag=dag,
        )

with TaskGroup(
    "specifications_scraping_tasks", dag=dag
) as specifications_scraping_tasks:
    cpu_scrape_task = BashOperator(
        task_id="cpu_scrape_task",
        bash_command="cd /app/scraper && scrapy crawl cpu_spider -O ../temp/cpu_data.json",
        pool="default_pool",
        do_xcom_push=False,
        dag=dag,
    )

    gpu_scrape_task = BashOperator(
        task_id="gpu_scrape_task",
        bash_command="cd /app/scraper && scrapy crawl gpu_spider -O ../temp/gpu_data.json",
        pool="default_pool",
        do_xcom_push=False,
        dag=dag,
    )


# [DATABASE (POSTGRES) TASK]
with TaskGroup("database_tasks", dag=dag) as database_tasks:
    # SQL generation tasks
    create_cpu_specs_table_sql = PythonOperator(
        task_id="create_cpu_specs_table_sql",
        python_callable=get_create_cpu_specs_table_sql,
        op_args=[timezone.utcnow().month, timezone.utcnow().year],
        dag=dag,
    )

    insert_into_cpu_specs_table_sql = PythonOperator(
        task_id="insert_into_cpu_specs_table_sql",
        python_callable=get_insert_into_cpu_specs_table_sql,
        op_args=[
            "./temp/cpu_data.json",
            timezone.utcnow().month,
            timezone.utcnow().year,
        ],
        dag=dag,
    )

    create_gpu_specs_table_sql = PythonOperator(
        task_id="create_gpu_specs_table_sql",
        python_callable=get_create_gpu_specs_table_sql,
        op_args=[timezone.utcnow().month, timezone.utcnow().year],
        dag=dag,
    )

    insert_into_gpu_specs_table_sql = PythonOperator(
        task_id="insert_into_gpu_specs_table_sql",
        python_callable=get_insert_into_gpu_specs_table_sql,
        op_args=[
            "./temp/gpu_data.json",
            timezone.utcnow().month,
            timezone.utcnow().year,
        ],
        dag=dag,
    )

    create_laptop_specs_table_sql = PythonOperator(
        task_id="create_laptop_specs_table_sql",
        python_callable=get_create_laptop_specs_table_sql,
        op_args=[timezone.utcnow().month, timezone.utcnow().year],
        dag=dag,
    )

    insert_into_laptop_specs_table_sql = PythonOperator(
        task_id="insert_into_laptop_specs_table_sql",
        python_callable=get_insert_into_laptop_specs_table_sql,
        op_args=[
            ["./temp/{}_data.json".format(name) for name in laptopshop_names],
            timezone.utcnow().month,
            timezone.utcnow().year,
        ],
        dag=dag,
    )

    # CPU specs table
    create_cpu_specs_table_task = PostgresOperator(
        task_id="create_cpu_specs_table_task",
        postgres_conn_id="postgres_default",
        sql="{{ task_instance.xcom_pull(task_ids='database_tasks.create_cpu_specs_table_sql') }}",
        pool="default_pool",
        dag=dag,
    )

    insert_into_cpu_specs_table_task = PostgresOperator(
        task_id="insert_into_cpu_specs_table_task",
        postgres_conn_id="postgres_default",
        sql="{{ task_instance.xcom_pull(task_ids='database_tasks.insert_into_cpu_specs_table_sql') }}",
        pool="default_pool",
        dag=dag,
    )

    # GPU specs table
    create_gpu_specs_table_task = PostgresOperator(
        task_id="create_gpu_specs_table_task",
        postgres_conn_id="postgres_default",
        sql="{{ task_instance.xcom_pull(task_ids='database_tasks.create_gpu_specs_table_sql') }}",
        pool="default_pool",
        dag=dag,
    )

    insert_into_gpu_specs_table_task = PostgresOperator(
        task_id="insert_into_gpu_specs_table_task",
        postgres_conn_id="postgres_default",
        sql="{{ task_instance.xcom_pull(task_ids='database_tasks.insert_into_gpu_specs_table_sql') }}",
        pool="default_pool",
        dag=dag,
    )

    # Laptop specifications table
    create_laptop_specs_table_task = PostgresOperator(
        task_id="create_laptop_specs_table_task",
        postgres_conn_id="postgres_default",
        sql="{{ task_instance.xcom_pull(task_ids='database_tasks.create_laptop_specs_table_sql') }}",
        pool="default_pool",
        dag=dag,
    )

    insert_into_laptop_specs_table_task = PostgresOperator(
        task_id="insert_into_laptop_specs_table_task",
        postgres_conn_id="postgres_default",
        sql="{{ task_instance.xcom_pull(task_ids='database_tasks.insert_into_laptop_specs_table_sql') }}",
        pool="default_pool",
        dag=dag,
    )

    check_integrity_task = PythonOperator(
        task_id="check_integrity",
        python_callable=check_integrity_all,
        dag=dag,
    )

# [DATA ANALYSIS TASK]
with TaskGroup("data_analysis_tasks", dag=dag) as data_analysis_tasks:
    save_data_as_csv = BashOperator(
        task_id="save_data_as_csv",
        bash_command="cd /app && python /app/data_analysis/data_save.py",
        pool="default_pool",
        do_xcom_push=False,
        dag=dag,
    )

    train_model = BashOperator(
        task_id="train_model",
        bash_command="cd /app && python /app/data_analysis/train.py --model all",
        pool="default_pool",
        do_xcom_push=False,
        dag=dag,
    )

    run_eda = BashOperator(
        task_id="run_eda",
        bash_command="jupyter nbconvert --to notebook --execute /app/data_analysis/EDA.ipynb --output /app/data_analysis/EDA.ipynb",
        pool="default_pool",
        do_xcom_push=False,
        dag=dag,
    )

    convert_eda_to_html = BashOperator(
        task_id="convert_eda_to_html",
        bash_command=f"mkdir -p /app/data_analysis/results/eda && jupyter nbconvert --to html /app/data_analysis/EDA.ipynb --output /app/data_analysis/results/eda/EDA_{CURRENT_MONTH}_{CURRENT_YEAR}.html",
        pool="default_pool",
        do_xcom_push=False,
        dag=dag,
    )

# [DEFINE DIRECTED ACYCLIC GRAPH]
laptop_scraping_tasks >> insert_into_laptop_specs_table_sql

cpu_scrape_task >> insert_into_cpu_specs_table_sql
gpu_scrape_task >> insert_into_gpu_specs_table_sql

[
    create_cpu_specs_table_task,
    create_gpu_specs_table_task,
] >> create_laptop_specs_table_task
[
    insert_into_cpu_specs_table_task,
    insert_into_gpu_specs_table_task,
] >> insert_into_laptop_specs_table_task

(
    create_cpu_specs_table_sql
    >> create_cpu_specs_table_task
    >> insert_into_cpu_specs_table_task
)
insert_into_cpu_specs_table_sql >> insert_into_cpu_specs_table_task
(
    create_gpu_specs_table_sql
    >> create_gpu_specs_table_task
    >> insert_into_gpu_specs_table_task
)
insert_into_gpu_specs_table_sql >> insert_into_gpu_specs_table_task

create_laptop_specs_table_sql >> create_laptop_specs_table_task
insert_into_laptop_specs_table_sql >> insert_into_laptop_specs_table_task
create_laptop_specs_table_task >> insert_into_laptop_specs_table_task

insert_into_laptop_specs_table_task >> check_integrity_task

check_integrity_task >> save_data_as_csv
check_integrity_task >> train_model
check_integrity_task >> run_eda >> convert_eda_to_html
