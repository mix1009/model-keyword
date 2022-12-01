import modules.scripts as scripts
import gradio as gr
import csv
import os

scripts_dir = scripts.basedir()

from modules.processing import process_images
import modules.shared as shared
import difflib
import random

kw_idx = 0

def str_simularity(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()

class Script(scripts.Script):
    def title(self):
        return "Model keyword"

    def ui(self, is_img2img):
        info = gr.HTML("<p style=\"margin-bottom:0.75em\">You can edit extensions/model-keyword/model-keyword-user.txt to add custom mappings</p>")

        keyword_placement = gr.Dropdown(choices=["keyword prompt", "prompt keyword", "keyword, prompt", "prompt, keyword"],
                                 value='keyword prompt',
                                 label='Keyword placement:')

        multiple_keywords = gr.Dropdown(choices=["keyword1, keyword2", "random", "iterate", "keyword1", "keyword2"],
                                 value='keyword1, keyword2',
                                 label='Multiple keywords:')

        return [info, keyword_placement, multiple_keywords]

    def run(self, p, _, keyword_placement, multiple_keywords):

        # hash -> [ (keyword, ckptname) ]
        mp_dict = {}
        def parse_file(filename):
            with open(f'{scripts_dir}/{filename}', newline='') as csvfile:
                csvreader = csv.reader(csvfile)
                for row in csvreader:
                    try:
                        mhash = row[0].strip(' ')
                        kw = row[1].strip(' ')
                        if mhash.startswith('#'):
                            continue
                        ckptname = 'default' if len(row)<=2 else row[2].strip(' ')
                        if mhash in mp_dict:
                            lst = mp_dict[mhash]
                            lst.append((kw, ckptname))
                            mp_dict[mhash] = lst
                        else:
                            mp_dict[mhash] = [(kw, ckptname)]
                    except:
                        pass

        parse_file('model-keyword.txt')
        parse_file('model-keyword-user.txt')

        # print(mp_dict)

        model_ckpt = os.path.basename(shared.sd_model.sd_checkpoint_info.filename)
        model_hash = shared.sd_model.sd_model_hash

        def new_prompt(prompt, kw):
            global kw_idx
            kws = kw.split('|')
            if len(kws) > 1:
                kws = [x.strip(' ') for x in kws]
                if multiple_keywords=="keyword1, keyword2":
                    kw = ', '.join(kws)
                elif multiple_keywords=="random":
                    kw = random.choice(kws)
                elif multiple_keywords=="iterate":
                    kw = kws[kw_idx%len(kws)]
                    kw_idx += 1
                elif multiple_keywords=="keyword1":
                    kw = kws[0]
                elif multiple_keywords=="keyword2":
                    kw = kws[1]


            if keyword_placement == 'keyword prompt':
                return kw + ' ' + prompt
            elif keyword_placement == 'keyword, prompt':
                return kw + ', ' + prompt
            elif keyword_placement == 'prompt keyword':
                return prompt + ' ' + kw
            elif keyword_placement == 'prompt, keyword':
                return prompt + ', ' + kw
            return kw + ' ' + prompt

        if model_hash in mp_dict:
            lst = mp_dict[model_hash]
            if len(lst) == 1:
                kw = lst[0][0]
                p.prompt = new_prompt(p.prompt, kw)
            elif len(lst) > 1:
                max_sim = 0.0
                kw = lst[0][0]
                for kw_ckpt in lst:
                    sim = str_simularity(kw_ckpt[1], model_ckpt)
                    if sim >= max_sim:
                        max_sim = sim
                        kw = kw_ckpt[0]
                p.prompt = new_prompt(p.prompt, kw)


        return process_images(p)

