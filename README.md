# model-keyword
Automatic1111 WEBUI extension to autofill keyword for custom stable diffusion models.


## Installation

Copy the url of that repository into the extension tab and press "Install"

<img width="936" alt="Screenshot 2022-12-01 at 12 14 25 PM" src="https://user-images.githubusercontent.com/1288793/204957471-63712085-783b-437b-9925-ee8f935093f7.png">

From "Extensions/Installed" tab press "Apply and restart UI".
<img width="925" alt="Screenshot 2022-12-01 at 12 18 43 PM" src="https://user-images.githubusercontent.com/1288793/204958071-357d1c9b-22aa-47fc-98b4-582349b1b0cd.png">

## Usage
From txt2img, img2img tab, select "Model keyword" from Script:
<img width="604" alt="Screenshot 2022-12-01 at 12 18 04 PM" src="https://user-images.githubusercontent.com/1288793/204958140-581a40c9-be99-48ce-95f6-01fad74e7760.png">

When generating image, the extension will try to figure out which model is used and insert matching keyword to the prompt:
<img width="1143" alt="Screenshot 2022-12-01 at 12 22 33 PM" src="https://user-images.githubusercontent.com/1288793/204958740-112badfe-f140-4e3a-aed7-55376cd9f41b.png">


## Keyword placement
<img width="569" alt="Screenshot 2022-12-01 at 12 26 41 PM" src="https://user-images.githubusercontent.com/1288793/204959180-8d2b509c-722e-44c3-84d6-e7dfd24f40ae.png">


## Multiple keywords 
<img width="577" alt="Screenshot 2022-12-01 at 12 27 00 PM" src="https://user-images.githubusercontent.com/1288793/204959221-66ae2e7f-5fd0-4896-9dc3-402f0db60dba.png">

## Adding custom mappings

Edit extensions/model-keyword/model-keyword-user.txt
