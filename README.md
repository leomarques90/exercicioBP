Atividade Brasil Paralelo
---

This code was written to attendee the needs sent in a exercise that I made to enter in my current job. The simulated business needs were:

> Tests your abillity to create a data workflow demonstrating good practices in the architecture solution. For accomplish that, imagine that you are serving two clients: (1) a data scientis team who seeks to work with all comments made in the Hacker News; (2) a data analyst team who wants to receive alerts every time that certain terms appear in the comments. Deliver a dataset for the first client, and trigger an alarm for the second.

## About the solution
Following part of the orientation and using my favorite language, I developed a solution that reads data from hacker-news through the official API, recommended by them, save the data in mongoDB in the raw structure e sends e-mail when a term pre-defined is encountered.<br>

### Technical details of the solution
#### About the workflow
1. Process the stories and comments from the last ID persisted in the database. If the database don't have data, the first 50 stories are read from the link that returns [500 new stories](https://hacker-news.firebaseio.com/v0/newstories.json) from the hacker-news API.
   - For each story, all descendent are read.
        ```yaml
        {
        "by" : "kmcquade",
        "descendants" : 18,
        "id" : 26154038,
        "kids" : [ 26154742, 26154244, 26154730, 26154505, 26154285, 26154677, 26154513, 26154443, 26154506 ],
        "score" : 77,
        "time" : 1613485014,
        "title" : "Show HN: Endgame – An AWS Pentesting tool to backdoor or expose AWS resources",
        "type" : "story",
        "url" : "https://github.com/salesforce/endgame"
        }
        ```
    - For each comment, the descendent are read too, and a reverse path are made until it gets to the story that originates that comment (loop through parent). Another comments in the story recovered are not processed.
        ```yaml
        {
        "by" : "baobabKoodaa",
        "id" : 26153361,
        "kids" : [ 26153463 ],
        "parent" : 26153237,
        "text" : "&gt; Have you ever done a hard leetcode problem?<p>Yes. I used to compete on CodeForces regularly.<p>&gt; Clearly the icon code was delegated to some intern or perhaps a child of one of the developers, because the bar is stupid high there just to have a conversation with a hiring manager.<p>You&#x27;re implying that the developers of Microsoft can&#x27;t be computer science illiterate, because a computer science illiterate couldn&#x27;t possibly pass through the recruitment funnel that you experienced. But <i>we know this code exists</i>. Somebody wrote it. Somebody reviewed it. Somebody tested it. Everybody involved in this process thought &quot;yeah, this is good enough&quot;, when it&#x27;s clearly not good enough. Anyone with as little as CS101 experience would not write crap like this in the first place, so it&#x27;s really hard to argue that the developers at Microsoft are computer science literate.",
        "time" : 1613479686,
        "type" : "comment"
        }
        ```
    - Dead or deleted stories and comments are not read.
        ```yaml
        {
        "by" : "mwitiderrick",
        "dead" : true,
        "id" : 26154500,
        "score" : 1,
        "time" : 1613488027,
        "title" : "Custom TensorFlow Lite Model on Android Using Firebase ML",
        "type" : "story",
        "url" : "https://heartbeat.fritz.ai/custom-tensorflow-lite-model-on-android-using-firebase-ml-7cc78cd057ec"
        }
        ```
        ```yaml
        {
        "deleted" : true,
        "id" : 26154647,
        "time" : 1613488855,
        "type" : "story"
        }
        ```
3. Insrt data into mongoDB resulted by the process described above.
4. Parallel to item 2, identify on the list generate by the item 1 if there is any occurrence of the parametrized term.
5. Send e-mail with relevant information about the execution, such as the quantity of encountered rows and mention of the term, and a file in attachment.

#### Parameters
To accomplish the requirements of the activity, some parameters of connection with mongodb were created, term definition and the e-mail that will receiver the message.
The parameters are located in the file `/airflow/variables.json` and needs to be imported (instructions are in this topic **Instructions > Usabillity**).
```yaml
{
    "termo": "understand",
    "email_receiver": "leonardorg15@gmail.com",
    "database_conn_uri": "mongodb://root:example@db",
    "database_name": "brasilParalelo",
    "collection_name": "hackerNewsRaw"
}
```
In addition to these variables, you should parametrize the (variables of SMTP)[https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html#smtp] to make the task `send_mail` work properly:

## Instructions

These instructions will copy the project to the local machine and wil enable the execution of the solution proposed.

- Clone this repo;
- Install requirements;
- Execute the service;
- Access http://localhost:8080;
- Import the document of variables.

### Requirements

- Install [Docker](https://www.docker.com/)
- Install [Docker Compose](https://docs.docker.com/compose/install/)

### Usabillity

Execute the service inside the cloned repo.

```
docker-compose up -d
```

Go to http://localhost:8080/.

Import variables in work following the path:
Admin > Variables > Choose File > variables.json > Import Variables
![image info](./imgs/intrucao_1.png)

Turn on and execute dag "bp_dag" :smile:

## Bibliography

- [Git hub airflow docker](https://github.com/tuanavu/airflow-tutorial)
- [Mongodb docker](https://hub.docker.com/_/mongo)
- [Hacker-news API](https://github.com/HackerNews/API)