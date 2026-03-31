#순차 실행 동시 실행 동기 비동기 멀티 스레드 멀티프로세스
# import time
# import threading #멀티 스레딩

# def task(name):
#     print(f"{name}시작")
#     time.sleep(2)
#     print(f"{name}완료")


# count = 0
# lock = threading.Lock()
# def increment():
#     global count
#     for _ in range(100):
#         lock.acquire() #잠금 ==> 진입 스레드가 작업을 독점하고 타 스레드들은 이구간 앞에서 대기
#         try:
#             temp = count
#             time.sleep(0.0002)
#             count = temp+1
#         finally:
#             lock.release()
# threads=[]
# for i in range(10):
#     t = threading.Thread(target=increment)
#     threads.append(t)
#     t.start()
# for t in threads:
#     t.join()
# print("최종", count)

# thread1 = threading.Thread(target = task, args = ("1번 스레드",))
# thread2 = threading.Thread(target = task, args = ("2번 스레드",))
# thread1.start() #스레드 작업 시작
# thread2.start()
# thread1.join() #작업 종료까지 메인 프로그램 대기 없으면 다음 코드 진행됨
# thread2.join()
#

# task("1번작업")
# task("2번작업")
# print("모든작업완료")

#동기 -> 비효율적/순차적        비동기 -> 병렬/ 효율적

# def delivery(name):
#     print(f"{name}시작")
#     time.sleep(1)
#     print(f"{name}완료")
#
# start = time.time()
# delivery("111")
# delivery("222")
# print()



import asyncio
import time
async def delivery_async(name):
    print(f"{name}시작")
    await asyncio.sleep(2)
    print(f"{name}완료")

async def main():
    start = time.time()
    await asyncio.gather(
        delivery_async("1111"),
        delivery_async("2222")
    )
    print(f"{time.time()-start}")

asyncio.run(main())