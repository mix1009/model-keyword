# model-keyword
Automatic1111 WEBUI extension to autofill keyword for custom stable diffusion models.

[model-keyword-github.webm](https://user-images.githubusercontent.com/1288793/205525862-a8eaebfe-1860-41d1-bc66-335896b467dd.webm)

## Installation

Copy the url of the repository ( https://github.com/mix1009/model-keyword ) into the extension tab and press "Install"

<img width="936" alt="Screenshot 2022-12-01 at 12 14 25 PM" src="https://user-images.githubusercontent.com/1288793/204957471-63712085-783b-437b-9925-ee8f935093f7.png">

From "Extensions/Installed" tab press "Apply and restart UI".
<img width="925" alt="Screenshot 2022-12-01 at 12 18 43 PM" src="https://user-images.githubusercontent.com/1288793/204958071-357d1c9b-22aa-47fc-98b4-582349b1b0cd.png">

## Usage
From txt2img, img2img tab, "Model Keyword" section is added. Model keyword extension is enabled by default. Click Model Keyword or triangle to reveal options.

![reveal](https://user-images.githubusercontent.com/1288793/205526835-fd95274b-a0db-423a-a2ca-20c0057bab02.png)

When generating image, the extension will try to figure out which model is used and insert matching keyword to the prompt:
<img width="1246" alt="model-keyword-usage" src="https://user-images.githubusercontent.com/1288793/205525854-9a4f90a7-6547-4fab-b49b-ab31b37707d6.png">



### Keyword placement
<img width="569" alt="Screenshot 2022-12-01 at 12 26 41 PM" src="https://user-images.githubusercontent.com/1288793/204959180-8d2b509c-722e-44c3-84d6-e7dfd24f40ae.png">


### Multiple keywords 
<img width="577" alt="Screenshot 2022-12-01 at 12 27 00 PM" src="https://user-images.githubusercontent.com/1288793/204959221-66ae2e7f-5fd0-4896-9dc3-402f0db60dba.png">

1) keyword1, keyword2 - use all keywords separated by comma
2) random - choose one random keyword 
3) iterate - iterate through each keyword for each image generation
   * If sd-dynamic-prompts extension is installed, iterate will not work properly. Please disable Dynamic Prompts.
   * Alternatively, you can rename model-keyword to sd-model-keyword in the extensions folder. It will change the order of the extension and fix the bug.
4) keyword1 - use first keyword
5) keyword2 - use second keyword (if it exists)

## Adding custom mappings

Edit extensions/model-keyword/model-keyword-user.txt . model-keyword-user.txt is a csv file.
* Format is model_hash, keyword_or_keywords, optional_ckpt_filename for each line.
* keywords are separated by pipe character |.
* do NOT edit model-keyword.txt . It can be overwritten or cause conflict while upgrading.

```
# csv file for adding custom model_hash to keyword mapping
# line starting with # is ignored.

# model_hash, keyword
41fef4bd, nousr robot

# model provides multiple keywords
4d5cca44, TinyPlanet|TinyCityPlanet

# in case there is a hash collision. it will use the closest matching filename.ckpt
# model_hash, keyword, filename.ckpt
a2a802b2, SKSKS app icon, App_Icons_V1_PublicPrompts.ckpt
a2a802b2, 16-bit-landscape pixel art style, 16-bit-landscape_PublicPrompts.ckpt
```

