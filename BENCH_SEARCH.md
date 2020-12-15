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
   local path = "/api/users/?first_name=" .. genreateName() .. "&" .. "last_name=" .. genreateName()
   return wrk.format(nil, path)
end

```

# Результаты нагрузочного тестирования до индекса <a name="before"></a>

![plot](./Before%20index.png)

```
Running 30s test @ http://31.184.253.155:8083/
  2 threads and 2 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     4.71s   384.54ms   5.52s    83.33%
    Req/Sec     0.00      0.00     0.00    100.00%
  Latency Distribution
     50%    4.61s 
     75%    4.69s 
     90%    5.48s 
     99%    5.52s 
  12 requests in 30.07s, 1.82KB read
Requests/sec:      0.40
Transfer/sec:      61.85B


=====================================================

Running 30s test @ http://31.184.253.155:8083/
  2 threads and 5 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     9.07s   387.90ms   9.66s    63.64%
    Req/Sec     0.29      0.76     2.00     85.71%
  Latency Distribution
     50%    8.93s 
     75%    9.64s 
     90%    9.65s 
     99%    9.66s 
  12 requests in 30.06s, 1.82KB read
  Socket errors: connect 0, read 0, write 0, timeout 1
Requests/sec:      0.40
Transfer/sec:      61.87B

=====================================================
Далее timeout был увеличен до 30 секунд. 
Сервер на вид не рабочий под такой нагрузкой, хотя какие-то ответы все-таки отдавал.
======================================================

Running 30s test @ http://31.184.253.155:8083/
  2 threads and 10 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    22.22s    54.87ms  22.25s    80.00%
    Req/Sec    16.00     18.17    40.00     80.00%
  Latency Distribution
     50%   22.25s 
     75%   22.25s 
     90%   22.25s 
     99%   22.25s 
  10 requests in 30.08s, 1.51KB read
Requests/sec:      0.33
Transfer/sec:      51.53B

========================================================

Running 30s test @ http://31.184.253.155:8083/
  2 threads and 50 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    23.16s   189.05ms  23.34s   100.00%
    Req/Sec     3.00      4.76    10.00     75.00%
  Latency Distribution
     50%   23.34s 
     75%   23.34s 
     90%   23.34s 
     99%   23.34s 
  10 requests in 30.07s, 1.51KB read
Requests/sec:      0.33
Transfer/sec:      51.54B

=========================================================

Running 30s test @ http://31.184.253.155:8083/
  2 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    22.41s   445.84ms  22.86s    80.00%
    Req/Sec     4.50      4.21    10.00     37.50%
  Latency Distribution
     50%   22.46s 
     75%   22.70s 
     90%   22.86s 
     99%   22.86s 
  10 requests in 30.08s, 1.51KB read
Requests/sec:      0.33
Transfer/sec:      51.54B

============================================================

Running 30s test @ http://31.184.253.155:8083/
  2 threads and 500 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    23.39s   977.96ms  24.69s    80.00%
    Req/Sec     3.22      4.02    10.00     77.78%
  Latency Distribution
     50%   23.48s 
     75%   23.99s 
     90%   24.69s 
     99%   24.69s 
  10 requests in 30.01s, 1.51KB read
Requests/sec:      0.33
Transfer/sec:      51.66B

===============================================================

Running 30s test @ http://31.184.253.155:8083/
  2 threads and 1000 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    28.96s   673.05ms  29.67s    70.00%
    Req/Sec     5.75      7.07    20.00     87.50%
  Latency Distribution
     50%   29.33s 
     75%   29.61s 
     90%   29.67s 
     99%   29.67s 
  10 requests in 30.02s, 1.51KB read
  Socket errors: connect 0, read 43584, write 0, timeout 0
Requests/sec:      0.33
Transfer/sec:      51.64B

```

# Создание индекса <a name="introduce_index"></a>

```
CREATE INDEX name_index ON users (last_name, first_name);

mysql> EXPLAIN SELECT * FROM users WHERE first_name = 'Ab' AND last_name = 'Bb';
+----+-------------+-------+------------+------+---------------+------------+---------+-------------+------+----------+-------+
| id | select_type | table | partitions | type | possible_keys | key        | key_len | ref         | rows | filtered | Extra |
+----+-------------+-------+------------+------+---------------+------------+---------+-------------+------+----------+-------+
|  1 | SIMPLE      | users | NULL       | ref  | name_index    | name_index | 516     | const,const |    1 |   100.00 | NULL  |
+----+-------------+-------+------------+------+---------------+------------+---------+-------------+------+----------+-------+
1 row in set, 1 warning (0.01 sec)

mysql> EXPLAIN SELECT * FROM users WHERE last_name = 'Bb' and first_name = 'Aa';
+----+-------------+-------+------------+------+---------------+------------+---------+-------------+------+----------+-------+
| id | select_type | table | partitions | type | possible_keys | key        | key_len | ref         | rows | filtered | Extra |
+----+-------------+-------+------------+------+---------------+------------+---------+-------------+------+----------+-------+
|  1 | SIMPLE      | users | NULL       | ref  | name_index    | name_index | 516     | const,const |    1 |   100.00 | NULL  |
+----+-------------+-------+------------+------+---------------+------------+---------+-------------+------+----------+-------+
1 row in set, 1 warning (0.00 sec)
``` 


Индекс по (last_name, first_name) обладает большей селективностью, поэтому эффективней, чем (first_name, last_name):

```
Database changed
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

# Результаты нагрузочного тестирования с индексом <a name="after"></a>

![plot](./After%20index.png)

```
Running 30s test @ http://31.184.253.155:8083/
  2 threads and 2 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   568.88ms    1.12s    4.70s    85.86%
    Req/Sec    19.81      9.16    40.00     33.44%
  Latency Distribution
     50%   43.70ms
     75%  229.97ms
     90%    2.52s 
     99%    4.39s 
  657 requests in 30.06s, 99.42KB read
Requests/sec:     21.86
Transfer/sec:      3.31KB

====================================================

Running 30s test @ http://31.184.253.155:8083/
  2 threads and 5 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   497.55ms    1.17s    5.64s    88.36%
    Req/Sec    33.87     22.57    70.00     30.43%
  Latency Distribution
     50%   37.83ms
     75%  100.24ms
     90%    2.20s 
     99%    5.14s 
  1688 requests in 30.05s, 255.43KB read
Requests/sec:     56.18
Transfer/sec:      8.50KB


====================================================

Running 30s test @ http://31.184.253.155:8083/
  2 threads and 10 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   182.10ms  558.20ms   5.31s    96.90%
    Req/Sec    33.25     25.52   130.00     83.73%
  Latency Distribution
     50%   94.90ms
     75%  102.42ms
     90%  138.51ms
     99%    3.85s 
  1863 requests in 30.07s, 281.93KB read
  Socket errors: connect 0, read 0, write 0, timeout 6
Requests/sec:     61.95
Transfer/sec:      9.38KB


============================================

Running 30s test @ http://31.184.253.155:8083/
  2 threads and 50 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   331.64ms  151.71ms   1.66s    85.43%
    Req/Sec    66.95     30.07   170.00     71.04%
  Latency Distribution
     50%  308.10ms
     75%  382.11ms
     90%  409.22ms
     99%  974.60ms
  2236 requests in 30.05s, 338.46KB read
  Socket errors: connect 0, read 0, write 0, timeout 50
Requests/sec:     74.40
Transfer/sec:     11.26KB


=================================================

Running 30s test @ http://31.184.253.155:8083/
  2 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   621.95ms  282.50ms   2.42s    72.82%
    Req/Sec    76.51     51.66   460.00     82.44%
  Latency Distribution
     50%  661.75ms
     75%  764.63ms
     90%  904.40ms
     99%    1.47s 
  3693 requests in 30.06s, 560.19KB read
  Socket errors: connect 0, read 0, write 0, timeout 4
Requests/sec:    122.87
Transfer/sec:     18.64KB

=======================================================

Running 30s test @ http://31.184.253.155:8083/
  2 threads and 500 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     2.80s     1.56s    8.44s    77.01%
    Req/Sec    65.34     40.08   222.00     73.12%
  Latency Distribution
     50%    2.77s 
     75%    3.60s 
     90%    4.48s 
     99%    7.89s 
  2732 requests in 30.01s, 413.54KB read
  Socket errors: connect 0, read 0, write 0, timeout 440
Requests/sec:     91.02
Transfer/sec:     13.78KB

==========================================================

Running 30s test @ http://31.184.253.155:8083/
  2 threads and 1000 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     4.18s     2.70s    9.99s    60.61%
    Req/Sec    37.12     26.47   181.00     68.57%
  Latency Distribution
     50%    4.43s 
     75%    6.20s 
     90%    7.79s 
     99%    9.75s 
  1632 requests in 30.04s, 247.45KB read
  Socket errors: connect 0, read 33340, write 0, timeout 355
Requests/sec:     54.34
Transfer/sec:      8.24KB


```