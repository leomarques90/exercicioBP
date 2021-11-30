import airflow
import requests
import pandas as pd
import time
import pymongo
from airflow.models import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python_operator import PythonOperator
from airflow.utils.email import send_email
from airflow.models import Variable


args = {
    "owner": "leonardo",
    "start_date": airflow.utils.dates.days_ago(0),
    "schedule_interval": "@daily",
}
dag = DAG(dag_id="bp_dag", default_args=args)

termo = Variable.get("termo")
db_conn = Variable.get("database_conn_uri")
db_name = Variable.get("database_name")
db_col = Variable.get("collection_name")
email_receiver = Variable.get("email_receiver")

baseUrl = "https://hacker-news.firebaseio.com/v0/"
data = []
data_termo = []
parent = []




def max_ids(**context):
    maxIdDB = 0
    myclient = pymongo.MongoClient(db_conn)
    db = myclient[db_name]
    col = db[db_col]
    maxIdDB_check = col.find_one(sort=[("id", -1)])
    maxId = maxId = requests.get(url=baseUrl + "maxitem.json").json()
    if maxIdDB_check is None:
        0
    else:
        maxIdDB = maxIdDB_check["id"]

    context["ti"].xcom_push(key="maxId", value=maxId)
    context["ti"].xcom_push(key="maxIdDB", value=maxIdDB)


def comments_child(id, data):
    from bs4 import BeautifulSoup

    try:
        response = requests.get("https://news.ycombinator.com/item?id=" + str(id))
        content = BeautifulSoup(response.text, "lxml")
        ids = content.find_all(attrs={"class": "athing comtr"})
        i = 0
        ##Em caso de se ter algum "filho", busca-se todos os comentários abaixo da história.
        for _ in ids:
            try:
                r = requests.get(
                    "https://hacker-news.firebaseio.com/v0/item/"
                    + str(ids[i]["id"])
                    + ".json"
                )
                data.append(r.json())
                i += 1
                break
            except:
                time.sleep(5)
    except:
        time.sleep(5)


def read_data(**context):
    maxId = context["ti"].xcom_pull(key="maxId")
    maxIdDB = context["ti"].xcom_pull(key="maxIdDB")
    if maxIdDB == 0:
        urlInicial = baseUrl + "newstories.json"
        r = requests.get(urlInicial)
        list = r.json()
        for i in list[0:50]:
            r = requests.get(baseUrl + "item/" + str(i) + ".json")
            data.append(r.json())
            descendants = "descendants" in r.json()
            if descendants == True and r.json()["descendants"] > 0:
                comments_child(i, data)
    else:
        for x in range(maxIdDB + 1, maxId + 1):
            r = requests.get(baseUrl + "item/" + str(x) + ".json")
            dead = "dead" in r.json()
            deleted = "deleted" in r.json()
            if dead == False:
                if deleted == False:
                    data.append(r.json())
                    if r.json()["type"] == "story":
                        descendants = "descendants" in r.json()
                        if descendants == True and r.json()["descendants"] > 0:
                            comments_child(x, data)
                    elif r.json()["type"] == "comment":
                        parent = r.json()["parent"]
                        kids = "kids" in r.json()
                        if kids == True:
                            comments_child(x, data)
                        while True:
                            r = requests.get(baseUrl + "item/" + str(parent) + ".json")
                            data.append(r.json())
                            if r.json()["type"] == "comment":
                                parent = r.json()["parent"]
                            else:
                                break
    context["ti"].xcom_push(key="data", value=data)


def insert_data_1(**context):
    data = context["ti"].xcom_pull(key="data")
    myclient = pymongo.MongoClient(db_conn)
    db = myclient[db_name]
    col = db[db_col]
    col.insert_many(data)


def send_term(**context):
    data = context["ti"].xcom_pull(key="data")
    i = 0
    for _ in data:
        txt = "text" in data[i]
        if txt:
            findterm = data[i]["text"].find(termo)
            if findterm > 0:
                data[i]["time"] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(data[i]["time"])
                )
                data_termo.append(data[i])
        i += 1
    qtd_termo = len(data_termo)
    df = pd.DataFrame(data_termo)
    df.rename(
        {
            0: "by",
            1: "descendants",
            2: "id",
            3: "score",
            4: "time",
            5: "title",
            6: "type",
            7: "url",
        },
        axis=1,
        inplace=True,
    )
    df.to_csv("termos.csv", index=False)
    context["ti"].xcom_push(key="qtd_termo", value=qtd_termo)


def email_callback(**context):
    qtd_termo = context["ti"].xcom_pull(key="qtd_termo")
    if qtd_termo > 0:
        send_email(
            to=[email_receiver],
            subject="Airflow Term Alert",
            html_content="<p>Sauda&ccedil;&otilde;es, Prezados(as).</p><p>Na &uacute;ltima execu&ccedil;&atilde;o da rotina de checagem de termos definidos pela equipe de analistas foram encontradas "
            + str(qtd_termo)
            + ' ocorr&ecirc;ncias de coment&aacute;rios contendo o termo "'
            + str(termo)
            + '".</p><p>Consta em anexo um documento de extens&atilde;o csv com as ocorr&ecirc;ncias encontradas.</p><p>Atenciosamente,</p><p>Equipe de Engenharia de Dados</p><p>&nbsp;</p>',
            files=["termos.csv"],
        )
    else:
        send_email(
            to=[email_receiver],
            subject="Airflow Term Alert",
            html_content='<p>Sauda&ccedil;&otilde;es, Prezados(as).</p><p>Na &uacute;ltima execu&ccedil;&atilde;o da rotina de checagem de termos definidos pela equipe de analistas n&atilde;o foram encontradas ocorr&ecirc;ncias de coment&aacute;rios contendo o termo "'
            + str(termo)
            + '".</p><p>Atenciosamente,</p><p>Equipe de Engenharia de Dados</p><p>&nbsp;</p>',
        )


t1 = PythonOperator(
    task_id="get_max_ids", python_callable=max_ids, provide_context=True, dag=dag
)

t2 = PythonOperator(
    task_id="read_data", python_callable=read_data, provide_context=True, dag=dag
)

t3 = PythonOperator(
    task_id="insert_data", python_callable=insert_data_1, provide_context=True, dag=dag
)

t4 = PythonOperator(
    task_id="send_term", python_callable=send_term, provide_context=True, dag=dag
)

t5 = PythonOperator(
    task_id="send_mail",
    python_callable=email_callback,
    provide_context=True,
    dag=dag,
)

t1 >> t2 >> [t3, t4]
t4 >> t5
