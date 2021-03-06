import os
from operator import add
import json
import argparse
import numpy as np

import hydra
from omegaconf import DictConfig
from hydra import slurm_utils

@hydra.main(config_path=os.path.expandvars('$HOME/conf/$PROJ'), config_name='config')
def display_results(cfg: DictConfig):
    res_string = ""
    std_string = ""

    if cfg.data.task in ['nli', 'nng_dataset']:
        base_path = '/scratch/ssd001/datasets/'
    elif cfg.data.task in ['sentiment', 'translation', 'robust', 'pretrain']:
        base_path = '/h/nng/data'
    else:
        raise Exception('task %s data path not found'.format(cfg.data.task))

    d_path = os.path.join(base_path, cfg.data.task, cfg.data.name)
    label_dictf = open(os.path.join(d_path, 'label.dict.txt')).readlines()

    label_dict = {}
    for i in range(len(label_dictf)):
        label_dict[i] = label_dictf[i].split()[0]

    if cfg.eval.noisy:
        cfg.display.dir.name[0] = 'eval_noisy_gen'
        if cfg.eval.mask_prob:
            cfg.display.dir.name.append(cfg.eval.mask_prob)

    if cfg.data.task == 'translation':
        cfg.display.dir.name[0] = 'eval_bleu'

    if cfg.extra:
        cfg.display.dir.name.append(cfg.extra)

    if cfg.gen.seed is not None:
        cfg.display.dir.name[3] = '_'.join(cfg.display.dir.name[3].split('_')[:-1])

    for fdset in cfg.data.display.fdset:
        cfg.display.dir.name[2] = fdset
        for noise in empty_to_list(cfg.display.noise):
            cfg.display.dir.name[1] = noise
            row = []
            std_row = []
            var_row = []

            for tdset in cfg.data.display.tdset:
                cfg.display.dir.name[5] = tdset
                #cfg.data.sdset=tdset
                seed_res = []

                for seed in empty_to_list(cfg.display.seed):
                    cfg.display.dir.name[6] = seed

                    for gen_seed in empty_to_list(cfg.gen.seed):
                        cfg.display.dir.name[4] = gen_seed

                        final_res = {}
                        final_target = None

                        for mask_noise in empty_to_list(cfg.display.mask_prob):
                            cfg.gen.mask_prob = mask_noise
                            #print(cfg.display.dir.name)
                            #print(slurm_utils.resolve_name(cfg.display.dir.name))
                            display_dir = os.path.join('/h/nng/slurm', cfg.display.dir.date, slurm_utils.resolve_name(cfg.display.dir.name))

                            if not os.path.exists(display_dir) or not os.path.exists(os.path.join(display_dir, 'eval_status.json')):
                                #print("{} does not exist!".format(display_dir))
                                continue
                            if os.stat(os.path.join(display_dir, 'eval_status.json')).st_size == 0:
                                continue

                            eval_res, eval_target, _ = json.load(open(os.path.join(display_dir, 'eval_status.json')))
                            if not final_target:
                                final_target = eval_target
                            for k, v in eval_res.items():
                                if k not in final_res:
                                    final_res[k] = v
                                else:
                                    final_res[k] = list(map(add, final_res[k], v))

                        if not final_res:
                            continue

                        nval = 0
                        nsamples = 0

                        for k in final_res:
                            prediction = np.asarray(final_res[k]).argmax()
                            prediction_label = label_dict[prediction]
                            nval += int(prediction_label == final_target[k])
                            nsamples += 1

                        seed_res.append(float(nval)/nsamples)

                if seed_res == []:
                    row.append(0)
                    std_row.append(0)
                    var_row.append(0)
                    continue

                if len(seed_res) != 1:
                    print(seed_res)
                    row.append(np.average(seed_res))
                    std_row.append(np.std(seed_res))
                    var_row.append(np.var(seed_res))
                else:
                    row.append(seed_res[0])
                    std_row.append(0)
                    var_row.append(0)
            res_string = res_string + '\t'.join([str(round(val, 4)) for val in row]) + '\n'
            ood_std = np.sqrt(np.average([v for i,v in enumerate(var_row) if i != cfg.data.display.fdset.index(fdset)]))
            std_string = std_string + '\t'.join([str(val) for val in std_row] + [str(ood_std)]) + '\n'
        res_string = res_string + '\n'
        std_string = std_string + '\n'
    print(res_string)
    print(std_string)

def empty_to_list(l):
    if l is None:
        return [None]
    else:
        return list(l)

if __name__ == "__main__":
    display_results()

