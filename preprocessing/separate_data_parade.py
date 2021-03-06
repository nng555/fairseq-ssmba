import os
import jsonlines as jsonl
import numpy as np
import csv

def separate(base_dir):
    if not os.path.exists(os.path.join(base_dir, 'orig')):
        os.makedirs(os.path.join(base_dir, 'orig'))
    for split in ['train', 'validation', 'test']:
        base_file = open(os.path.join(base_dir, 'PARADE_' + split + '.txt'))
        res = []
        for ex in csv.reader(base_file, delimiter='\t', quoting=csv.QUOTE_NONE):
            res.append([ex[3], ex[4], ex[1]])
        print(len(res))
        if 'validation' in split:
            split = 'valid'

        with open(os.path.join(base_dir, 'orig', split + '.raw.input0'), 'w') as file0, \
             open(os.path.join(base_dir, 'orig', split + '.raw.input1'), 'w') as file1, \
             open(os.path.join(base_dir, 'orig', split + '.raw.label'), 'w') as filelab:

            for entry in res:
                file0.write(entry[0] + '\n')
                file1.write(entry[1] + '\n')
                filelab.write(entry[2] + '\n')

if __name__ == "__main__":
    separate('/scratch/ssd001/datasets/nng_dataset/paraphrase/parade')

