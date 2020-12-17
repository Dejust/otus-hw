# <a name="common"/> Тестовый стенд

Стенд: VDS 512 МБ + 1vCPU

Ресурсы распределены следующим образом:

```
API: 0.5 vcpu  / 64 Mib
NGINX: 0.25 vcpu / 64 Mib
MYSQL: 0.25 vcpu / 256 Mib
```

```bash
wrk -s bench_search.lua -d 30s -c 2 --timeout 10s --latency http://31.184.253.155:8083/
```

```lua
local upperCase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
local lowerCase = "abcdefghijklmnopqrstuvwxyz"

math.randomseed(os.time())

genreateName = function ()
   local rand = math.random(#upperCase)
   local output = string.sub(upperCase, rand, rand)

   rand = math.random(#lowerCase)
   output = output .. string.sub(lowerCase, rand, rand)

   rand = math.random(#lowerCase)
   output = output .. string.sub(lowerCase, rand, rand)

   return output
end

request = function()
   local path = "/api/users/?first_name_prefix=" .. genreateName() .. "&" .. "last_name_prefix=" .. genreateName()
   return wrk.format(nil, path)
end

```

# Результаты нагрузочного тестирования до индекса

```
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 1 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 1 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.38s   257.13ms   2.64s    50.00%
    Req/Sec     0.00      0.00     0.00    100.00%
  Latency Distribution
     50%    2.55s 
     75%    2.64s 
     90%    2.64s 
     99%    2.64s 
  4 requests in 10.03s, 620.00B read
Requests/sec:      0.40
Transfer/sec:      61.82B

dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 5 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 5 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     0.00us    0.00us   0.00us    -nan%
    Req/Sec     0.00      0.00     0.00      -nan%
  Latency Distribution
     50%    0.00us
     75%    0.00us
     90%    0.00us
     99%    0.00us
  0 requests in 10.02s, 0.00B read
Requests/sec:      0.00
Transfer/sec:       0.00B

```

# Создание индекса (композитный last_name, first_name)

В рамках задачи необходимо организовать поиск по двум полям ОДНОВРЕМЕННО: first_name, last_name. Для этой цели,
предлагается ввести композитный индекс на двух колонках (last_name, first_name). В качестве первого элемента индекса
выбрана колонка last_name, так как значения в этой колонке обладают большей селективностью, по сравнению с first_name.

Как видно по результатам EXPLAIN, индекс покрывает запросы:

```
WHERE last_name = "Ab%"
WHERE last_name = "Ab%" and first_name = "Bb%"
``` 

Но не покрывает запросы только на имя пользователя.

```
mysql> explain SELECT * FROM users use index (name_index) WHERE last_name LIKE "B%" AND first_name LIKE "A%";
+----+-------------+-------+------------+-------+---------------+------------+---------+------+--------+----------+-----------------------+
| id | select_type | table | partitions | type  | possible_keys | key        | key_len | ref  | rows   | filtered | Extra                 |
+----+-------------+-------+------------+-------+---------------+------------+---------+------+--------+----------+-----------------------+
|  1 | SIMPLE      | users | NULL       | range | name_index    | name_index | 516     | NULL | 153624 |    11.11 | Using index condition |
+----+-------------+-------+------------+-------+---------------+------------+---------+------+--------+----------+-----------------------+


mysql> explain SELECT * FROM users use index (name_index) WHERE last_name LIKE "B%";
+----+-------------+-------+------------+-------+---------------+------------+---------+------+--------+----------+-----------------------+
| id | select_type | table | partitions | type  | possible_keys | key        | key_len | ref  | rows   | filtered | Extra                 |
+----+-------------+-------+------------+-------+---------------+------------+---------+------+--------+----------+-----------------------+
|  1 | SIMPLE      | users | NULL       | range | name_index    | name_index | 258     | NULL | 153624 |   100.00 | Using index condition |
+----+-------------+-------+------------+-------+---------------+------------+---------+------+--------+----------+-----------------------+
1 row in set, 1 warning (0.00 sec)


mysql> explain SELECT * FROM users use index (name_index) WHERE first_name LIKE "A%";
+----+-------------+-------+------------+------+---------------+------+---------+------+--------+----------+-------------+
| id | select_type | table | partitions | type | possible_keys | key  | key_len | ref  | rows   | filtered | Extra       |
+----+-------------+-------+------------+------+---------------+------+---------+------+--------+----------+-------------+
|  1 | SIMPLE      | users | NULL       | ALL  | NULL          | NULL | NULL    | NULL | 995835 |    11.11 | Using where |
+----+-------------+-------+------------+------+---------------+------+---------+------+--------+----------+-------------+
1 row in set, 1 warning (0.00 sec)

``` 

Количество уникальных имен и фамилий:

```
mysql> select count(distinct first_name) from users;
+----------------------------+
| count(distinct first_name) |
+----------------------------+
|                        695 |
+----------------------------+
1 row in set (2.08 sec)

mysql> select count(distinct last_name) from users;
+---------------------------+
| count(distinct last_name) |
+---------------------------+
|                      1005 |
+---------------------------+
1 row in set (2.21 sec)
```

# Результаты нагрузочного тестирования с индексом

```
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 1 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 1 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    35.36ms   14.02ms 147.48ms   95.64%
    Req/Sec    29.24      5.51    40.00     82.65%
  Latency Distribution
     50%   32.34ms
     75%   32.93ms
     90%   35.78ms
     99%  133.38ms
  289 requests in 10.02s, 43.74KB read
Requests/sec:     28.84
Transfer/sec:      4.36KB

dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 10 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 10 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    44.11ms   17.70ms 374.26ms   96.55%
    Req/Sec   232.78     35.87   280.00     80.81%
  Latency Distribution
     50%   40.49ms
     75%   43.90ms
     90%   51.42ms
     99%  139.74ms
  2303 requests in 10.02s, 348.69KB read
Requests/sec:    229.91
Transfer/sec:     34.81KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 100 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   471.84ms  262.11ms   1.94s    73.95%
    Req/Sec   215.27     75.31   484.00     82.42%
  Latency Distribution
     50%  406.29ms
     75%  552.92ms
     90%  777.68ms
     99%    1.44s 
  2152 requests in 10.02s, 326.75KB read
Requests/sec:    214.68
Transfer/sec:     32.60KB

dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 250 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 250 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     1.00s   713.53ms   3.82s    48.98%
    Req/Sec   236.09     46.32   303.00     81.82%
  Latency Distribution
     50%    1.03s 
     75%    1.15s 
     90%    1.99s 
     99%    2.90s 
  2332 requests in 10.03s, 352.99KB read
Requests/sec:    232.47
Transfer/sec:     35.19KB

dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 500 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 500 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.04s     1.17s    8.53s    69.87%
    Req/Sec   231.89     56.14   303.00     83.16%
  Latency Distribution
     50%    2.09s 
     75%    2.16s 
     90%    3.98s 
     99%    5.73s 
  2205 requests in 10.07s, 334.35KB read
Requests/sec:    218.88
Transfer/sec:     33.19KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 750 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 750 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.31s     1.20s    8.96s    74.16%
    Req/Sec   210.40     68.22   400.00     75.56%
  Latency Distribution
     50%    2.22s 
     75%    2.65s 
     90%    3.74s 
     99%    6.26s 
  1904 requests in 10.02s, 288.20KB read
  Socket errors: connect 0, read 3768, write 0, timeout 0
Requests/sec:    190.04
Transfer/sec:     28.77KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 1000 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 1000 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.30s     1.48s    8.31s    62.44%
    Req/Sec   177.87    120.04   590.00     69.41%
  Latency Distribution
     50%    2.25s 
     75%    2.96s 
     90%    4.26s 
     99%    6.54s 
  1584 requests in 10.01s, 242.11KB read
  Socket errors: connect 0, read 3427, write 0, timeout 0
Requests/sec:    158.26
Transfer/sec:     24.19KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 2000 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 2000 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.05s   915.48ms   6.07s    82.63%
    Req/Sec   228.69     53.68   323.00     89.66%
  Latency Distribution
     50%    1.74s 
     75%    2.59s 
     90%    3.16s 
     99%    4.64s 
  2026 requests in 10.01s, 306.67KB read
  Socket errors: connect 980, read 2908, write 0, timeout 0
Requests/sec:    202.34
Transfer/sec:     30.63KB
```

# Создание индекса (два отдельных для last_name, first_name)

Предыдущий индекс обладает недостатком: он не позволяет искать по префиксу имени пользователя.

Для того чтобы решить эту проблему, предлагается ввести два отдельных индекса (взамен предыдущему) 
и сравнить его эффективность.
 
```
mysql> explain SELECT * FROM users use index (last_name) WHERE last_name LIKE "B%" AND first_name LIKE "A%";
+----+-------------+-------+------------+-------+---------------+-----------+---------+------+--------+----------+------------------------------------+
| id | select_type | table | partitions | type  | possible_keys | key       | key_len | ref  | rows   | filtered | Extra                              |
+----+-------------+-------+------------+-------+---------------+-----------+---------+------+--------+----------+------------------------------------+
|  1 | SIMPLE      | users | NULL       | range | last_name     | last_name | 258     | NULL | 166554 |    11.11 | Using index condition; Using where |
+----+-------------+-------+------------+-------+---------------+-----------+---------+------+--------+----------+------------------------------------+
1 row in set, 1 warning (0.00 sec)

mysql> explain SELECT * FROM users use index (last_name) WHERE last_name LIKE "B%";
+----+-------------+-------+------------+-------+---------------+-----------+---------+------+--------+----------+-----------------------+
| id | select_type | table | partitions | type  | possible_keys | key       | key_len | ref  | rows   | filtered | Extra                 |
+----+-------------+-------+------------+-------+---------------+-----------+---------+------+--------+----------+-----------------------+
|  1 | SIMPLE      | users | NULL       | range | last_name     | last_name | 258     | NULL | 166554 |   100.00 | Using index condition |
+----+-------------+-------+------------+-------+---------------+-----------+---------+------+--------+----------+-----------------------+
1 row in set, 1 warning (0.00 sec)

mysql> explain SELECT * FROM users use index (last_name) WHERE first_name LIKE "A%";
+----+-------------+-------+------------+------+---------------+------+---------+------+--------+----------+-------------+
| id | select_type | table | partitions | type | possible_keys | key  | key_len | ref  | rows   | filtered | Extra       |
+----+-------------+-------+------------+------+---------------+------+---------+------+--------+----------+-------------+
|  1 | SIMPLE      | users | NULL       | ALL  | NULL          | NULL | NULL    | NULL | 995835 |    11.11 | Using where |
+----+-------------+-------+------------+------+---------------+------+---------+------+--------+----------+-------------+
1 row in set, 1 warning (0.00 sec)


```

# Результаты тестов

```
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 1 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 1 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    34.44ms    2.41ms  53.92ms   92.33%
    Req/Sec    28.70      3.93    40.00     86.00%
  Latency Distribution
     50%   33.88ms
     75%   34.77ms
     90%   36.31ms
     99%   48.19ms
  287 requests in 10.02s, 43.43KB read
Requests/sec:     28.65
Transfer/sec:      4.34KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 10 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 10 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    42.18ms    5.91ms  85.13ms   84.34%
    Req/Sec   235.22     28.32   280.00     87.00%
  Latency Distribution
     50%   41.02ms
     75%   43.39ms
     90%   48.10ms
     99%   65.88ms
  2344 requests in 10.01s, 354.71KB read
Requests/sec:    234.11
Transfer/sec:     35.43KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 100 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   386.25ms  154.15ms   1.10s    69.47%
    Req/Sec   257.48    108.61   505.00     69.57%
  Latency Distribution
     50%  388.14ms
     75%  409.60ms
     90%  615.33ms
     99%  874.81ms
  2542 requests in 10.02s, 384.92KB read
Requests/sec:    253.78
Transfer/sec:     38.43KB

dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 250 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 250 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   987.73ms  508.40ms   4.66s    74.34%
    Req/Sec   251.77     74.27   484.00     79.17%
  Latency Distribution
     50%  976.14ms
     75%    1.06s 
     90%    1.74s 
     99%    2.86s 
  2444 requests in 10.02s, 370.13KB read
Requests/sec:    243.83
Transfer/sec:     36.93KB

dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 500 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 500 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.00s   659.00ms   6.29s    83.59%
    Req/Sec   230.26     40.05   272.00     88.54%
  Latency Distribution
     50%    2.14s 
     75%    2.18s 
     90%    2.23s 
     99%    4.05s 
  2217 requests in 10.07s, 335.73KB read
Requests/sec:    220.22
Transfer/sec:     33.35KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 750 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 750 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.72s     1.51s    8.78s    73.11%
    Req/Sec   209.40     88.44   530.00     71.79%
  Latency Distribution
     50%    2.60s 
     75%    3.22s 
     90%    4.78s 
     99%    7.01s 
  1644 requests in 10.01s, 249.00KB read
  Socket errors: connect 0, read 3833, write 0, timeout 0
Requests/sec:    164.24
Transfer/sec:     24.87KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 1000 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 1000 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.12s     1.46s    8.75s    61.41%
    Req/Sec   236.95     60.59   340.00     85.06%
  Latency Distribution
     50%    2.10s 
     75%    2.53s 
     90%    4.00s 
     99%    6.41s 
  2081 requests in 10.10s, 315.00KB read
  Socket errors: connect 0, read 3381, write 0, timeout 0
Requests/sec:    206.09
Transfer/sec:     31.19KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 2000 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 2000 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.14s     1.27s    9.14s    70.38%
    Req/Sec   216.54     69.79   323.00     81.32%
  Latency Distribution
     50%    1.93s 
     75%    2.83s 
     90%    3.60s 
     99%    5.96s 
  1975 requests in 10.09s, 299.54KB read
  Socket errors: connect 980, read 2940, write 0, timeout 0
Requests/sec:    195.69
Transfer/sec:     29.68KB
```

# Итог

## Average latency

Без индекса сервер тянет одного клиента, но не более.
С индексам ситуация лучше. По эффективности оба индекса примерно одинаковы.

![plot](./Average%20latency%20(seconds).png)

## Throughput

Без индекса сервер тянет одного клиента, но не более.
С индексам ситуация лучше. По эффективности оба индекса примерно одинаковы.

![plot](./Throughput%20(req_seconds).png)

## Сравнение композитного и индекс last_name_index

В случае композитного индекса при выполнении запроса применен именно он. В случае двух индексов - только индекс по last_name. 

Далее представлен детальный explain при использовании обоих индексов из которых видно, что не смотря на разную стратегию, оба индекса обладают почти одинаковой "стоимостью". Поэтому, для данного запроса, имеет смысл использовать индекс по last_name, так как он обладает меньшими запросами.

### Композитный индекс

Применяется только одна часть композитного индекса - last_name. Это информация используется далее для извлечения остальной информации (Index Condition Pushdown)..

```
explain format = json SELECT * FROM users use index (name_index) WHERE last_name LIKE "B%" AND first_name LIKE "A%";
 
| {
  "query_block": {
    "select_id": 1,
    "cost_info": {
      "query_cost": "215074.61"
    },
    "table": {
      "table_name": "users",
      "access_type": "range",
      "possible_keys": [
        "name_index"
      ],
      "key": "name_index",
      "used_key_parts": [
        "last_name"
      ],
      "key_length": "516",
      "rows_examined_per_scan": 153624,
      "rows_produced_per_join": 17067,
      "filtered": "11.11",
      "index_condition": "((`network`.`users`.`last_name` like 'B%') and (`network`.`users`.`first_name` like 'A%'))",
      "cost_info": {
        "read_cost": "211661.08",
        "eval_cost": "3413.53",
        "prefix_cost": "215074.61",
        "data_read_per_join": "29M"
      },
      "used_columns": [
        "id",
        "first_name",
        "last_name",
        "email",
        "password_hash",
        "age",
        "city",
        "interests",
        "gender"
      ]
    }
  }
} |
```

### Индекс last_name

Применяется индекс по last_name. Эта информация используется для дальнейшей фильтрации по first_name и извлечения остальной информации (Index Condition Pushdown).

```
explain format = json SELECT * FROM users use index (first_name) WHERE last_name LIKE "B%" AND first_name LIKE "A%";


| {
  "query_block": {
    "select_id": 1,
    "cost_info": {
      "query_cost": "204454.00"
    },
    "table": {
      "table_name": "users",
      "access_type": "ALL",
      "possible_keys": [
        "first_name"
      ],
      "rows_examined_per_scan": 995835,
      "rows_produced_per_join": 21607,
      "filtered": "2.17",
      "cost_info": {
        "read_cost": "200132.57",
        "eval_cost": "4321.43",
        "prefix_cost": "204454.00",
        "data_read_per_join": "37M"
      },
      "used_columns": [
        "id",
        "first_name",
        "last_name",
        "email",
        "password_hash",
        "age",
        "city",
        "interests",
        "gender"
      ],
      "attached_condition": "((`network`.`users`.`last_name` like 'B%') and (`network`.`users`.`first_name` like 'A%'))"
    }
  }
} |

```

## Идеи для дальнейшей оптимизации. Покрывающий индекс.

Необходимо упростить запрос так, чтобы все данные извлекались из индекса:

```
SELECT id, first_name, last_name FROM users WHERE last_name LIKE "X%" AND first_name LIKE "Y%"
```

В этом случае, комопзитный индекс покажет себя очень красиво:

```
mysql> explain SELECT id, first_name, last_name FROM users use index (name_index) WHERE last_name LIKE "B%" AND first_name LIKE "A%";
+----+-------------+-------+------------+-------+---------------+------------+---------+------+--------+----------+--------------------------+
| id | select_type | table | partitions | type  | possible_keys | key        | key_len | ref  | rows   | filtered | Extra                    |
+----+-------------+-------+------------+-------+---------------+------------+---------+------+--------+----------+--------------------------+
|  1 | SIMPLE      | users | NULL       | range | name_index    | name_index | 516     | NULL | 153624 |    11.11 | Using where; Using index |
+----+-------------+-------+------------+-------+---------------+------------+---------+------+--------+----------+--------------------------+
1 row in set, 1 warning (0.00 sec)
```

Using index указывает на то, что данные будут взяты из самого индекса.  Стоимость запроса в данном случае будет ниже:

```
{
  "query_block": {
    "select_id": 1,
    "cost_info": {
      "query_cost": "71052.05"
    },
    "table": {
      "table_name": "users",
      "access_type": "range",
      "possible_keys": [
        "name_index"
      ],
      "key": "name_index",
      "used_key_parts": [
        "last_name"
      ],
      "key_length": "516",
      "rows_examined_per_scan": 153624,
      "rows_produced_per_join": 17067,
      "filtered": "11.11",
      "using_index": true,
      "cost_info": {
        "read_cost": "67638.52",
        "eval_cost": "3413.53",
        "prefix_cost": "71052.05",
        "data_read_per_join": "29M"
      },
      "used_columns": [
        "id",
        "first_name",
        "last_name"
      ],
      "attached_condition": "((`network`.`users`.`last_name` like 'B%') and (`network`.`users`.`first_name` like 'A%'))"
    }
  }
}
```

# Результаты тестирования. Покрывающий индекс.

```
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 1 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 1 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    32.57ms    1.70ms  50.09ms   94.39%
    Req/Sec    30.23      4.34    40.00     84.00%
  Latency Distribution
     50%   32.19ms
     75%   32.62ms
     90%   33.43ms
     99%   40.35ms
  303 requests in 10.03s, 45.85KB read
Requests/sec:     30.22
Transfer/sec:      4.57KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 10 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 10 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    38.59ms    7.82ms 108.06ms   94.65%
    Req/Sec   258.00     38.41   300.00     89.00%
  Latency Distribution
     50%   36.90ms
     75%   38.97ms
     90%   41.79ms
     99%   79.04ms
  2571 requests in 10.01s, 389.07KB read
Requests/sec:    256.92
Transfer/sec:     38.88KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 100 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   367.44ms  141.30ms   1.13s    74.08%
    Req/Sec   269.20     46.03   430.00     83.84%
  Latency Distribution
     50%  360.57ms
     75%  389.78ms
     90%  580.44ms
     99%  843.81ms
  2665 requests in 10.02s, 404.12KB read
Requests/sec:    266.05
Transfer/sec:     40.34KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 250 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 250 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   920.61ms  655.20ms   4.29s    49.42%
    Req/Sec   262.14     40.60   310.00     82.65%
  Latency Distribution
     50%  935.00ms
     75%    1.16s 
     90%    1.77s 
     99%    2.62s 
  2580 requests in 10.03s, 390.58KB read
Requests/sec:    257.34
Transfer/sec:     38.96KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 500 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 500 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     1.77s     1.03s    6.14s    68.06%
    Req/Sec   257.19     54.02   320.00     89.69%
  Latency Distribution
     50%    1.89s 
     75%    1.92s 
     90%    3.63s 
     99%    4.12s 
  2505 requests in 10.06s, 379.17KB read
Requests/sec:    249.00
Transfer/sec:     37.69KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 750 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 750 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     1.92s     1.18s    6.93s    72.87%
    Req/Sec   246.66     64.36   313.00     90.59%
  Latency Distribution
     50%    1.64s 
     75%    2.60s 
     90%    3.49s 
     99%    5.12s 
  2123 requests in 10.04s, 321.86KB read
  Socket errors: connect 0, read 3696, write 0, timeout 0
Requests/sec:    211.53
Transfer/sec:     32.07KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 1000 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 1000 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.35s     1.08s    8.83s    81.80%
    Req/Sec   214.48     76.54   303.00     72.22%
  Latency Distribution
     50%    2.12s 
     75%    3.03s 
     90%    3.19s 
     99%    4.98s 
  1934 requests in 10.10s, 293.51KB read
  Socket errors: connect 0, read 3087, write 0, timeout 0
Requests/sec:    191.49
Transfer/sec:     29.06KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 2000 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 2000 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.01s     1.09s    7.73s    72.57%
    Req/Sec   243.08     59.13   313.00     88.89%
  Latency Distribution
     50%    2.02s 
     75%    2.05s 
     90%    3.64s 
     99%    5.10s 
  2198 requests in 10.04s, 332.71KB read
  Socket errors: connect 980, read 2665, write 0, timeout 0
Requests/sec:    218.98
Transfer/sec:     33.15KB
```

### Результаты тестов без индекса. После оптимизации запроса.

```
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 1 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 1 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     1.81s   742.73ms   3.13s    80.00%
    Req/Sec     0.00      0.00     0.00    100.00%
  Latency Distribution
     50%    1.47s 
     75%    1.61s 
     90%    3.13s 
     99%    3.13s 
  5 requests in 10.02s, 775.00B read
Requests/sec:      0.50
Transfer/sec:      77.33B
```

### Результаты тесты два индекса (last_name, first_name). После оптимизации запроса.

```
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 1 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 1 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    34.10ms    8.94ms 142.82ms   96.31%
    Req/Sec    29.55      5.25    40.00     79.80%
  Latency Distribution
     50%   32.48ms
     75%   33.47ms
     90%   34.94ms
     99%   78.35ms
  294 requests in 10.02s, 44.49KB read
Requests/sec:     29.36
Transfer/sec:      4.44KB

dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 10 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 10 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    48.76ms   23.63ms 319.96ms   92.32%
    Req/Sec   210.21     48.34   282.00     59.00%
  Latency Distribution
     50%   41.99ms
     75%   51.59ms
     90%   66.10ms
     99%  138.69ms
  2096 requests in 10.02s, 317.48KB read
Requests/sec:    209.27
Transfer/sec:     31.70KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 100 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   401.88ms  172.92ms   1.63s    71.40%
    Req/Sec   244.62     51.90   313.00     69.00%
  Latency Distribution
     50%  387.55ms
     75%  464.21ms
     90%  607.14ms
     99%  907.62ms
  2438 requests in 10.01s, 370.24KB read
Requests/sec:    243.53
Transfer/sec:     36.98KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 250 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 250 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   967.81ms  638.01ms   4.41s    58.88%
    Req/Sec   246.21     58.96   313.00     89.00%
  Latency Distribution
     50%  979.54ms
     75%    1.06s 
     90%    1.84s 
     99%    2.72s 
  2458 requests in 10.04s, 372.06KB read
Requests/sec:    244.91
Transfer/sec:     37.07KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 500 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 500 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.06s     1.31s    9.21s    69.76%
    Req/Sec   211.64     65.32   290.00     81.25%
  Latency Distribution
     50%    2.11s 
     75%    2.78s 
     90%    3.53s 
     99%    6.27s 
  2051 requests in 10.05s, 310.51KB read
Requests/sec:    204.09
Transfer/sec:     30.90KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 750 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 750 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.19s     1.37s    9.02s    69.32%
    Req/Sec   203.08     69.25   313.00     71.91%
  Latency Distribution
     50%    1.96s 
     75%    3.08s 
     90%    3.82s 
     99%    5.99s 
  1819 requests in 10.10s, 275.45KB read
  Socket errors: connect 0, read 2997, write 0, timeout 0
Requests/sec:    180.08
Transfer/sec:     27.27KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 1000 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 1000 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.26s     1.37s    7.84s    71.80%
    Req/Sec   205.91     73.24   515.00     70.79%
  Latency Distribution
     50%    2.23s 
     75%    2.64s 
     90%    4.12s 
     99%    7.15s 
  1851 requests in 10.01s, 280.44KB read
  Socket errors: connect 0, read 3159, write 0, timeout 0
Requests/sec:    184.82
Transfer/sec:     28.00KB
dejust@dejust-labs:~/otus-hw$ wrk -s bench_search.lua -d 10s -t 1 -c 2000 --timeout 10s --latency http://31.184.253.155:8083/
Running 10s test @ http://31.184.253.155:8083/
  1 threads and 2000 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.26s     1.52s    9.71s    63.56%
    Req/Sec   205.60     74.35   505.00     78.02%
  Latency Distribution
     50%    2.33s 
     75%    2.66s 
     90%    4.38s 
     99%    6.69s 
  1869 requests in 10.02s, 282.91KB read
  Socket errors: connect 980, read 2740, write 0, timeout 0
Requests/sec:    186.60
Transfer/sec:     28.24KB
```

# Итог 2

Была проведена оптимизация, которая позволяет применить покрывающий композитный индекс. В результате видно, что удалось
добиться прироста по пропускной способности и уменьшить задержки по сравнению с обычным композитным индексом 
и индексом по last_name (из рассуждений выше => MySQL использует только один из двух индексов first_name или last_name). 

## Average Latency

![plot](./Latency3.png)

## Throughput

![plot](./Throuput3.png)