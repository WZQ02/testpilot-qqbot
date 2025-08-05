msglis = {}

def cache_msg(groupid,msg):
    if groupid in msglis:
        msglis[groupid].append(msg)
        if len(msglis[groupid]) > 5:
            del msglis[groupid][0]
    else:
        msglis[groupid] = [msg]

def get_cached_msg(groupid,seq):
    return msglis[groupid][-1-seq]

def get_cached_msg_count(groupid):
    if groupid in msglis:
        return len(msglis[groupid])
    else:
        return 0

def rem_cached_msg(groupid,seq):
    del msglis[groupid][-1-seq]