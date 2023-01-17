import modules.scripts as scripts
import gradio as gr
import csv
import os
from collections import defaultdict

import modules.shared as shared
import difflib
import random

scripts_dir = scripts.basedir()
kw_idx = 0
hash_dict = None
hash_dict_modified = None
model_hash_dict = {}

def str_simularity(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()

def get_old_model_hash(filename):
    if filename in model_hash_dict:
        return model_hash_dict[filename]
    try:
        with open(filename, "rb") as file:
            import hashlib
            m = hashlib.sha256()

            file.seek(0x100000)
            m.update(file.read(0x10000))
            hash = m.hexdigest()[0:8]
            model_hash_dict[filename] = hash
            return hash
    except FileNotFoundError:
        return 'NOFILE'


class Script(scripts.Script):
    def title(self):
        return "Model keyword"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):

        def get_keywords():
            model_ckpt = os.path.basename(shared.sd_model.sd_checkpoint_info.filename)
            model_hash = get_old_model_hash(shared.sd_model.sd_checkpoint_info.filename)
            kws = self.get_keyword(model_hash, model_ckpt)
            mk_choices = ["keyword1, keyword2", "random", "iterate"]
            if kws:
                mk_choices.extend([x.strip() for x in kws.split('|')])
            else:
                mk_choices.extend(["keyword1", "keyword2"])
            return gr.Dropdown.update(choices=mk_choices)

        def check_keyword():
            model_ckpt = os.path.basename(shared.sd_model.sd_checkpoint_info.filename)
            model_hash = get_old_model_hash(shared.sd_model.sd_checkpoint_info.filename)
            # hash_dict = self.load_hash_dict()
            entry = self.get_keyword(model_hash, model_ckpt, return_entry=True)

            if entry:
                kw = entry[0]
                src = 'user-mappings.txt' if entry[2]==1 else 'user-keyword.txt (default database)'
                return f"filename={model_ckpt}\nhash={model_hash}\nkeyword={kw}\nmatch from {src}"
            else:
                return f"filename={model_ckpt}\nhash={model_hash}\nno match"

        def delete_keyword():
            model_ckpt = os.path.basename(shared.sd_model.sd_checkpoint_info.filename)
            model_hash = get_old_model_hash(shared.sd_model.sd_checkpoint_info.filename)
            # hash_dict = self.load_hash_dict()
            user_file = f'{scripts_dir}/custom-mappings.txt'
            user_backup_file = f'{scripts_dir}/custom-mappings-backup.txt'
            lines = []
            found = None

            if os.path.exists(user_file):
                with open(user_file, newline='') as csvfile:
                    csvreader = csv.reader(csvfile)
                    for row in csvreader:
                        try:
                            mhash = row[0]
                            if mhash.startswith('#'):
                                lines.append(','.join(row))
                                continue
                            # kw = row[1]
                            ckptname = None if len(row)<=2 else row[2].strip(' ')
                            if mhash==model_hash and ckptname==model_ckpt:
                                found = row
                                continue
                            lines.append(','.join(row))
                        except:
                            pass

            if found:
                csvtxt = '\n'.join(lines) + '\n'
                import shutil
                try:
                    shutil.copy(user_file, user_backup_file)
                except:
                    pass
                open(user_file, 'w').write(csvtxt)

                return f'deleted entry: {found}'
            else:
                return f'no custom mapping found'


        def add_custom(txt):
            txt = txt.strip()
            model_ckpt = os.path.basename(shared.sd_model.sd_checkpoint_info.filename)
            model_hash = get_old_model_hash(shared.sd_model.sd_checkpoint_info.filename)
            if len(txt) == 0:
                return "Fill keyword(trigger word) or keywords separated by | (pipe character)"
            insert_line = f'{model_hash}, {txt}, {model_ckpt}'
            global scripts_dir

            user_file = f'{scripts_dir}/custom-mappings.txt'
            user_backup_file = f'{scripts_dir}/custom-mappings-backup.txt'
            lines = []

            if os.path.exists(user_file):
                with open(user_file, newline='') as csvfile:
                    csvreader = csv.reader(csvfile)
                    for row in csvreader:
                        try:
                            mhash = row[0]
                            if mhash.startswith('#'):
                                lines.append(','.join(row))
                                continue
                            # kw = row[1]
                            ckptname = None if len(row)<=2 else row[2].strip(' ')
                            if mhash==model_hash and ckptname==model_ckpt:
                                continue
                            lines.append(','.join(row))
                        except:
                            pass
            lines.append(insert_line)
            csvtxt = '\n'.join(lines) + '\n'
            import shutil
            try:
                shutil.copy(user_file, user_backup_file)
            except:
                pass
            open(user_file, 'w').write(csvtxt)

            return 'added: ' + insert_line

        with gr.Group():
            with gr.Accordion('Model Keyword', open=False):
                is_enabled = gr.Checkbox(label='Model Keyword Enabled', value=True)

                keyword_placement = gr.Dropdown(choices=["keyword prompt", "prompt keyword", "keyword, prompt", "prompt, keyword"], 
                                value='keyword prompt',
                                label='Keyword placement:')

                mk_choices = ["keyword1, keyword2", "random", "iterate"]
                mk_choices.extend(["keyword1", "keyword2"])

                # css = '#mk_refresh_btn { min-width: 2.3em; height: 2.5em; flex-grow: 0; margin-top: 0.4em; margin-right: 1em; padding-left: 0.25em; padding-right: 0.25em;}'
                # with gr.Blocks(css=css):
                with gr.Row(equal_height=True):
                    multiple_keywords = gr.Dropdown(choices=mk_choices,
                                    value='keyword1, keyword2',
                                    label='Multiple keywords:')
                    refresh_btn = gr.Button(value='\U0001f504', elem_id='mk_refresh_btn_random_seed')
                refresh_btn.click(get_keywords, inputs=None, outputs=multiple_keywords)

                with gr.Accordion('Add Custom Mappings', open=False):
                    info = gr.HTML("<p style=\"margin-bottom:0.75em\">Add custom keyword(trigger word) mapping for current model. Custom mappings are saved to extensions/model-keyword/custom-mappings.txt</p>")
                    text_input = gr.Textbox(placeholder="Keyword or keywords separated by |", label="Keyword(trigger word)")
                    with gr.Row():
                        check_mappings = gr.Button(value='Check')
                        add_mappings = gr.Button(value='Save')
                        delete_mappings = gr.Button(value='Delete')

                    text_output = gr.Textbox(interactive=False, label='result')

                    add_mappings.click(add_custom, inputs=text_input, outputs=text_output)
                    check_mappings.click(check_keyword, inputs=None, outputs=text_output)
                    delete_mappings.click(delete_keyword, inputs=None, outputs=text_output)


        return [is_enabled, keyword_placement, multiple_keywords]

    def load_hash_dict(self):
        global hash_dict, hash_dict_modified, scripts_dir

        default_file = f'{scripts_dir}/model-keyword.txt'
        user_file = f'{scripts_dir}/custom-mappings.txt'
        modified = str(os.stat(default_file).st_mtime) + '_' + str(os.stat(user_file).st_mtime)

        if hash_dict is None or hash_dict_modified != modified:
            hash_dict = defaultdict(list)
            def parse_file(path, idx):
                if os.path.exists(path):
                    with open(path, newline='') as csvfile:
                        csvreader = csv.reader(csvfile)
                        for row in csvreader:
                            try:
                                mhash = row[0].strip(' ')
                                kw = row[1].strip(' ')
                                if mhash.startswith('#'):
                                    continue
                                ckptname = 'default' if len(row)<=2 else row[2].strip(' ')
                                hash_dict[mhash].append((kw, ckptname,idx))
                            except:
                                pass

            parse_file(default_file, 0) # 0 for default_file
            parse_file(user_file, 1) # 1 for user_file

            hash_dict_modified = modified

        return hash_dict

    def get_keyword(self, model_hash, model_ckpt, return_entry=False):
        found = None

        # hash -> [ (keyword, ckptname, idx) ]
        hash_dict = self.load_hash_dict()

        # print(hash_dict)

        if model_hash in hash_dict:
            lst = hash_dict[model_hash]
            if len(lst) == 1:
                found = lst[0]

            elif len(lst) > 1:
                max_sim = 0.0
                found = lst[0]
                for kw_ckpt in lst:
                    sim = str_simularity(kw_ckpt[1], model_ckpt)
                    if sim >= max_sim:
                        max_sim = sim
                        found = kw_ckpt
        if return_entry:
            return found
        return found[0] if found else None
            

    def process(self, p, is_enabled, keyword_placement, multiple_keywords):

        if not is_enabled:
            global hash_dict
            hash_dict = None
            return

        model_ckpt = os.path.basename(shared.sd_model.sd_checkpoint_info.filename)
        model_hash = get_old_model_hash(shared.sd_model.sd_checkpoint_info.filename)
        # print(f'model_hash = {model_hash}')

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
                elif multiple_keywords in kws:
                    kw = multiple_keywords
                else:
                    kw = kws[0]
                    
            if keyword_placement == 'keyword prompt':
                return kw + ' ' + prompt
            elif keyword_placement == 'keyword, prompt':
                return kw + ', ' + prompt
            elif keyword_placement == 'prompt keyword':
                return prompt + ' ' + kw
            elif keyword_placement == 'prompt, keyword':
                return prompt + ', ' + kw
            return kw + ' ' + prompt

        kw = self.get_keyword(model_hash, model_ckpt)

        if kw is not None:
            p.prompt = new_prompt(p.prompt, kw, no_iter=True)
            p.all_prompts = [new_prompt(prompt, kw) for prompt in p.all_prompts]
