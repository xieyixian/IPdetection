import redis

# 创建Redis连接
r = redis.Redis(host='localhost', port=6379, db=0)

# 清空当前数据库
r.flushdb()
