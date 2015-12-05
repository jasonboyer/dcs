    records = kin.get_records(limit=int(frame_count/CHUNK), shard_iterator=shardit['ShardIterator'], b64_decode=False)

    if VERBOSE:
        print("getRecords returned records: " + str(records))

    shardit['ShardIterator'] = records['NextShardIterator']
    data = []

    for rec in records['Records']:
        pp.pprint(rec)
        data.append(base64.b64decode(rec['Data']))
#        data.append(rec['Data'])

    if data is None:
        return data, pyaudio.paComplete
    else:
        return b''.join(data), pyaudio.paContinue
