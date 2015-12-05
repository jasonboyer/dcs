import argparse
import audioin.chunks_from_s3 as ch
import pyaudio
import queue


parser = argparse.ArgumentParser()
parser.add_argument('-b', '--bucket', type=str, default='boyer-cs767-audio', help='S3 bucket where audio samples are stored. Should be output from a Kinesis Firehose')
parser.add_argument('-Y', '--year', type=int, default=2015, help='year')
parser.add_argument('-M', '--month', type=int, default=11, help='month')
parser.add_argument('-D', '--day', type=int, default=23, help='day')
parser.add_argument('-H', '--hour', type=int, default=0, help='hour')
parser.add_argument('-m', '--minute', type=int, default=0, help='start minute')
parser.add_argument('-s', '--skip_seconds', type=int, default=0, help='seconds to skip before playing')
parser.add_argument('-p', '--play_seconds', type=int, default=3600, help='seconds to play')

args = parser.parse_args()

output_queue = queue.Queue()
player = ch.ChunksFromS3(bucket_name=args.bucket,
                      year=args.year, month=args.month, day=args.day, hour=args.hour,
                      rate=96000, samples_per_record=96000/100,
                      chunk=96000/40, step=96000/100,
                      output_queue=output_queue)
player.play_blob(args.minute, args.skip_seconds, args.play_seconds)


# output_queue should have samples
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=96000,
                output=True)

while True:
    data = output_queue.get(True)
    if data is not None:
        stream.write(data)
    else:
        break

stream.stop_stream()
stream.close()

p.terminate()
