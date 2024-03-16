import modules.scripts as scripts
import gradio as gr
import csv
import os
from collections import defaultdict

import modules.shared as shared
import difflib
import random
import glob
import hashlib
import shutil
import fnmatch

scripts_dir = scripts.basedir()
kw_idx = 0
lora_idx = 0
hash_dict = None
hash_dict_modified = None
lora_hash_dict = None
lora_hash_dict_modified = None

model_hash_dict = {}

def str_simularity(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()

def get_old_model_hash(filename):
    if filename in model_hash_dict:
        return model_hash_dict[filename]
    try:
        with open(filename, "rb") as file:
            m = hashlib.sha256()

            file.seek(0x100000)
            m.update(file.read(0x10000))
            hash = m.hexdigest()[0:8]
            model_hash_dict[filename] = hash
            return hash
    except FileNotFoundError:
        return 'NOFILE'

def find_files(directory, exts):
    for root, dirs, files in os.walk(directory):
        for ext in exts:
            pattern = f'*.{ext}'
            for filename in fnmatch.filter(files, pattern):
                yield os.path.relpath(os.path.join(root, filename), directory)

def load_hash_dict():
    global hash_dict, hash_dict_modified, scripts_dir

    default_file = f'{scripts_dir}/model-keyword.txt'
    user_file = f'{scripts_dir}/custom-mappings.txt'

    if not os.path.exists(user_file):
        open(user_file, 'w').write('\n')

    modified = str(os.stat(default_file).st_mtime) + '_' + str(os.stat(user_file).st_mtime)

    if hash_dict is None or hash_dict_modified != modified:
        hash_dict = defaultdict(list)
        def parse_file(path, idx):
            if os.path.exists(path):
                with open(path, newline='', encoding='utf-8') as csvfile:
                    csvreader = csv.reader(csvfile)
                    for row in csvreader:
                        try:
                            mhash = row[0].strip(' ')
                            kw = row[1].strip(' ')
                            if mhash.startswith('#'):
                                continue
                            mhash = mhash.lower()
                            ckptname = 'default' if len(row)<=2 else row[2].strip(' ')
                            hash_dict[mhash].append((kw, ckptname,idx))
                        except:
                            pass

        parse_file(default_file, 0) # 0 for default_file
        parse_file(user_file, 1) # 1 for user_file

        hash_dict_modified = modified

    return hash_dict

def load_lora_hash_dict():
    global lora_hash_dict, lora_hash_dict_modified, scripts_dir

    default_file = f'{scripts_dir}/lora-keyword.txt'
    user_file = f'{scripts_dir}/lora-keyword-user.txt'

    if not os.path.exists(user_file):
        open(user_file, 'w').write('\n')

    modified = str(os.stat(default_file).st_mtime) + '_' + str(os.stat(user_file).st_mtime)

    if lora_hash_dict is None or lora_hash_dict_modified != modified:
        lora_hash_dict = defaultdict(list)
        def parse_file(path, idx):
            if os.path.exists(path):
                with open(path, encoding='utf-8', newline='') as csvfile:
                    csvreader = csv.reader(csvfile)
                    for row in csvreader:
                        try:
                            mhash = row[0].strip(' ')
                            kw = row[1].strip(' ')
                            if mhash.startswith('#'):
                                continue
                            mhash = mhash.lower()
                            ckptname = 'default' if len(row)<=2 else row[2].strip(' ')
                            lora_hash_dict[mhash].append((kw, ckptname,idx))
                        except:
                            pass

        parse_file(default_file, 0) # 0 for default_file
        parse_file(user_file, 1) # 1 for user_file

        lora_hash_dict_modified = modified

    return lora_hash_dict

def get_keyword_for_model(model_hash, model_ckpt, return_entry=False):
    found = None

    # hash -> [ (keyword, ckptname, idx) ]
    hash_dict = load_hash_dict()

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

def _get_keywords_for_lora(lora_model, return_entry=False):
    found = None

    lora_model_path = f'{shared.cmd_opts.lora_dir}/{lora_model}'

    # hash -> [ (keyword, ckptname, idx) ]
    lora_hash_dict = load_lora_hash_dict()

    lora_model_hash = get_old_model_hash(lora_model_path)

    if lora_model_hash in lora_hash_dict:
        lst = lora_hash_dict[lora_model_hash]
        if len(lst) == 1:
            found = lst[0]

        elif len(lst) > 1:
            max_sim = 0.0
            found = lst[0]
            for kw_ckpt in lst:
                sim = str_simularity(kw_ckpt[1], lora_model)
                if sim >= max_sim:
                    max_sim = sim
                    found = kw_ckpt
    if return_entry:
        return found
    return found[0] if found else None

def get_lora_keywords(lora_model, keyword_only=False):
    lora_keywords = ["None"]
    if lora_model != 'None':
        kws = _get_keywords_for_lora(lora_model)
        if kws:
            words = [x.strip() for x in kws.split('|')]
            if keyword_only:
                return words
            if len(words) > 1:
                words.insert(0, ', '.join(words))
                words.append('< iterate >')
                words.append('< random >')
            lora_keywords.extend(words)

    return lora_keywords
settings = None

def save_settings(m):
    global scripts_dir, settings
    
    if settings is None:
        settings = get_settings()
    
    for k in m.keys():
        settings[k] = m[k]

    # print(settings)

    settings_file = f'{scripts_dir}/settings.txt'

    lines = []
    for k in settings.keys():
        lines.append(f'{k}={settings[k]}')
    csvtxt = '\n'.join(lines)+'\n'
    open(settings_file, 'w').write(csvtxt)
    
def get_settings():
    global scripts_dir, settings
    if settings:
        return settings

    settings = {}

    settings['is_enabled'] = 'False'
    settings['keyword_placement'] = 'keyword prompt'
    settings['multiple_keywords'] = 'keyword1, keyword2'
    settings['ti_keywords'] = 'None'
    settings['keyword_order'] = 'textual inversion first'
    settings['lora_model'] = 'None'
    settings['lora_multiplier'] = 0.7
    settings['lora_keywords'] = 'None'

    settings_file = f'{scripts_dir}/settings.txt'

    if os.path.exists(settings_file):    
        with open(settings_file, newline='') as file:
            for line in file.read().split('\n'):
                pos = line.find('=')
                if pos == -1: continue
                k = line[:pos]
                v = line[pos+1:].strip()
                settings[k] = v

    return settings

class Script(scripts.Script):
    def title(self):
        return "Model keyword"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        def get_embeddings():
            return [os.path.basename(x) for x in glob.glob(f'{shared.cmd_opts.embeddings_dir}/*.pt')]
        def get_loras():
            return sorted(list(find_files(shared.cmd_opts.lora_dir,['safetensors','ckpt','pt'])), key=str.casefold)
            # return [os.path.basename(x) for x in glob.glob(f'{shared.cmd_opts.lora_dir}/*.safetensors')]

        def update_keywords():
            model_ckpt = os.path.basename(shared.sd_model.sd_checkpoint_info.filename)
            model_hash = get_old_model_hash(shared.sd_model.sd_checkpoint_info.filename)
            kws = get_keyword_for_model(model_hash, model_ckpt)
            mk_choices = ["keyword1, keyword2", "random", "iterate"]
            if kws:
                mk_choices.extend([x.strip() for x in kws.split('|')])
            else:
                mk_choices.extend(["keyword1", "keyword2"])
            return gr.Dropdown.update(choices=mk_choices)
        def update_embeddings():
            ti_choices = ["None"]
            ti_choices.extend(get_embeddings())
            return gr.Dropdown.update(choices=ti_choices)
        def update_loras():
            lora_choices = ["None"]
            lora_choices.extend(get_loras())
            return gr.Dropdown.update(choices=lora_choices)


        def update_lora_keywords(lora_model):
            lora_keywords = get_lora_keywords(lora_model)
            return gr.Dropdown.update(choices=lora_keywords)

        def check_keyword():
            model_ckpt = os.path.basename(shared.sd_model.sd_checkpoint_info.filename)
            model_hash = get_old_model_hash(shared.sd_model.sd_checkpoint_info.filename)
            entry = get_keyword_for_model(model_hash, model_ckpt, return_entry=True)

            if entry:
                kw = entry[0]
                src = 'custom-mappings.txt' if entry[2]==1 else 'model-keyword.txt (default database)'
                return f"filename={model_ckpt}\nhash={model_hash}\nkeyword={kw}\nmatch from {src}"
            else:
                return f"filename={model_ckpt}\nhash={model_hash}\nno match"

        def delete_keyword():
            model_ckpt = os.path.basename(shared.sd_model.sd_checkpoint_info.filename)
            model_hash = get_old_model_hash(shared.sd_model.sd_checkpoint_info.filename)
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
            try:
                shutil.copy(user_file, user_backup_file)
            except:
                pass
            open(user_file, 'w').write(csvtxt)

            return 'added: ' + insert_line

        def delete_lora_keyword(lora_model):
            model_ckpt = lora_model
            lora_model_path = f'{shared.cmd_opts.lora_dir}/{lora_model}'
            model_hash = get_old_model_hash(lora_model_path)
            user_file = f'{scripts_dir}/lora-keyword-user.txt'
            user_backup_file = f'{scripts_dir}/lora-keyword-user-backup.txt'
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

            outline = ''
            if found:
                csvtxt = '\n'.join(lines) + '\n'
                try:
                    shutil.copy(user_file, user_backup_file)
                except:
                    pass
                open(user_file, 'w').write(csvtxt)

                outline = f'deleted entry: {found}'
            else:
                outline = f'no custom mapping found'
            lora_keywords = get_lora_keywords(lora_model)
            return [outline, gr.Dropdown.update(choices=lora_keywords)]


        def add_lora_keyword(txt, lora_model):
            txt = txt.strip()
            model_ckpt = lora_model
            lora_model_path = f'{shared.cmd_opts.lora_dir}/{lora_model}'
            model_hash = get_old_model_hash(lora_model_path)
            if len(txt) == 0:
                return "Fill keyword(trigger word) or keywords separated by | (pipe character)"
            insert_line = f'{model_hash}, {txt}, {model_ckpt}'
            global scripts_dir

            user_file = f'{scripts_dir}/lora-keyword-user.txt'
            user_backup_file = f'{scripts_dir}/lora-keyword-user-backup.txt'
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
            try:
                shutil.copy(user_file, user_backup_file)
            except:
                pass
            open(user_file, 'w').write(csvtxt)

            lora_keywords = get_lora_keywords(lora_model)
            return ['added: ' + insert_line, gr.Dropdown.update(choices=lora_keywords)]

        settings = get_settings()

        def cb_enabled():
            return True if settings['is_enabled']=='True' else False
        def cb_keyword_placement():
            return settings['keyword_placement']
        def cb_multiple_keywords():
            return settings['multiple_keywords']
        def cb_ti_keywords():
            return settings['ti_keywords']
        def cb_lora_model():
            return settings['lora_model']
        def cb_lora_multiplier():
            return settings['lora_multiplier']
        def cb_lora_keywords():
            return settings['lora_keywords']
        def cb_keyword_order():
            return settings['keyword_order']

        refresh_icon = '\U0001f504'
        with gr.Group():
            with gr.Accordion('Model Keyword', open=False):

                is_enabled = gr.Checkbox(label='Model Keyword Enabled ', value=cb_enabled)
                setattr(is_enabled,"do_not_save_to_config",True)

                placement_choices = ["keyword prompt", "prompt keyword", "keyword, prompt", "prompt, keyword"]
                keyword_placement = gr.Dropdown(choices=placement_choices,
                                value=cb_keyword_placement,
                                label='Keyword placement: ')
                setattr(keyword_placement,"do_not_save_to_config",True)

                mk_choices = ["keyword1, keyword2", "random", "iterate"]
                mk_choices.extend(["keyword1", "keyword2"])

                # css = '#mk_refresh_btn { min-width: 2.3em; height: 2.5em; flex-grow: 0; margin-top: 0.4em; margin-right: 1em; padding-left: 0.25em; padding-right: 0.25em;}'
                # with gr.Blocks(css=css):
                with gr.Row(equal_height=True):
                    multiple_keywords = gr.Dropdown(choices=mk_choices,
                                    value=cb_multiple_keywords,
                                    label='Multiple keywords: ')
                    setattr(multiple_keywords,"do_not_save_to_config",True)

                    refresh_btn = gr.Button(value=refresh_icon, elem_id='mk_refresh_btn_random_seed') # XXX _random_seed workaround.
                refresh_btn.click(update_keywords, inputs=None, outputs=multiple_keywords)

                ti_choices = ["None"]
                ti_choices.extend(get_embeddings())
                with gr.Row(equal_height=True):
                    ti_keywords = gr.Dropdown(choices=ti_choices,
                                    value=cb_ti_keywords,
                                    label='Textual Inversion (Embedding): ')
                    setattr(ti_keywords,"do_not_save_to_config",True)
                    refresh_btn = gr.Button(value=refresh_icon, elem_id='ti_refresh_btn_random_seed') # XXX _random_seed workaround.
                refresh_btn.click(update_embeddings, inputs=None, outputs=ti_keywords)

                keyword_order = gr.Dropdown(choices=["textual inversion first", "model keyword first"], 
                                value=cb_keyword_order,
                                label='Keyword order: ')
                setattr(keyword_order,"do_not_save_to_config",True)


                with gr.Accordion('LORA', open=True):
                    lora_choices = ["None"]
                    lora_choices.extend(get_loras())
                    lora_kw_choices = get_lora_keywords(settings['lora_model'])

                    with gr.Row(equal_height=True):
                        lora_model = gr.Dropdown(choices=lora_choices,
                                        value=cb_lora_model,
                                        label='Model: ')
                        setattr(lora_model,"do_not_save_to_config",True)
                        lora_refresh_btn = gr.Button(value=refresh_icon, elem_id='lora_m_refresh_btn_random_seed') # XXX _random_seed workaround.
                        lora_refresh_btn.click(update_loras, inputs=None, outputs=lora_model)

                        lora_multiplier = gr.Slider(minimum=0,maximum=2, step=0.01, value=cb_lora_multiplier, label="multiplier")
                    with gr.Row(equal_height=True):
                        lora_keywords = gr.Dropdown(choices=lora_kw_choices,
                                        value=cb_lora_keywords,
                                        label='keywords: ')
                        setattr(lora_keywords,"do_not_save_to_config",True)

                        lora_model.change(fn=update_lora_keywords,inputs=lora_model, outputs=lora_keywords)
                    info = gr.HTML("<p style=\"margin-bottom:0.75em\">Add custom keyword(trigger word) mapping for selected LORA model.</p>")
                    lora_text_input = gr.Textbox(placeholder="Keyword or keywords separated by |", label="Keyword(trigger word)")
                    with gr.Row():
                        add_mappings = gr.Button(value='Save')
                        delete_mappings = gr.Button(value='Delete')
                    lora_text_output = gr.Textbox(interactive=False, label='result')
                    add_mappings.click(add_lora_keyword, inputs=[lora_text_input, lora_model], outputs=[lora_text_output, lora_keywords])
                    delete_mappings.click(delete_lora_keyword, inputs=lora_model, outputs=[lora_text_output, lora_keywords])

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


        return [is_enabled, keyword_placement, multiple_keywords, ti_keywords, keyword_order, lora_model, lora_multiplier, lora_keywords]

    def process(self, p, is_enabled, keyword_placement, multiple_keywords, ti_keywords, keyword_order, lora_model, lora_multiplier, lora_keywords):
        if lora_model != 'None':
            if lora_keywords not in get_lora_keywords(lora_model):
                lora_keywords = 'None'

        save_settings({
            'is_enabled': f'{is_enabled}',
            'keyword_placement': keyword_placement,
            'multiple_keywords': multiple_keywords,
            'ti_keywords': ti_keywords,
            'keyword_order': keyword_order,
            'lora_model': lora_model,
            'lora_multiplier': lora_multiplier,
            'lora_keywords': lora_keywords,
        })

        if not is_enabled:
            global hash_dict
            hash_dict = None
            return

        model_ckpt = os.path.basename(shared.sd_model.sd_checkpoint_info.filename)
        model_hash = get_old_model_hash(shared.sd_model.sd_checkpoint_info.filename)
        # print(f'model_hash = {model_hash}')

        def new_prompt(prompt, kw, no_iter=False):
            global kw_idx, lora_idx
            if kw:
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

            arr = [kw]

            ti = None
            if ti_keywords != 'None':
                ti = ti_keywords[:ti_keywords.rfind('.')]

            lora = None
            if lora_keywords != 'None' and lora_model != 'None':
                lora = lora_keywords
                try:
                    if lora == '< iterate >':
                        loras = get_lora_keywords(lora_model, keyword_only=True)
                        lora = loras[lora_idx%len(loras)]
                        if not no_iter:
                            lora_idx += 1
                    elif lora == '< random >':
                        loras = get_lora_keywords(lora_model, keyword_only=True)
                        lora = random.choice(loras)
                except:
                    pass

            if keyword_order == 'model keyword first':
                arr = [kw, lora, ti]
            else:
                arr = [ti, lora, kw]

            while None in arr:
                arr.remove(None)

            if keyword_placement.startswith('keyword'):
                arr.append(prompt)
            else:
                arr.insert(0, prompt)

            if lora_model != 'None':
                lora_name = lora_model[:lora_model.rfind('.')]
                lora_name = lora_name.replace('\\', '/')
                lora_name = lora_name.split('/')[-1]
                arr.insert(0, f'<lora:{lora_name}:{lora_multiplier}>')

            if ',' in keyword_placement:
                return ', '.join(arr)
            else:
                return ' '.join(arr)


        kw = get_keyword_for_model(model_hash, model_ckpt)

        if kw is not None or ti_keywords != 'None' or lora_model != 'None':
            p.prompt = new_prompt(p.prompt, kw, no_iter=True)
            p.all_prompts = [new_prompt(prompt, kw) for prompt in p.all_prompts]


from fastapi import FastAPI, Response, Query, Body
from fastapi.responses import JSONResponse


def model_keyword_api(_: gr.Blocks, app: FastAPI):
    @app.get("/model_keyword/get_keywords")
    async def get_keywords():
        model_ckpt = os.path.basename(shared.sd_model.sd_checkpoint_info.filename)
        model_hash = get_old_model_hash(shared.sd_model.sd_checkpoint_info.filename)
        r = get_keyword_for_model(model_hash, model_ckpt, return_entry=True)
        if r is None:
            return {"keywords": [], "model": model_ckpt, "hash": model_hash, "match_source": "no match"}
        kws = [x.strip() for x in r[0].split('|')]
        match_source = "model-keyword.txt" if r[2]==0 else "custom-mappings.txt"
        return {"keywords": kws, "model": model_ckpt, "hash": model_hash, "match_source": match_source}

    # @app.get("/model_keyword/get_raw_keywords")
    # async def get_raw_keywords():
    #     model_ckpt = os.path.basename(shared.sd_model.sd_checkpoint_info.filename)
    #     model_hash = get_old_model_hash(shared.sd_model.sd_checkpoint_info.filename)
    #     kw = get_keyword_for_model(model_hash, model_ckpt)
    #     return {"keywords": kw, "model": model_ckpt, "hash": model_hash}

try:
    import modules.script_callbacks as script_callbacks

    script_callbacks.on_app_started(model_keyword_api)
except:
    pass
