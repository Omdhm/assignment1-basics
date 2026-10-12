import os
from typing import BinaryIO


def find_chunk_boundaries(
    file: BinaryIO,
    desired_num_chunks: int,
    split_special_token: bytes,
) -> list[int]:
    """
    Chunk the file into parts that can be counted independently.
    May return fewer chunks if the boundaries end up overlapping.
    """
    assert isinstance(split_special_token, bytes), "Must represent special token as a bytestring"

    # Get total file size in bytes
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    chunk_size = file_size // desired_num_chunks

    # Initial guesses for chunk boundary locations, uniformly spaced
    # Chunks start on previous index, don't include last index
    chunk_boundaries = [i * chunk_size for i in range(desired_num_chunks + 1)]
    chunk_boundaries[-1] = file_size

    mini_chunk_size = 4096  # Read ahead by 4k bytes at a time

    for bi in range(1, len(chunk_boundaries) - 1):
        initial_position = chunk_boundaries[bi]
        file.seek(initial_position)  # Start at boundary guess
        while True:
            mini_chunk = file.read(mini_chunk_size)  # Read a mini chunk

            # If EOF, this boundary should be at the end of the file
            if mini_chunk == b"":
                chunk_boundaries[bi] = file_size
                break

            # Find the special token in the mini chunk
            found_at = mini_chunk.find(split_special_token)
            if found_at != -1:
                chunk_boundaries[bi] = initial_position + found_at
                break
            initial_position += mini_chunk_size

    # Make sure all boundaries are unique, but might be fewer than desired_num_chunks
    return sorted(set(chunk_boundaries))


## Usage



def wawa_file_reader(
    f: BinaryIO,
    desired_chunk:int,
    special_token: list[bytes]
) -> list[int]:
    assert all(isinstance(st, bytes) for st in special_token), "Special Token needs to be bytes instance/type"

    file_size = f.seek(0, os.SEEK_END)
    f.seek(0)
    chunk = file_size // desired_chunk
    naive_boundaries = [i*chunk for i in range(desired_chunk+1)]
    naive_boundaries[-1] = (file_size)
    mini_size = 4096

    for i in range(1, len(naive_boundaries)-1):
        position = naive_boundaries[i]
        f.seek(position)
        while True:
            mini_read = f.read(mini_size)
            if mini_read == b"":
                naive_boundaries[i] = file_size
                break
            found_at = min([mini_read.find(st) for st in special_token if mini_read.find(st) !=-1 ], default=-1)
            if found_at != -1:
                naive_boundaries[i] = found_at + position
                break
            position+=mini_size

    return sorted(set(naive_boundaries))





            



        



     

import regex as re
from multiprocessing import Pool


def work(args):
    path, s, e, special_tokens = args
    st_escape = [re.escape(st.decode('utf-8'))  for st in special_tokens]
    pat_st =  "|".join(st_escape) 
    PAT = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
           
    with open(path,  "r", encoding="utf-8") as f:
        f.seek(s)
        chunk = f.read(e - s)
        initial = 0
        corpus=[]
        matches = re.finditer(pat_st, chunk)
        match = next(matches, None)
        while True :
            if match is not None:
                decode_corpus = chunk[initial:match.start()]
                corpus.extend([[bytes([b]) for b in w.encode("utf-8")]  for w in re.findall(PAT, decode_corpus)])
                corpus.append([match.group()])
                initial = match.end()
                match = next(matches, None)
            else:
                decode_corpus = chunk[initial:]
                corpus.extend([[bytes([b]) for b in w.encode("utf-8")]  for w in re.findall(PAT, decode_corpus)])
                break
    return corpus
def processing(f,path, num_processes, special_tokens ):
    boundaries =  wawa_file_reader(f, num_processes, special_tokens )
    tasks=[(path, s, e , special_tokens) for s, e in zip(boundaries[:-1], boundaries[1:])] 
    with Pool(num_processes) as pool:
        flat = []
        for sub in pool.imap_unordered(work, tasks):
            flat.extend(sub)
    return flat
        
if __name__ == "__main__":
    path="tests/fixtures/corpus.en"
    with open(path, "rb") as f:
        num_processes = 10
        special_tokens=[b"<|endoftext|>"]
        flat = processing(f, num_processes, special_tokens )
    print(flat)
        
        
