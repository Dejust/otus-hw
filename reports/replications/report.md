# Репликации MySQL

## Мониторинг ресурсов

Для мониторинга выбран https://hub.docker.com/r/netdata/netdata. Был добавлен сервис в docker-compose.yaml.

## Нагрузочное тестирование до репликации

Выбраны запрос: поиск по имени и фамилии. Для того, чтобы нагрузить диск, был выполнен отказ от покрывающего индекса.

```
wrk -s bench_search.lua -d 30s -t 4 -c 50 --timeout 30s --latency http://localhost:8083/
```

### CPU

![plot](./img/master_cpu_before.jpg)


### Memory

![plot](./img/master_memory_before.jpg)


### DISK

![plot](./img/master_disk_before.jpg)


## Настраиваем асинхронную репликацию


### Запустить мастер с включенным binary log

1. В конфигурации мастера добавлено

[mysqld]
server-id=1
log-bin=mysql-bin

2. Мастер был запущен

3. Проверил, что log bin включен.
```txt
mysql> show variables like "%log_bin%";
+---------------------------------+--------------------------------+
| Variable_name                   | Value                          |
+---------------------------------+--------------------------------+
| log_bin                         | ON                             |
| log_bin_basename                | /var/lib/mysql/mysql-bin       |
| log_bin_index                   | /var/lib/mysql/mysql-bin.index |
| log_bin_trust_function_creators | OFF                            |
| log_bin_use_v1_row_events       | OFF                            |
| sql_log_bin                     | ON                             |
+---------------------------------+--------------------------------+

mysql> SHOW MASTER STATUS;
+------------------+----------+--------------+------------------+-------------------+
| File             | Position | Binlog_Do_DB | Binlog_Ignore_DB | Executed_Gtid_Set |
+------------------+----------+--------------+------------------+-------------------+
| mysql-bin.000003 |      154 |              |                  |                   |
+------------------+----------+--------------+------------------+-------------------+
```

```txt
root@32865b26845a:/# ls -alh /var/lib/mysql/  | grep mysql-bin

-rw-r----- 1 mysql mysql  154 Dec 27 09:19 mysql-bin.000001
-rw-r----- 1 mysql mysql   19 Dec 27 09:19 mysql-bin.index
```

### Создать пользователя для реплики

Был создан пользователь `rep1` с паролем `123456`.

```
mysql> CREATE USER 'rep1'@'%' IDENTIFIED BY '123456';
Query OK, 0 rows affected (0.05 sec)

mysql> GRANT REPLICATION SLAVE ON *.* TO 'rep1'@'%';
Query OK, 0 rows affected (0.01 sec)
```

## Настройка слейва

0. 

Был сделан snapshot данных мастера

```
docker-compose exec db mysqldump --all-databases --master-data > dbdump.db 
```

1. Был добавлен новый сервис db_slave с настройками.

Был также включен binary log, так как далее планируется эксперимент с переключением слейва как мастера.

```txt
[mysqld]
server-id=21
log-bin=mysql-bin
```


2. Мастер установлен в качестве источника данных 

```
mysql> CHANGE MASTER TO MASTER_HOST='db', MASTER_USER='rep1', MASTER_PASSWORD='123456', MASTER_LOG_FILE='mysql-bin.000004', MASTER_LOG_POS=609;

mysql> SHOW SLAVE STATUS\G
*************************** 1. row ***************************
               Slave_IO_State: 
                  Master_Host: db
                  Master_User: rep1
                  Master_Port: 3306
                Connect_Retry: 60
              Master_Log_File: mysql-bin.000003
          Read_Master_Log_Pos: 595
               Relay_Log_File: 858beb3879c1-relay-bin.000001
                Relay_Log_Pos: 4
        Relay_Master_Log_File: mysql-bin.000003
             Slave_IO_Running: No
            Slave_SQL_Running: No

mysql> START SLAVE;
```

3. Проверка репликации

На мастере

```
mysql> CREATE TABLE test (id integer not null);
Query OK, 0 rows affected (0.01 sec)

mysql> insert into test (id) values (1);
Query OK, 1 row affected (0.04 sec)

mysql> insert into test (id) values (2);
Query OK, 1 row affected (0.01 sec)

mysql> insert into test (id) values (3);
Query OK, 1 row affected (0.02 sec)
```

На слейве:

```
mysql> select * from test;
+----+
| id |
+----+
|  1 |
|  2 |
|  3 |
+----+
3 rows in set (0.00 sec)
```

## Нагрузочное тестирование после репликации

Выбраны запрос: поиск по имени и фамилии. Для того, чтобы нагрузить диск, был выполнен отказ от покрывающего индекса.

```
wrk -s bench_search.lua -d 30s -t 4 -c 50 --timeout 30s --latency http://localhost:8083/
```

### CPU (MASTER)

![plot](./img/master_cpu_after.jpg)


### Memory (MASTER)

![plot](./img/master_memory_after.jpg)


### DISK (MASTER)

![plot](./img/master_disk_after.jpg)


### CPU (SLAVE)

![plot](./img/slave_cpu.jpg)


### Memory (SLAVE)

![plot](./img/slave_memory.jpg)


### DISK (SLAVE)

![plot](./img/slave_disk.jpg)


## Включить row-based replication

Выставим binlog_format=ROW на мастере и на слейве. После перезапуска сервера, убедились, что репликация продолжает работать.

### Обзор binlog (RBR)

Убедились, что binlogformat = ROW

```
mysql> SHOW GLOBAL VARIABLES LIKE 'binlog_format';
+---------------+-------+
| Variable_name | Value |
+---------------+-------+
| binlog_format | ROW   |
+---------------+-------+
1 row in set (0.01 sec)
```

Обновили таблицу:

```
> update test2 set id = 50000;
```

В логе, ожидаемо, лежит несколько записей:

```
$ mysqlbinlog --base64-output=DECODE-ROWS -vv mysql-bin.000006


#201227 13:07:50 server id 1  end_log_pos 686 CRC32 0x2dfb7f65 	Update_rows: table id 108 flags: STMT_END_F
### UPDATE `network`.`test2`
### WHERE
###   @1=100 /* INT meta=0 nullable=1 is_null=0 */
### SET
###   @1=50000 /* INT meta=0 nullable=1 is_null=0 */
### UPDATE `network`.`test2`
### WHERE
###   @1=1000 /* INT meta=0 nullable=1 is_null=0 */
### SET
###   @1=50000 /* INT meta=0 nullable=1 is_null=0 */
### UPDATE `network`.`test2`
### WHERE
###   @1=1000 /* INT meta=0 nullable=1 is_null=0 */
### SET
###   @1=50000 /* INT meta=0 nullable=1 is_null=0 */
### UPDATE `network`.`test2`
### WHERE
###   @1=1000 /* INT meta=0 nullable=1 is_null=0 */
### SET
###   @1=50000 /* INT meta=0 nullable=1 is_null=0 */
### UPDATE `network`.`test2`
### WHERE
###   @1=5000 /* INT meta=0 nullable=1 is_null=0 */
### SET
###   @1=50000 /* INT meta=0 nullable=1 is_null=0 */

```

### Обзор binlog (SBR)

Убедились, что binlogformat = STATEMENT
```
mysql> SHOW GLOBAL VARIABLES LIKE 'binlog_format';
+---------------+-----------+
| Variable_name | Value     |
+---------------+-----------+
| binlog_format | STATEMENT |
+---------------+-------+
1 row in set (0.01 sec)
```

Обновлена таблица

```
> insert into test2 (id) values (50);
> update test2 set id = 25000;
```


В логе, ожидаемо, лежит одна команда.
```
$ mysqlbinlog --base64-output=DECODE-ROWS -vv mysql-bin.000007


# at 304
#201227 13:10:30 server id 1  end_log_pos 411 CRC32 0xe9cab265 	Query	thread_id=2	exec_time=0	error_code=0
use `network`/*!*/;
SET TIMESTAMP=1609074630/*!*/;
update test2 set id = 25000
/*!*/;

```

## Включит GTID

https://dev.mysql.com/doc/refman/5.7/en/replication-mode-change-online-enable-gtids.html

На мастере и слейве выполнить:

```
SET @@GLOBAL.ENFORCE_GTID_CONSISTENCY = WARN;
```

После чего, согласно документации, я убедился, что в логах нет предупреждение. Приложение генерирует
простейшие запросы, поэтому ничего не должно противоречить GTID based replication.

На мастере и слейве выполнить. Все транзанкции, что противоречат GTID, будут отклонены.

```
SET @@GLOBAL.ENFORCE_GTID_CONSISTENCY = ON;
```

Действительно, не работает...
https://dev.mysql.com/doc/refman/5.7/en/replication-options-gtids.html
```
mysql> begin;
Query OK, 0 rows affected (0.00 sec)

mysql> create temporary table x2 (id integer);
ERROR 1787 (HY000): Statement violates GTID consistency: CREATE TEMPORARY TABLE and DROP TEMPORARY TABLE can only be executed outside transactional context.  These statements are also not allowed in a function or trigger because functions and triggers are also considered to be multi-statement transactions.
```

На мастере и слейве выполнить:

новые транзакции будут анонимными. реплицированные транзакции могут быть как GTID так и анонимными
```
SET @@GLOBAL.GTID_MODE = OFF_PERMISSIVE;
```

На мастере и слейве выполнить

Новые транзакции - GTID. Реплицированные могут быть как GTID так и анонимными.

```
SET @@GLOBAL.GTID_MODE = ON_PERMISSIVE;
```

Убеждаемся, что анонимных транзакций более нет (на мастере и слейве)

```
mysql> SHOW STATUS LIKE 'ONGOING_ANONYMOUS_TRANSACTION_COUNT';
+-------------------------------------+-------+
| Variable_name                       | Value |
+-------------------------------------+-------+
| Ongoing_anonymous_transaction_count | 0     |
+-------------------------------------+-------+
1 row in set (0.00 sec)
```

Включаем GTID на каждом сервере

```
SET @@GLOBAL.GTID_MODE = ON;

----
db_1          | 2020-12-28T09:43:13.934739Z 6 [Note] Changed ENFORCE_GTID_CONSISTENCY from OFF to WARN.
db_1          | 2020-12-28T09:48:53.131850Z 6 [Note] Changed ENFORCE_GTID_CONSISTENCY from WARN to ON.
db_1          | 2020-12-28T09:51:34.735272Z 6 [Note] Changed GTID_MODE from OFF to OFF_PERMISSIVE.
db_1          | 2020-12-28T09:52:36.905136Z 6 [Note] Changed GTID_MODE from OFF_PERMISSIVE to ON_PERMISSIVE.
db_1          | 2020-12-28T09:54:37.445995Z 6 [Note] Changed GTID_MODE from ON_PERMISSIVE to ON.


db_slave_1_1  | 2020-12-28T09:43:16.067636Z 5 [Note] Changed ENFORCE_GTID_CONSISTENCY from OFF to WARN.
db_slave_1_1  | 2020-12-28T09:48:49.293475Z 5 [Note] Changed ENFORCE_GTID_CONSISTENCY from WARN to ON.
db_slave_1_1  | 2020-12-28T09:51:36.991689Z 5 [Note] Changed GTID_MODE from OFF to OFF_PERMISSIVE.
db_slave_1_1  | 2020-12-28T09:52:34.593487Z 5 [Note] Changed GTID_MODE from OFF_PERMISSIVE to ON_PERMISSIVE.
db_slave_1_1  | 2020-12-28T09:54:35.357892Z 5 [Note] Changed GTID_MODE from ON_PERMISSIVE to ON.
```

Список выполненных GTID транзакций

```
mysql> select * from  mysql.gtid_executed limit 5;
+--------------------------------------+----------------+--------------+
| source_uuid                          | interval_start | interval_end |
+--------------------------------------+----------------+--------------+
| b357c92d-482a-11eb-aa69-0242ac170002 |              1 |            1 |
| b357c92d-482a-11eb-aa69-0242ac170002 |              2 |            2 |
| b357c92d-482a-11eb-aa69-0242ac170002 |              3 |            3 |
| b357c92d-482a-11eb-aa69-0242ac170002 |              4 |            4 |
| b357c92d-482a-11eb-aa69-0242ac170002 |              5 |            5 |
+--------------------------------------+----------------+--------------+
```

В cnf файл мастера и слейва добавлено:

```
gtid_mode=ON
enforce_gtid_consistency=ON
```

## Добавить 2-ой слейв.

Для простоты, решено было поднять стенд с нуля.


```
docker-compose up -d db db_slave_1 db_slave_2
```

## Настройка полу-синхронной репликацию

На мастере:

```
mysql> INSTALL PLUGIN rpl_semi_sync_master SONAME 'semisync_master.so';
Query OK, 0 rows affected (0.00 sec)

mysql> SELECT PLUGIN_NAME, PLUGIN_STATUS
    ->        FROM INFORMATION_SCHEMA.PLUGINS
    ->        WHERE PLUGIN_NAME LIKE '%semi%';
+----------------------+---------------+
| PLUGIN_NAME          | PLUGIN_STATUS |
+----------------------+---------------+
| rpl_semi_sync_master | ACTIVE        |
+----------------------+---------------+
1 row in set (0.01 sec)

mysql> SET GLOBAL rpl_semi_sync_master_enabled = 1;
Query OK, 0 rows affected (0.00 sec)

mysql> SET GLOBAL rpl_semi_sync_master_timeout = 1000;
Query OK, 0 rows affected (0.00 sec)

mysql> create table test (id integer null);
Query OK, 0 rows affected (0.02 sec)

mysql> SHOW STATUS LIKE 'Rpl_semi_sync%';
+--------------------------------------------+-------+
| Variable_name                              | Value |
+--------------------------------------------+-------+
| Rpl_semi_sync_master_clients               | 2     |
| Rpl_semi_sync_master_net_avg_wait_time     | 0     |
| Rpl_semi_sync_master_net_wait_time         | 0     |
| Rpl_semi_sync_master_net_waits             | 2     |
| Rpl_semi_sync_master_no_times              | 0     |
| Rpl_semi_sync_master_no_tx                 | 0     |
| Rpl_semi_sync_master_status                | ON    |
| Rpl_semi_sync_master_timefunc_failures     | 0     |
| Rpl_semi_sync_master_tx_avg_wait_time      | 187   |
| Rpl_semi_sync_master_tx_wait_time          | 187   |
| Rpl_semi_sync_master_tx_waits              | 1     |
| Rpl_semi_sync_master_wait_pos_backtraverse | 0     |
| Rpl_semi_sync_master_wait_sessions         | 0     |
| Rpl_semi_sync_master_yes_tx                | 1     |
+--------------------------------------------+-------+
14 rows in set (0.00 sec)

```

На слейвах. Был установлен пплагин как для мастера, так и для слейва: для целей эксперимента - один из слейвов должен стать мастером.

```
mysql> INSTALL PLUGIN rpl_semi_sync_slave SONAME 'semisync_slave.so';
Query OK, 0 rows affected (0.00 sec)

mysql> INSTALL PLUGIN rpl_semi_sync_master SONAME 'semisync_master.so';
Query OK, 0 rows affected (0.00 sec)

mysql> SELECT PLUGIN_NAME, PLUGIN_STATUS
    ->        FROM INFORMATION_SCHEMA.PLUGINS
    ->        WHERE PLUGIN_NAME LIKE '%semi%';
+----------------------+---------------+
| PLUGIN_NAME          | PLUGIN_STATUS |
+----------------------+---------------+
| rpl_semi_sync_slave  | ACTIVE        |
| rpl_semi_sync_master | ACTIVE        |
+----------------------+---------------+
2 rows in set (0.00 sec)

mysql> SET GLOBAL rpl_semi_sync_slave_enabled = 1;
Query OK, 0 rows affected (0.00 sec)

mysql> STOP SLAVE IO_THREAD;
Query OK, 0 rows affected (0.00 sec)

mysql> START SLAVE IO_THREAD;
Query OK, 0 rows affected (0.00 sec)


mysql> SHOW STATUS LIKE 'Rpl_semi_sync%';
+--------------------------------------------+-------+
| Variable_name                              | Value |
+--------------------------------------------+-------+
| Rpl_semi_sync_master_clients               | 0     |
| Rpl_semi_sync_master_net_avg_wait_time     | 0     |
| Rpl_semi_sync_master_net_wait_time         | 0     |
| Rpl_semi_sync_master_net_waits             | 0     |
| Rpl_semi_sync_master_no_times              | 0     |
| Rpl_semi_sync_master_no_tx                 | 0     |
| Rpl_semi_sync_master_status                | OFF   |
| Rpl_semi_sync_master_timefunc_failures     | 0     |
| Rpl_semi_sync_master_tx_avg_wait_time      | 0     |
| Rpl_semi_sync_master_tx_wait_time          | 0     |
| Rpl_semi_sync_master_tx_waits              | 0     |
| Rpl_semi_sync_master_wait_pos_backtraverse | 0     |
| Rpl_semi_sync_master_wait_sessions         | 0     |
| Rpl_semi_sync_master_yes_tx                | 0     |
| Rpl_semi_sync_slave_status                 | ON    |
+--------------------------------------------+-------+
15 rows in set (0.00 sec)
```

## Нагрузка на запись

Был запущен скрипт для генерации анект:

```
docker-compose run --rm api python -m network_api.commands.generate_fake_users
```

Который, до убийства мастера, успел создать `22462` анкет.

Которые успешно разъехались по всем слейвам. Без потерь транзакций.

```
mysql> select count(*) from users;
+----------+
| count(*) |
+----------+
|    22462 |
+----------+
```

Переключаем `db_slave_2` на `db_slave_1`

```
mysql> STOP SLAVE IO_THREAD;
Query OK, 0 rows affected (0.00 sec)

mysql> CHANGE MASTER TO MASTER_HOST='db_slave_1', MASTER_USER='rep1', MASTER_PASSWORD='123456', MASTER_LOG_FILE='mysql-bin.000003', MASTER_LOG_POS=649;
Query OK, 0 rows affected, 2 warnings (0.01 sec)

mysql> START SLAVE IO_THREAD;
Query OK, 0 rows affected (0.00 sec)
```

Проверяем, что репликация работает:

новый мастер:

```
mysql> insert into test (id) values (1000);
Query OK, 1 row affected (0.05 sec)

mysql> select count(*) from test;
+----------+
| count(*) |
+----------+
|        1 |
+----------+
1 row in set (0.00 sec)
```

на слейве:

```
mysql> select count(*) from test;
+----------+
| count(*) |
+----------+
|        1 |
+----------+
1 row in set (0.00 sec)
```