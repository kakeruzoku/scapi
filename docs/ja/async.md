**絶対正しいと保証するものではありません。**

# asyncとは

Asyncというのは非同期処理のことで、処理の待ち時間に別の処理を実行することができます。

# 関数を作ってみよう

`async def`から関数を作成することで、非同期処理がつかえるようになります。
```py
async def main():
    print("running!")
    return "OK"
```

`asyncio.run()`で実行することができます。

```py
import asyncio

async def main():
    print("running!")
    return "OK"


print(asyncio.run(main())) #返り値が返る
# running!
# OK
```

## ただmain()とするだけだと...

```py

async def main():
    print("running!")
    return "OK"


print(main())
# <coroutine object test at 0x00000275B0579000>
#
# Warning (from warnings module):
#   File "*****", line 5
# RuntimeWarning: coroutine 'test' was never awaited
```

asyncでは、`test()`が行われたタイミングでは関数を実行せず、`coroutine object`というものを生成します。
`asyncio.run()`などに`coroutine object`を入れて実行することで実際に実行されます。

# 実際に非同期処理してみよう

今の状態だと、同時に1つの関数しか実行されていないため、非同期処理されているとは言えません。

## 非同期関数で非同期関数を実行する

別の場所にある非同期関数を実行する時には、先頭に`await`をつけます。この場合は、他の関数が実行終了するまで次の行には進みません。
```py
import asyncio

async def main2():
    print("running!")

async def main():
    await main2() #main2が終わるまでここで止まる
    return "OK"

print(asyncio.run(main()))
# running!
# OK
```

## 複数の非同期関数を実行する。

処理の途中で一時停止したい場合(通常でいう`time.sleep()`)をしたい場合は`await asyncio.sleep(1)`と入力することで、一時停止し、他の処理を実行します。

```py
import asyncio
import time

async def main():
    print("開始",time.time())
    await asyncio.sleep(2)
    print("2秒止まった",time.time())
    return "OK"


print(asyncio.run(main()))
# 開始 1736411544.0946996
# 2秒止まった 1736411546.1567948
# OK
```

ここで、複数の処理をしてみましょう。
`asyncio.gather()`関数で複数の関数を実行できます。

```py
import asyncio
import time

async def wait(times:int):
    print("停止前:",times,time.time())
    await asyncio.sleep(times)
    print("停止後:",times,time.time())
    return times

async def main():
    return await asyncio.gather(wait(1),wait(2),wait(3)) #3つの関数をタスクに入れる


print(asyncio.run(main()))
# 停止前: 1 1736411738.884931
# 停止前: 2 1736411738.9436812
# 停止前: 3 1736411738.9616215
# 停止後: 1 1736411739.9576778
# 停止後: 2 1736411740.9739637
# 停止後: 3 1736411741.9762988
# [1, 2, 3]
```

それぞれ非同期に停止して、約3秒で処理が終了しています。

ここで、同期処理をした時と比べてみましょう。

```py
import asyncio
import time

def wait(times:int):
    print("停止前:",times,time.time())
    time.sleep(times)
    print("停止後:",times,time.time())
    return times

print(list(wait(1),wait(2),wait(3)))


# 停止前: 1 1736411937.6134763
# 停止後: 1 1736411938.6769195
# 停止前: 2 1736411938.6928463
# 停止後: 2 1736411940.709606
# 停止前: 3 1736411940.7549348
# 停止後: 3 1736411943.7705212
# [1, 2, 3]
```

同期処理だと`1秒待つ`→`2秒待つ`→`3秒待つ`という順番になり、6秒処理がかかります。

`asyncio.gather()`関数は、入力された関数の処理が終了するまでその行で一時停止します。ただ、関数を追加したい場合は`asyncio.create_task()`を使用します。

ここで、タスクが終了する前に`main()`(`asyncio.run()`で実行した関数)が終了すると、強制的に全ての非同期実行は終了します。そのため、`asyncio.gather()`や`asyncio.sleep()`、`await (関数)`で実行を待つ必要があります。

```py
import asyncio
import time

async def wait(times:int):
    print("停止前:",times,time.time())
    await asyncio.sleep(times)
    print("停止後:",times,time.time())
    return times

async def main():
    task1 = asyncio.create_task(wait(1)) #ここでタスクに追加される
    task2 = asyncio.create_task(wait(2))
    print("タスクに追加:",time.time())
    print(await asyncio.gather(task1,task2)) #awaitやasyncio.gather()に入れると、終了するまで待って、結果を返す


asyncio.run(main())
# タスクに追加: 1736412773.1325738
# 停止前: 1 1736412773.1854324
# 停止前: 2 1736412773.2024145
# 停止後: 1 1736412774.218083
# 停止後: 2 1736412775.226813
# [1, 2]
```

# 処理の順番について

非同期処理は同時に複数の関数を処理するのではなく、ある関数の処理の休憩時間(`asyncio.sleep()`など)に他の処理を入れることによって実行されます。先ほどのコードでは、

```py
asyncio.run(main()) #非同期処理の開始

#main()の中
task1 = asyncio.create_task(wait(1)) #ここでタスクに追加される
task2 = asyncio.create_task(wait(2))
print("タスクに追加:",time.time()) #まだ実行されない
print(await asyncio.gather(task1,task2))
#     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ 
# awaitがきて、まだtask1,task2が終わっていないので、ここでmain()->wait(1)に処理が移る

#wait(1)の中
print("停止前:",times,time.time()) # 停止前: 1 1736412773.1854324
await asyncio.sleep(times)
#^^^^^^^^^^^^^^^^^^^^^^^^^
# awaitがきて、まだ1秒たっていないので、ここでwait(1)->wait(2)に処理が移る

#wait(2)の中
print("停止前:",times,time.time()) # 停止前: 2 1736412773.2024145
await asyncio.sleep(times)
#^^^^^^^^^^^^^^^^^^^^^^^^^
# awaitがきて、まだ2秒たっていないので、ここでwait(2)->main()に処理が移る

#main()の中
print(await asyncio.gather(task1,task2))
#     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# まだtask1,task2が終わっていないので、内部でまたmain()->wait(1)に処理が移る。

#wait(1)の中
await asyncio.sleep(times)
#^^^^^^^^^^^^^^^^^^^^^^^^^
#まだ1秒立っていないのでwait(1)->wait(2)に移る

#1秒立つまで、main()->wait(1)->wait(2)->main()が繰り返される

#wait(1)の中
await asyncio.sleep(times)
#1秒立ったので、sleep()はawaitから抜け出す
print("停止後:",times,time.time()) # 停止後: 1 1736412774.218083
return times

#wait(1)のタスクが終了するので、wait(1)はタスクから削除され、wait(2)に移る。もう1秒立つまで、main()->wait(2)->main()が繰り返される

#wait(2)の中
await asyncio.sleep(times)
#2秒立ったので、sleep()はawaitから抜け出す
print("停止後:",times,time.time()) # 停止後: 2 1736412775.226813
return times
#wait(2)のタスクが終了するので、wait(2)はタスクから削除され、main()に移る。

#main()の中
print(await asyncio.gather(task1,task2)) #[1, 2]
#どちらとも処理が終わっているのでprint()が実行される

#asyncio.run()の処理が終わる。
```

という感じで行われています。とにかく`await`があったところで他の処理に移る時があるよ～ってことだけ覚えればいい。(逆にそれ以外のところでは他の処理には移らない。)