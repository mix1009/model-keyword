import modules.scripts as scripts
import gradio as gr
import csv
import os

import modules.shared as shared
import difflib
import random

scripts_dir = scripts.basedir()
kw_idx = 0
hash_dict = None
hash_dict_modified = None

def str_simularity(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()

class Script(scripts.Script):
    def title(self):
        return "Model keyword"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with gr.Group():
            with gr.Accordion('Model Keyword', open=False):
                is_enabled = gr.Checkbox(label='Model Keyword Enabled', value=True)
                info = gr.HTML("<p style=\"margin-bottom:0.75em\">You can edit extensions/model-keyword/model-keyword-user.txt to add custom mappings</p>")

                keyword_placement = gr.Dropdown(choices=["keyword prompt", "prompt keyword", "keyword, prompt", "prompt, keyword"], 
                                value='keyword prompt',
                                label='Keyword placement:')

                multiple_keywords = gr.Dropdown(choices=["keyword1, keyword2", "random", "iterate", "keyword1", "keyword2"],
                                 value='keyword1, keyword2',
                                 label='Multiple keywords:')

        return [is_enabled, info, keyword_placement, multiple_keywords]

    def load_hash_dict(self):
        global hash_dict, hash_dict_modified, scripts_dir

        default_file = f'{scripts_dir}/model-keyword.txt'
        user_file = f'{scripts_dir}/model-keyword-user.txt'
        modified = str(os.stat(default_file).st_mtime) + '_' + str(os.stat(user_file).st_mtime)

        if hash_dict is None or hash_dict_modified != modified:
            hash_dict = {}
            def parse_file(path):
                with open(path, newline='') as csvfile:
                    csvreader = csv.reader(csvfile)
                    for row in csvreader:
                        try:
                            mhash = row[0].strip(' ')
                            kw = row[1].strip(' ')
                            if mhash.startswith('#'):
                                continue
                            ckptname = 'default' if len(row)<=2 else row[2].strip(' ')
                            if mhash in hash_dict:
                                lst = hash_dict[mhash]
                                lst.append((kw, ckptname))
                                hash_dict[mhash] = lst
                            else:
                                hash_dict[mhash] = [(kw, ckptname)]
                        except:
                            pass

            parse_file(default_file)
            parse_file(user_file)

            hash_dict_modified = modified

        return hash_dict

    def process(self, p, is_enabled, _, keyword_placement, multiple_keywords):

        if not is_enabled:
            global hash_dict
            hash_dict = None
            return

        # hash -> [ (keyword, ckptname) ]
        hash_dict = self.load_hash_dict()

        # print(hash_dict)

        model_ckpt = os.path.basename(shared.sd_model.sd_checkpoint_info.filename)
        model_hash = shared.sd_model.sd_model_hash

        def new_prompt(prompt, kw, no_iter=False):
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
                    if not no_iter:
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

        if model_hash in hash_dict:
            lst = hash_dict[model_hash]
            kw = None
            if len(lst) == 1:
                kw = lst[0][0]
            elif len(lst) > 1:
                max_sim = 0.0
                kw = lst[0][0]
                for kw_ckpt in lst:
                    sim = str_simularity(kw_ckpt[1], model_ckpt)
                    if sim >= max_sim:
                        max_sim = sim
                        kw = kw_ckpt[0]
            if kw is not None:
                p.prompt = new_prompt(p.prompt, kw, no_iter=True)
                p.all_prompts = [new_prompt(prompt, kw) for prompt in p.all_prompts]
